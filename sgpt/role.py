import json
import platform
from enum import Enum
from os import getenv, pathsep
from os.path import basename
from pathlib import Path
from typing import Dict, Optional

import typer
from click import BadArgumentUsage
from distro import name as distro_name

from .config import cfg
from .utils import option_callback

SHELL_ROLE = """You are a {shell} shell command generator for {os}
Generate only valid bash commands, without explanations or additional text.
Handle incomplete prompts by providing the most logical solution.
Combine multiple steps using && when necessary.
Output plain text only, without formatting or markdown.
Ensure commands are concise, efficient, and adhere to best practices.
Consider edge cases and potential errors, and handle them appropriately.
Optimize commands for performance and resource usage when relevant.
Use clear and standard syntax, following bash conventions.
Remember, output the command described in natural language, then stop typing anything.
Any text after the first newline is going to be discarded unless you choose to place the {shell} shell text in markdown.
The task prescribed to you is only to translate from natural language to {shell} shell commands."""

DESCRIBE_SHELL_ROLE = """You are a Shell Command Descriptor.
For a given {shell} shell command in {os}
* Provide a concise, single-sentence description.
* Explain each argument and option of the command in a brief paragraph.
* Use Markdown formatting with triple or single backticks when appropriate, ensuring proper syntax with opening and closing backticks.
* Keep text inside Markdown concise and descriptions as short as possible.
* Use clear, technical language and maintain a consistent structure for each command description.
* Highlight key aspects such as required vs. optional arguments and default behaviors.
* Provide usage examples if necessary for clarity, using Markdown for code blocks.
* Ensure accuracy and completeness in your descriptions."""
# Note that output for all roles containing "APPLY MARKDOWN" will be formatted as Markdown.

SHELL_COMMAND_FIXER_ROLE = """You are a {shell} Shell Command Fixer operating within a controlled installation of {os}
Analyze single-line {shell} commands for potential errors.
If erroneous, provide a corrected command that is both valid and optimized.
Address common errors like incorrect flags, missing arguments, or syntax issues.
Consider edge cases and potential unintended consequences.
Explain corrections concisely using Markdown formatting.
Suggest alternative approaches when applicable.
Output valid commands verbatim.
Ensure that you take reasonable steps to ensure compatibility with the user's {shell} shell version and OS.
Output the fixed or original command followed by any explanations or suggestions.
Avoid placeholders unless present in the original command.
Prioritize working solutions that align with the user's intent, avoiding unnecessary simplification."""

CODE_ROLE = """You are a Code Generator.
Generate code snippets or scripts based on the provided prompt.
Output the code directly, without explanations or descriptions.
Use plain text format without markdown or code delimiters.
Assume the most logical solution for incomplete prompts.
Focus on concise, functional code adhering to best practices.
Infer the programming language from the prompt if not specified.
Prioritize code clarity and brevity.
"""

DEFAULT_ROLE = """You are ShellGPT, a {os} system administrator with expertise in the {shell} shell.
Respond concisely, aiming for around 100 words unless more detail is needed.
Utilize Markdown formatting for commands (bash code blocks) and code tools (Python Jupyter notebook cells).
Explain complex topics clearly, using examples when beneficial.
Adapt your communication style to the user's specific requirements.
Assume data storage within the conversation context.
Provide step-by-step guidance for tasks and troubleshooting.
Prioritize accurate, efficient solutions based on best practices.
Generate executable code and shell commands without requiring modifications.
Prompt for additional information when necessary.
Focus on fulfilling the user's specific needs.
"""
# Note that output for all roles containing "APPLY MARKDOWN" will be formatted as Markdown.

ROLE_TEMPLATE = "You are {name}\n{role}"


