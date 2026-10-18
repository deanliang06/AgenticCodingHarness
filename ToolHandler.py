import subprocess
import os

class DictError(Exception):
    def __str__(self):
        return "ChatGPT returned false args for tool"
class ToolHandler:
    @staticmethod
    def run_shell(cmd:str, with_result:bool=False):
        if not cmd: raise DictError

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        output = f"Using {cmd}, the output was {result.stdout}\nStderr: {result.stderr}\nExit code: {result.returncode}"
        if with_result:
            return output, result
        return output

    @staticmethod
    def read_file(filepath:str):
        if not filepath: raise DictError

        with open(filepath, 'r') as f:
            content = f.read()
        return f"From {filepath}, we read the following: {content}"

    @staticmethod
    def write_file(filepath:str, content:str):
        if not filepath or not content: raise DictError

        with open(filepath, 'w', newline='') as f:
            f.write(content)
        verification = ToolHandler.verify_file(filepath, content)
        return f"Successfully wrote to {filepath}\n{verification}"

    @staticmethod
    def verify_file(filepath:str, expected_content:str):
        if not filepath: raise DictError

        try:
            with open(filepath, 'r', newline='') as f:
                content = f.read()
        except (OSError, UnicodeError) as e:
            return f"Verification failed for {filepath}: could not read back the file: {e}"

        if content != expected_content:
            return f"Verification failed for {filepath}: saved content does not match the requested changes"

        if os.path.splitext(filepath)[1].lower() == '.py':
            try:
                compile(content, filepath, 'exec')
            except (SyntaxError, ValueError) as e:
                return f"Changes verified in {filepath}, but Python syntax verification failed: {e}"
            return f"Changes verified in {filepath}; Python syntax passed. Runtime behavior and bugs still require tests."

        return f"Changes verified in {filepath}; code correctness was not checked. Run the relevant tests."

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
