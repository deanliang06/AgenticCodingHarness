"""Three-task offline-selected Aider subset, using the real Agent unchanged.

Run from the repository root: python benchmarks/run_polyglot.py
Requires the upstream dataset in benchmarks/vendor/polyglot-benchmark.
"""
import contextlib
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--run-name', default='pilot')
parser.add_argument('--tasks', nargs='+')
args = parser.parse_args()
if not args.run_name.replace('-', '').replace('_', '').isalnum():
    parser.error('--run-name must contain only letters, digits, hyphens or underscores')
sys.path.insert(0, str(ROOT))
import Message
from Agent import Agent

# Bound transport failures; leave prompts, model selection and agent loop intact.
Message.client = Message.client.with_options(timeout=45, max_retries=0)

DATA = ROOT / 'benchmarks/vendor/polyglot-benchmark'
OUT = ROOT / 'benchmarks/results'
OUT.mkdir(exist_ok=True)
rows = []
active = None
depth = 0


def instrument(original):
    def call(*args, **kwargs):
        global depth
        outer = depth == 0
        if outer:
            if active['api_calls'] >= 12:
                raise RuntimeError('benchmark API call limit')
            active['api_calls'] += 1
        depth += 1
        try:
            response = original(*args, **kwargs)
            if outer:
                usage = response.usage
                active['input_tokens'] += usage.input_tokens
                active['output_tokens'] += usage.output_tokens
                active['total_tokens'] += usage.total_tokens
                active['models'].append(response.model)
                parsed = getattr(response, 'output_parsed', None)
                active['responses'].append(parsed.model_dump() if parsed else
                                           {'refined_prompt': response.output_text})
            return response
        except Exception as exc:
            if outer:
                active['errors'].append(type(exc).__name__)
            raise
        finally:
            depth -= 1
    return call


for method in ('create', 'parse'):
    setattr(Message.client.responses, method,
            instrument(getattr(Message.client.responses, method)))


def timeout(*_):
    raise TimeoutError('benchmark task exceeded 180 seconds')


signal.signal(signal.SIGALRM, timeout)
dataset_sha = subprocess.check_output(['git', '-C', str(DATA), 'rev-parse', 'HEAD'], text=True).strip()
tasks = sorted((DATA / 'python/exercises/practice').iterdir())[:3]
if args.tasks:
    available = {p.name: p for p in (DATA / 'python/exercises/practice').iterdir()}
    tasks = [available[name] for name in args.tasks]
for source in tasks:
    work = ROOT / 'benchmarks/work' / args.run_name / source.name
    if work.exists():
        raise RuntimeError(f'Refusing to overwrite previous run: {work}')
    work.mkdir(parents=True)
    for path in source.glob('*.py'):
        shutil.copy2(path, work / path.name)
    shutil.copytree(source / '.docs', work / '.docs')
    active = dict(task=source.name, api_calls=0, input_tokens=0,
                  output_tokens=0, total_tokens=0, models=[], errors=[], responses=[])
    rows.append(active)
    os.chdir(work)
    instructions = '\n\n'.join(p.read_text() for p in sorted((work / '.docs').glob('*.md')))
    files = [p.name for p in work.glob('*.py') if not p.name.endswith('_test.py')]
    prompt = (f'Complete this Python Exercism exercise: {source.name}.\n'
              f'Implement the solution in {files}. Read existing files before editing. '
              'Do not modify tests or metadata. Run the existing tests to verify your solution.\n\n'
              + instructions)
    start = time.perf_counter()
    captured = io.StringIO()
    signal.alarm(180)
    try:
        agent = Agent()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            agent.on_user_msg(prompt)
        active['final_response'] = bool(agent.session_msgs and agent.session_msgs[-1].typeMsg == 'output')
        active['session'] = [dict(type=msg.typeMsg, message=msg.msg,
                                  tools=msg.toolsCalled, evidence=getattr(msg, 'evidence', {}))
                             for msg in agent.session_msgs]
    except Exception as exc:
        active['errors'].append(type(exc).__name__)
    finally:
        signal.alarm(0)
        os.chdir(ROOT)
    active['agent_seconds'] = round(time.perf_counter() - start, 3)
    # Restore original tests before independent grading.
    for test in source.glob('*_test.py'):
        shutil.copy2(test, work / test.name)
    try:
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-p', '*_test.py', '-v'],
                                cwd=work, capture_output=True, text=True, timeout=30)
        active['passed'] = result.returncode == 0
        active['test_output'] = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        active['passed'] = False
        active['test_output'] = 'Independent tests exceeded 30 seconds.'
    active['completion_seconds'] = round(time.perf_counter() - start, 3)
    report = dict(dataset_commit=dataset_sha, selection=[p.name for p in tasks],
                  api_timeout_seconds=45, api_retries=0,
                  max_task_seconds=180, max_api_calls_per_task=12, tasks=rows,
                  source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                 for name in ['Agent.py', 'Message.py', 'AgentOutputs.py', 'ToolHandler.py']})
    (OUT / f'polyglot-{args.run_name}.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in active.items()
                      if k not in ('test_output', 'responses', 'session')}), flush=True)