class SystemRole:
    storage: Path = Path(cfg.get("ROLE_STORAGE_PATH"))

    def __init__(
        self,
        name: str,
        role: str,
        variables: Optional[Dict[str, str]] = None,
    ) -> None:
        self.storage.mkdir(parents=True, exist_ok=True)
        self.name = name
        if variables:
            role = role.format(**variables)
        self.role = role

    @classmethod
    def create_defaults(cls) -> None:
        cls.storage.parent.mkdir(parents=True, exist_ok=True)
        variables = {"shell": cls._shell_name(), "os": cls._os_name()}
        for default_role in (
            SystemRole("ShellGPT", DEFAULT_ROLE, variables),
            SystemRole("Shell Command Generator", SHELL_ROLE, variables),
            SystemRole("Shell Command Descriptor", DESCRIBE_SHELL_ROLE, variables),
            SystemRole("Code Generator", CODE_ROLE),
            SystemRole("Shell Command Fixer", SHELL_COMMAND_FIXER_ROLE, variables),
        ):
            if not default_role._exists:
                default_role._save()

    @classmethod
    def get(cls, name: str) -> "SystemRole":
        file_path = cls.storage / f"{name}.json"
        if not file_path.exists():
            raise BadArgumentUsage(f'Role "{name}" not found.')
        return cls(**json.loads(file_path.read_text()))

    @classmethod
    @option_callback
    def create(cls, name: str) -> None:
        role = typer.prompt("Enter role description")
        role = cls(name, role)
        role._save()

    @classmethod
    @option_callback
    def list(cls, _value: str) -> None:
        if not cls.storage.exists():
            return
        # Get all files in the folder.
        files = cls.storage.glob("*")
        # Sort files by last modification time in ascending order.
        for path in sorted(files, key=lambda f: f.stat().st_mtime):
            typer.echo(path)

    @classmethod
    @option_callback
    def show(cls, name: str) -> None:
        typer.echo(cls.get(name).role)

    @classmethod
    def get_role_name(cls, initial_message: str) -> Optional[str]:
        if not initial_message:
            return None
        message_lines = initial_message.splitlines()
        if "You are" in message_lines[0]:
            return message_lines[0].split("You are ")[1].strip()
        return None

    @classmethod
    def _os_name(cls) -> str:
        current_platform = platform.system()
        if current_platform == "Linux":
            return "Linux/" + distro_name(pretty=True)
        if current_platform == "Windows":
            return "Windows " + platform.release()
        if current_platform == "Darwin":
            return "Darwin/MacOS " + platform.mac_ver()[0]
        return current_platform

    @classmethod
    def _shell_name(cls) -> str:
        current_platform = platform.system()
        if current_platform in ("Windows", "nt"):
            is_powershell = len(getenv("PSModulePath", "").split(pathsep)) >= 3
            return "powershell.exe" if is_powershell else "cmd.exe"
        return basename(getenv("SHELL", "/bin/sh"))

    @property
    def _exists(self) -> bool:
        return self._file_path.exists()

    @property
    def _file_path(self) -> Path:
        return self.storage / f"{self.name}.json"

    def _save(self) -> None:
        if self._exists:
            typer.confirm(
                f'Role "{self.name}" already exists, overwrite it?',
                abort=True,
            )

        self.role = ROLE_TEMPLATE.format(name=self.name, role=self.role)
        self._file_path.write_text(json.dumps(self.__dict__), encoding="utf-8")

    def delete(self) -> None:
        if self._exists:
            typer.confirm(
                f'Role "{self.name}" exist, delete it?',
                abort=True,
            )
        self._file_path.unlink()

    def same_role(self, initial_message: str) -> bool:
        if not initial_message:
            return False
        return True if f"You are {self.name}" in initial_message else False


class DefaultRoles(Enum):
    DEFAULT = "ShellGPT"
    SHELL = "Shell Command Generator"
    SHELL_COMMAND_FIXER="Shell Command Fixer"
    DESCRIBE_SHELL = "Shell Command Descriptor"
    CODE = "Code Generator"

    @classmethod
    def check_get(cls, shell: bool, describe_shell: bool, code: bool, shell_fix: bool) -> SystemRole:
        if shell:
            return SystemRole.get(DefaultRoles.SHELL.value)
        if describe_shell:
            return SystemRole.get(DefaultRoles.DESCRIBE_SHELL.value)
        if code:
            return SystemRole.get(DefaultRoles.CODE.value)
        if shell_fix:
            return SystemRole.get(DefaultRoles.SHELL_COMMAND_FIXER.value)
        return SystemRole.get(DefaultRoles.DEFAULT.value)

    def get_role(self) -> SystemRole:
        return SystemRole.get(self.value)


SystemRole.create_defaults()
