"""Offline reproductions of failure-observability and completion behavior."""
import contextlib
import io
from pathlib import Path
import shlex
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ToolHandler import ToolHandler
from AgentOutputs import AgentOutput, ToolCall
from Agent import Agent
from Message import Message

command = shlex.join([sys.executable, '-c',
                     "import sys; sys.stderr.write('FAILED (failures=8)'); sys.exit(1)"])
result = ToolHandler.run_shell(command)
# Check only returned output: the command itself contains the failure marker.
returned_output = result.split('the output was ', 1)[1]
assert returned_output == ''
print('CONFIRMED: failing shell command returns empty output; stderr and exit code are lost')

def fake_run(self, previous, iteration):
    self.handle_raw_output(AgentOutput(type='output', msg='Done', tools_called=[]))

with patch('Agent.refine_prompt_wcontext', return_value='Implement the function'), \
     patch.object(Message, 'run', fake_run), contextlib.redirect_stdout(io.StringIO()):
    agent = Agent()
    agent.on_user_msg('Implement the function')
assert len(agent.session_msgs) == 1 and agent.last_output.typeMsg == 'output'
print('CONFIRMED: agent accepts final output without any edits or test evidence')

message = Message('task', 0, '.')
with patch.object(ToolHandler, 'read_file', return_value='first result'), \
     patch.object(ToolHandler, 'write_file', side_effect=OSError('write failed')), \
     contextlib.redirect_stdout(io.StringIO()):
    try:
        message.handle_raw_output(AgentOutput(type='thinking', msg='Read and edit', tools_called=[
            ToolCall(tool='read_file', path='a.py'),
            ToolCall(tool='write_file', path='a.py', content='new')]))
    except OSError:
        pass
assert any(msg.typeMsg == 'tool' for msg in message.toAppend)
print('CONFIRMED: tool exception interrupts batch before Agent copies accumulated results to history')
