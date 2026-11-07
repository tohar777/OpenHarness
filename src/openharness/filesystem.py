
from pathlib import Path

class FileSystem:

    def __init__(self, workspace: str = "./workspace"):
        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def get_path(self, filename: str) -> Path:
        path = (self.workspace / filename).resolve()

        # Prevent accessing files outside the workspace
        if not path.is_relative_to(self.workspace):
            raise PermissionError("Access denied: outside workspace")

        return path

    def read_file(self, filename: str) -> str:
        path = self.get_path(filename)
        return path.read_text(encoding="utf-8")

    def write_file(self, filename: str, content: str):
        path = self.get_path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

        print(f"[FileSystem] Created: {path}")

    def list_files(self):
        return [
            str(path.relative_to(self.workspace))
            for path in self.workspace.rglob("*")
            if path.is_file()
        ]

    def delete_file(self, filename: str):
        path = self.get_path(filename)

        if path.is_file():
            path.unlink()
