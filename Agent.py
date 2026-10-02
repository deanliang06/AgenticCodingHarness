import os
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

    def on_user_msg(self, msg):
        try:
            refined_prompt = refine_prompt_wcontext(msg, self.session_msgs, self.curMsgID)
            done = False
            while not done:
                refined_msg = Message(refined_prompt, self.curMsgID, self.cwd)
                refined_msg.run(self.session_msgs, 0)
                #unpacking in case of reg response and tool call
                for msg in refined_msg.get_session():
                    self.session_msgs.append(msg)
                self.last_output = self.session_msgs[len(self.session_msgs)-1]
                if self.last_output.msgId != self.curMsgID:
                    self.session_msgs.append(SessionMessage(msg="Error bitch", type="output", msgId=self.curMsgID))
                done = (self.last_output.typeMsg == "output")
                self.cwd = os.getcwd()
        except Exception as e:
            print(e)
        finally:
            self.curMsgID+=1

    

    


