I wrote this with my own harness. bitch (Breaking Bad reference)
=====================================================

# Harness Gadget

Harness Gadget is a small Python coding-agent harness that brings a conversational AI agent together with a desktop chat interface and a set of tools for working in a local repository. Instead of being only a chat window, it is designed to let a user describe a coding task in ordinary language and have the agent inspect relevant files, make focused changes, and report back. The interface is built with Tkinter: it presents a scrollable conversation, a message-entry area, a Send button, and a status label, with Ctrl+Enter available to submit a message while ordinary Enter inserts a new line. The project’s purpose is to provide an approachable, locally oriented environment for experimenting with an agent-assisted development workflow.

The main pieces of the application are separated by responsibility. `input.py` creates the graphical interface and forwards submitted messages to an `Agent` instance. `Agent.py` manages the working directory and conversation history, sends user requests through the message-processing flow, and keeps processing until it receives a final response. `Message.py` constructs the model interaction, records assistant actions and tool results, and dispatches requested operations to `ToolHandler.py`. Structured response types in `AgentOutputs.py` describe the assistant’s response and the available tool-call arguments. Together, these modules form a loop in which the assistant can explain what it plans to do, request supported operations, receive their results, and use that recorded context to continue responding to the user.

The available local operations cover running shell commands, reading and writing files, listing directories, changing the current working directory, checking whether paths exist, creating directories, and deleting files; a web-search operation is also provided through the configured model client. The project uses Python packages listed in `requirements.txt`, including the OpenAI client, Pydantic, and dotenv, and `Message.py` loads environment settings before constructing the client. The harness is intentionally compact: it is useful as a foundation for exploring tool-calling agents, conversation state, and desktop interfaces, while also making clear that operations such as shell execution and file modification act on the local environment. Review tool behavior and run the application in an environment where you are comfortable granting those capabilities.

## Aider benchmark: Harness vs Codex

Three Python exercises, same `gpt-6-luna` model (October 18, 2026). Tokens include input, output, and cached input.

| Exercise | Harness tokens | Codex tokens | Harness / Codex |
| --- | ---: | ---: | --- |
| affine-cipher | 16,884* | 121,201 | Timeout / Pass |
| beer-song | 50,311 | 129,085 | Pass / Pass |
| book-store | 28,656 | 95,997 | Pass / Pass |
| **Total** | **95,851*** | **346,283** | **2/3 / 3/3 solved** |

*Harness timeout usage is missing. Codex includes 310,272 cached-input tokens. Different runtime settings and this small sample limit conclusions; token totals do not compare costs. Raw results: [harness](benchmarks/results/polyglot-completion-guards.json), [Codex](benchmarks/results/codex-comparison.json).

## Contributing

- Keep changes focused and consistent with the existing separation between the interface, agent flow, response models, and tool handlers.
- When changing or adding a tool, update its structured definition and dispatch behavior together, and describe its arguments and effects clearly.
- Verify changes with an appropriate local check, and include a concise description of what you changed and how you checked it in your contribution.
