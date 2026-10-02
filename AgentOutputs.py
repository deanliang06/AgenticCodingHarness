from pydantic import BaseModel, PlainSerializer, Field
from typing import *


def ser_type(value: type[Any]) -> str:
    return value.__name__

T = TypeVar('T')

JSONSerializableType = Annotated[type[T], PlainSerializer(ser_type, when_used='json-unless-none')]


class ToolCall(BaseModel):
    tool:Literal[
        "run_shell", 
        "read_file",
        "write_file",
        "list_dir",
        "change_dir",
        "file_exists",
        "make_dir",
        "delete_file",
        "web_search"]
    path: str = ""
    cmd: str = ""
    content: str = ""

    def __str__(self):
        return f"""This command calls the function {self.tool} 
        with optional arguments of path: {self.path}, with cmd: {self.cmd}
        , and with content: {self.content}"""

class AgentOutput(BaseModel):
    type: Literal["output", "thinking"]
    msg: str
    tools_called: list[ToolCall] = []