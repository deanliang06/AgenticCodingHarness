# Investigation of unfinished benchmark tasks

Investigated October 18, 2026. Production harness files were left unchanged.
The original pilot did not save model responses or session history, so its exact
failure sequence cannot be reconstructed. These findings distinguish a fresh,
traced rerun from the original score.

## Traced rerun

See [complete traces and independent test output](polyglot-investigation.json).
Same model, original task inputs, fresh task folders, unchanged harness source
hashes, and the pilot's transport and call limits were used.

| Task | Independent outcome | Tokens | Time through grading |
| --- | --- | ---: | ---: |
| beer-song | 0/8 tests passed | 15,830 | 22.310 s |
| book-store | 20/20 tests passed | 40,777 | 53.338 s |

`beer-song` requested only `list_dir`, followed by reads of the starter file and
tests. It then returned a final response claiming it had implemented `recite`
and requested a test run. Neither a write nor a test call occurred. This directly
reproduces premature completion with an untouched stub.

`book-store` read the starter file and tests, then emitted three consecutive
`thinking` responses with empty tool lists, describing implementation/testing as
already requested. It eventually issued a real write, ran `python -m unittest`
twice, and passed independent grading. Its final claim that an exit status of
zero had been confirmed was unsupported by the returned tool data: the shell
handler does not return exit status. Independent grading subsequently confirmed
the solution passed.

## Confirmed harness problems

1. **Shell results omit stderr and return code.** `ToolHandler.run_shell` returns
   only stdout. Python unittest writes test reports to stderr; command-not-found
   and other failures can also appear there. A successful run and a failed run
   can therefore both produce empty returned output. The traced book-store run
   received empty shell output, then repeated verification.
2. **Completion relies entirely on model-declared response type.**
   `Agent.on_user_msg` stops at an `output` message without checking the evidence
   behind its claims. There is also no guard against repeated `thinking` messages
   with no tools. The beer-song trace demonstrates the consequence. A generic
   agent must still allow greetings, questions, clarification and genuine blockers;
   requiring a write for every final response would be an incorrect fix.
3. **Tool exceptions stop the whole request.** A batch exception escapes
   `Message.handle_raw_output` before `Agent` copies accumulated messages into
   session history. `Agent` prints the exception and returns, denying the model
   a chance to inspect and recover from the error. This is reproducible locally,
   but was not observed as the cause of the traced failures.
4. **Diagnostic evidence was discarded by the original runner.** It captured
   stdout in memory but did not save agent responses or session history. The
   runner now saves the refiner response, structured agent responses and session
   entries, and supports separate named runs without replacing the original data.

The prompt refiner also compressed the beer-song request into a summary that
referred to lyrics in the supplied prompt without retaining those lyrics.
The agent could still obtain them from files/tests; the trace does not establish
this as the cause. It is an additional reason to preserve the original request
alongside any refined prompt.

## Verification and recommended order of repair

`benchmarks/diagnose_control_flow.py` runs offline, using fake model responses,
and reproduced missing failure output, acceptance of an unevidenced final answer,
and interruption of a tool batch by an exception. All three checks passed.

First return stdout, stderr and exit status from shell commands. Next record
per-tool exceptions as tool results and let the model recover. Then handle empty
action turns and unsupported completion claims explicitly, while preserving
normal conversational replies. Preserve the original user request when refining.
Keep the new traces and rerun the same fixed tasks after those changes, reporting
the new run separately from the baseline.

The observed problem is unreliable action execution/completion, with poor shell
observability. This pilot does not isolate model ability from prompt/protocol
effects and does not establish that a larger architecture would improve results.
