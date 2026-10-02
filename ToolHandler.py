import subprocess
import os

class DictError(Exception):
    def __str__(self):
        return "ChatGPT returned false args for tool"
class ToolHandler:

    @staticmethod
    def run_shell(cmd:str):
        if not cmd: raise DictError

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return f"Using {cmd}, the output was {result.stdout}"

    @staticmethod
    def read_file(filepath:str):
        if not filepath: raise DictError

        with open(filepath, 'r') as f:
            content = f.read()
        return f"From {filepath}, we read the following: {content}"

    @staticmethod
    def write_file(filepath:str, content:str):
        if not filepath or not content: raise DictError

        with open(filepath, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"

    @staticmethod
    def list_dir(path:str):
        if not path: raise DictError
        
        return f"Files in {path}: {" ".join(os.listdir(path))}"

    @staticmethod
    def change_dir(path:str):
        if not path: raise DictError

        os.chdir(path)
        return f"Changed directory to {path}"

    @staticmethod
    def file_exists(path:str):
        if not path: raise DictError

        if os.path.exists(path):
            return f"{path} exists at path"
        else:
            return f"{path} doesn't exist in this path"

    @staticmethod
    def make_dir(path:str):
        if not path: raise DictError

        try:
            os.makedirs(path)
            return f"{path} successfully created"
        except OSError as e:
            return f"{path} already existed"

    @staticmethod
    def delete_file(path:str):
        if not path: raise DictError

        if os.path.exists(path):
            os.unlink(path)
            return f"{path} successfully deleted"
        else:
            return f"{path} doesn't exist"

    @staticmethod
    def web_search(client, query:str):
        if not query: raise DictError

        response = client.responses.create(
            model="gpt-6-luna",
            tools=[{"type": "web_search"}],
            input=query,
        )

        return f"From a search of {query}, the response of {response.output_text} was returned"
        