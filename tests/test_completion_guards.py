import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Agent import Agent
from AgentOutputs import AgentOutput, ToolCall
from Message import Message
from ToolHandler import ToolHandler


class CompletionGuardTests(unittest.TestCase):
    def run_agent(self, outputs, request='Implement the function'):
        responses = iter(outputs)
        def run(message, previous, iteration):
            message.handle_raw_output(next(responses))
        with patch('Agent.refine_prompt_wcontext', return_value=request), \
             patch.object(Message, 'run', run), contextlib.redirect_stdout(io.StringIO()):
            agent = Agent()
            agent.on_user_msg(request)
        return agent

    def test_repeated_empty_actions_stop_after_one_retry(self):
        empty = AgentOutput(type='thinking', msg='Waiting')
        agent = self.run_agent([empty, empty])
        self.assertIn('Stopped before verified completion', agent.last_output.msg)
        self.assertEqual(sum('Harness feedback:' in m.msg for m in agent.session_msgs), 1)

    def test_unverified_done_is_rejected_even_without_declared_claims(self):
        done = AgentOutput(type='output', msg='Done')
        agent = self.run_agent([done, done])
        self.assertIn('No verified successful file edit', agent.last_output.msg)
        self.assertFalse(any(m.typeMsg == 'output' and m.msg == 'Done' for m in agent.session_msgs))

    def test_correction_can_lead_to_real_edit_and_passing_tests(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'solution.py')
            outputs = [
                AgentOutput(type='output', msg='Implemented the function'),
                AgentOutput(type='thinking', msg='Editing', tools_called=[
                    ToolCall(tool='write_file', path=path, content='value = 1\n'),
                    ToolCall(tool='run_shell', cmd='python -m unittest')]),
                AgentOutput(type='output', outcome='completed', msg='Implemented; tests passed',
                            claims=['file_edit', 'tests_passed'])]
            result = subprocess.CompletedProcess('test', 0, '', 'Ran 1 test\nOK')
            with patch.object(ToolHandler, 'run_shell', return_value=('Exit code: 0', result)):
                agent = self.run_agent(outputs)
            self.assertEqual(agent.last_output.msg, 'Implemented; tests passed')
            self.assertEqual(Path(path).read_text(), 'value = 1\n')

    def test_answers_and_clarification_and_blockers_can_finish(self):
        for request, outcome, text in [
            ('Hello', 'answer', 'Hello!'),
            ('How do I implement this?', 'answer', 'Use a loop.'),
            ('Can you explain how to implement this?', 'answer', 'Use a loop.'),
            ('What changed previously?', 'answer', 'The function was updated.'),
            ('Write a poem', 'answer', 'A short poem.'),
            ('Implement the function', 'clarification', 'Which function?'),
            ('Implement the function', 'blocked', 'I cannot proceed; no files were modified.')]:
            with self.subTest(outcome=outcome, request=request):
                agent = self.run_agent([AgentOutput(type='output', outcome=outcome, msg=text)], request)
                self.assertEqual(agent.last_output.msg, text)

    def test_declared_and_prose_test_claims_need_actual_evidence(self):
        for done in [AgentOutput(type='output', msg='Tests passed'),
                     AgentOutput(type='output', msg='Verified', claims=['tests_passed'])]:
            agent = self.run_agent([done, done], 'Check the tests')
            self.assertIn('No successful test run', agent.last_output.msg)

    def test_new_edit_invalidates_earlier_tests(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'solution.py')
            action = AgentOutput(type='thinking', msg='Edit/test/edit', tools_called=[
                ToolCall(tool='write_file', path=path, content='value = 1\n'),
                ToolCall(tool='run_shell', cmd='python -m unittest'),
                ToolCall(tool='write_file', path=path, content='value = 2\n')])
            done = AgentOutput(type='output', msg='Tests passed', claims=['tests_passed'])
            result = subprocess.CompletedProcess('test', 0, '', 'Ran 1 test\nOK')
            with patch.object(ToolHandler, 'run_shell', return_value=('ok', result)):
                agent = self.run_agent([action, done, done])
            self.assertIn('No successful test run', agent.last_output.msg)

    def test_failed_zero_test_and_non_test_commands_do_not_prove_tests(self):
        for cmd, result in [
            ('python -m unittest', subprocess.CompletedProcess('test', 1, '', 'FAILED')),
            ('python -m unittest', subprocess.CompletedProcess('test', 0, '', 'Ran 0 tests')),
            ('echo done', subprocess.CompletedProcess('echo', 0, 'done', ''))]:
            with self.subTest(cmd=cmd, stderr=result.stderr):
                action = AgentOutput(type='thinking', msg='Check', tools_called=[ToolCall(tool='run_shell', cmd=cmd)])
                done = AgentOutput(type='output', msg='Tests passed')
                with patch.object(ToolHandler, 'run_shell', return_value=('result', result)):
                    agent = self.run_agent([action, done, done], 'Check the tests')
                self.assertIn('No successful test run', agent.last_output.msg)

    def test_previous_request_evidence_cannot_prove_current_completion(self):
        agent = Agent()
        result = type('Result', (), dict(msgId=99, evidence=dict(tool='write_file', path='x', success=True)))()
        agent.session_msgs.append(result)
        error = agent.completion_error(AgentOutput(type='output', msg='Implemented'), 'Implement the function')
        self.assertIn('No verified successful file edit', error)


if __name__ == '__main__':
    unittest.main()
