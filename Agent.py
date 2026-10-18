import os
import re
from openai import OpenAI
from typing import *

from Message import *
tools = [
    "run_shell",
    "read_file",
    "write_file",
    "list_directory",
    "change_directory",
    "file_exists",
    "make_directory",
    "delete_file",
    "web_search",
]

class SessionMessage:
    typeMsg : Literal["input", "output", "tool", "thinking"]
    def __init__(self, msg, type, msgId, toolsCalled=[]):
        try:
            self.msg = msg
            self.typeMsg = type
            self.msgId = msgId
            self.toolsCalled = toolsCalled
        except ValueError as e:
            print("Literal is violated", e)
        except Exception as e:
            print("Idk boss", e)
    def __str__(self):
        if self.typeMsg == "input":
            output = "The following text is from the user:\n"
        elif self.typeMsg == "output":
            output = "The following text is a final message sent to a user in response to their query:\n"
        elif self.typeMsg == "tool":
            output = "The following result was gotten from a tool call:\n"
        else:
            output = "The following text was an intermediate thinking step in order answer the user:\n"
            output+=self.msg+"\n"
            if (len(self.toolsCalled) > 0):
                output+="and we called tools" + ",".join(self.toolsCalled)
            output+="\n\n"
            return output
        return output+self.msg+"\n\n" 

class Agent:
    def __init__(self):
        self.cwd = os.getcwd()
        self.curMsgID = 0
        self.session_msgs : List[SessionMessage] = []
        self.last_output = ""

    def completion_error(self, output, request):
        claims = set(output.claims)
        question = bool(re.match(r'\s*(how|why|what|explain|describe|(?:can|could|would) you (?:explain|describe|tell))\b', request, re.I))
        # Also catch the unsupported prose claims seen in the benchmark traces.
        positive_claims = ' '.join(sentence for sentence in re.split(r'[.!?\n]', output.msg)
            if not re.search(r"\b(no|not|never|unable|failed|cannot)\b|n't", sentence, re.I))
        if not question and re.search(r'\b(implemented|updated|fixed|modified|wrote|created|edited)\b', positive_claims, re.I):
            claims.add('file_edit')
        if not question and re.search(r'\btests?\b.{0,40}\b(passed|passing|succeeded)\b|\b(all|existing) tests? pass\b', positive_claims, re.I):
            claims.add('tests_passed')
        editing_request = bool(re.search(r'\b(implement|refactor|debug)\b', request, re.I)
            or (re.search(r'\b(fix|edit|modify|update|add|create|write)\b', request, re.I)
                and re.search(r'\b(code|codebase|repo|harness|files?|functions?|classes?|bugs?|modules?|scripts?|tests?|features?)\b|\.py\b', request, re.I)))
        if editing_request and not question and output.outcome not in ('blocked', 'clarification'):
            claims.add('file_edit')

        edits = {}
        tests_passed = False
        for msg in self.session_msgs:
            if msg.msgId != self.curMsgID: continue
            evidence = getattr(msg, 'evidence', {})
            if evidence.get('tool') == 'write_file':
                edits[evidence['path']] = evidence['success']
                tests_passed = False
            elif evidence.get('test'):
                tests_passed = evidence['success']
        if 'file_edit' in claims and (not edits or not all(edits.values())):
            return 'No verified successful file edit supports completion. Apply the requested changes using tools, or report a genuine blocker/essential clarification without claiming edits.'
        if 'tests_passed' in claims and not tests_passed:
            return 'No successful test run after the latest edit supports this claim. Run the relevant tests and inspect the result, or honestly report that verification is incomplete.'
        return ''

    def on_user_msg(self, msg):
        try:
            refined_prompt = refine_prompt_wcontext(msg, self.session_msgs, self.curMsgID)
            done = False
            retries = {'empty': 0, 'completion': 0}
            turns = 0
            while not done:
                turns += 1
                if turns > 40:
                    self.last_output = SessionMessage('Stopped before completion: the request exceeded 40 agent turns.', 'output', self.curMsgID)
                    self.session_msgs.append(self.last_output)
                    break
                refined_msg = Message(refined_prompt, self.curMsgID, self.cwd)
                refined_msg.run(self.session_msgs, 0)
                #unpacking in case of reg response and tool call
                for entry in refined_msg.get_session():
                    self.session_msgs.append(entry)
                self.last_output = self.session_msgs[len(self.session_msgs)-1]
                if self.last_output.msgId != self.curMsgID:
                    self.session_msgs.append(SessionMessage(msg="Error bitch", type="output", msgId=self.curMsgID))
                self.cwd = os.getcwd()
                output = refined_msg.output
                error = ''
                kind = 'completion'
                if output.type == 'thinking' and not output.tools_called:
                    kind = 'empty'
                    error = 'No tools were requested or executed. Nothing runs in the background. Choose an action or provide a supported final response.'
                elif output.type == 'output' and output.tools_called:
                    error = 'Tools just executed. Inspect their recorded results before returning a final response with tools_called=[].'
                elif output.type == 'output':
                    error = self.completion_error(output, msg)
                if error:
                    # Rejected final answers must not become historical completed outputs.
                    for entry in refined_msg.toAppend:
                        if entry.typeMsg == 'output': entry.typeMsg = 'thinking'
                    if retries[kind] >= 1:
                        self.last_output = SessionMessage('Stopped before verified completion: ' + error, 'output', self.curMsgID)
                        self.session_msgs.append(self.last_output)
                        break
                    retries[kind] += 1
                    self.session_msgs.append(SessionMessage('Harness feedback: ' + error, 'thinking', self.curMsgID))
                    continue
                done = output.type == 'output'
        except Exception as e:
            print(e)
        finally:
            self.curMsgID+=1

    

    


