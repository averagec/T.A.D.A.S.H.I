"""
Self-modification tools — Tadashi can read, edit, and extend its own codebase.
"""

import os
import subprocess
import sys
from pathlib import Path

from tools.registry import BaseTool, register_tool

_PROJECT_ROOT = Path(__file__).parent.parent


@register_tool
class ReadSourceTool(BaseTool):
    name = "read_source"
    description = (
        "Read one of your own source files to understand your current code. "
        "Path is relative to project root (e.g. 'core/brain.py', 'tools/weather.py'). "
        "Pass 'list' to see all files."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative file path to read, or 'list' to list all project files.",
            }
        },
        "required": ["path"],
    }

    async def execute(self, path: str, **kwargs) -> str:
        if path.strip().lower() == "list":
            lines = ["Project files:"]
            for root, dirs, files in os.walk(_PROJECT_ROOT):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", ".venv", "data")]
                rel_root = Path(root).relative_to(_PROJECT_ROOT)
                for f in sorted(files):
                    if f.startswith(".") and f != ".env.example":
                        continue
                    if f.endswith(".pyc"):
                        continue
                    lines.append(f"  {rel_root / f}")
                return "\n".join(lines)

        file_path = _PROJECT_ROOT / path
        if not file_path.exists():
            return f"File not found: {path}"
        if file_path.name == ".env":
            return "Cannot read .env — contains secrets."

        try:
            content = file_path.read_text(encoding="utf-8")
            return f"=== {path} ===\n{content}"
        except Exception as e:
            return f"Error reading {path}: {e}"


@register_tool
class WriteSourceTool(BaseTool):
    name = "write_source"
    description = (
        "Create or overwrite a source file in your own codebase. Use this to "
        "add new tools or rewrite existing files. Follow existing tool patterns."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative file path (e.g. 'tools/spotify.py')"},
            "content": {"type": "string", "description": "Full file content to write."},
            "description": {"type": "string", "description": "What this change does."},
        },
        "required": ["path", "content", "description"],
    }

    async def execute(self, path: str, content: str, description: str = "", **kwargs) -> str:
        file_path = _PROJECT_ROOT / path
        if file_path.name == ".env":
            return "Cannot overwrite .env."
        if ".." in path:
            return "Path cannot contain '..'."
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return f"Written: {path}\nReason: {description}\nRestart required for changes to take effect."
        except Exception as e:
            return f"Error writing {path}: {e}"


@register_tool
class EditSourceTool(BaseTool):
    name = "edit_source"
    description = (
        "Make a targeted edit to an existing source file — find and replace. "
        "Read the file first to get the exact text to replace."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative file path to edit."},
            "old_text": {"type": "string", "description": "Exact text to find."},
            "new_text": {"type": "string", "description": "Replacement text."},
        },
        "required": ["path", "old_text", "new_text"],
    }

    async def execute(self, path: str, old_text: str, new_text: str, **kwargs) -> str:
        file_path = _PROJECT_ROOT / path
        if not file_path.exists():
            return f"File not found: {path}"
        if file_path.name == ".env":
            return "Cannot edit .env."
        try:
            content = file_path.read_text(encoding="utf-8")
            count = content.count(old_text)
            if count == 0:
                return f"Text not found in {path}. Read the file first."
            if count > 1:
                return f"Text found {count} times — must be unique. Add more context."
            new_content = content.replace(old_text, new_text, 1)
            file_path.write_text(new_content, encoding="utf-8")
            return f"Edited {path}. Restart required."
        except Exception as e:
            return f"Error editing {path}: {e}"


@register_tool
class InstallPackageTool(BaseTool):
    name = "install_package"
    description = "Install Python packages using pip."
    parameters = {
        "type": "object",
        "properties": {
            "packages": {"type": "string", "description": "Space-separated package names."},
        },
        "required": ["packages"],
    }

    async def execute(self, packages: str, **kwargs) -> str:
        pkg_list = packages.strip().split()
        if not pkg_list:
            return "No packages specified."
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", *pkg_list],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                return f"Installed: {', '.join(pkg_list)}"
            return f"Failed:\n{result.stderr[-500:]}"
        except Exception as e:
            return f"Error: {e}"


@register_tool
class RunCommandTool(BaseTool):
    name = "run_command"
    description = (
        "Run any shell command on the user's Windows PC (PowerShell). "
        "Can do anything: manage files, open apps, download things, change settings, "
        "run scripts. For destructive actions, confirm with user first."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "PowerShell command to execute."},
            "working_dir": {"type": "string", "description": "Directory to run in. Default: user home."},
            "timeout": {"type": "integer", "description": "Max seconds. Default 30."},
        },
        "required": ["command"],
    }

    async def execute(self, command: str, working_dir: str = "", timeout: int = 30, **kwargs) -> str:
        catastrophic = ["rm -rf /", "format c:", "del /s /q c:\\"]
        if any(d in command.lower() for d in catastrophic):
            return f"Blocked dangerous command."
        cwd = working_dir if working_dir else str(Path.home())
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd)
            output = result.stdout[-3000:] if result.stdout else ""
            errors = result.stderr[-1000:] if result.stderr else ""
            response = f"Exit code: {result.returncode}"
            if output:
                response += f"\n{output}"
            if errors and result.returncode != 0:
                response += f"\nErrors:\n{errors}"
            return response
        except subprocess.TimeoutExpired:
            return f"Timed out ({timeout}s)."
        except Exception as e:
            return f"Error: {e}"


@register_tool
class AppControlTool(BaseTool):
    name = "control_app"
    description = "Open, close, or check status of applications."
    parameters = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["open", "close", "is_running", "list_running"]},
            "app_name": {"type": "string", "description": "App or process name."},
        },
        "required": ["action"],
    }

    async def execute(self, action: str, app_name: str = "", **kwargs) -> str:
        try:
            if action == "open":
                subprocess.Popen(f'start "" "{app_name}"', shell=True)
                return f"Opened {app_name}"
            elif action == "close":
                result = subprocess.run(f"taskkill /IM {app_name} /F", shell=True, capture_output=True, text=True)
                return result.stdout or result.stderr
            elif action == "is_running":
                result = subprocess.run(f'tasklist /FI "IMAGENAME eq {app_name}"', shell=True, capture_output=True, text=True)
                return f"{app_name} is running." if app_name.lower() in result.stdout.lower() else f"{app_name} is not running."
            elif action == "list_running":
                result = subprocess.run("tasklist /FO CSV /NH", shell=True, capture_output=True, text=True)
                return result.stdout[-3000:]
            return f"Unknown action: {action}"
        except Exception as e:
            return f"Error: {e}"


@register_tool
class FileManagerTool(BaseTool):
    name = "manage_files"
    description = "Read, write, search, copy, move, delete files anywhere on the PC."
    parameters = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["read", "write", "list", "search", "copy", "move", "delete", "info"]},
            "path": {"type": "string", "description": "Absolute file/directory path."},
            "content": {"type": "string", "description": "For 'write' action."},
            "destination": {"type": "string", "description": "For 'copy'/'move' actions."},
            "pattern": {"type": "string", "description": "For 'search' action (e.g. '*.py')."},
        },
        "required": ["action", "path"],
    }

    async def execute(self, action: str, path: str, content: str = "", destination: str = "", pattern: str = "*", **kwargs) -> str:
        p = Path(path)
        try:
            if action == "read":
                if not p.exists(): return f"Not found: {path}"
                text = p.read_text(encoding="utf-8", errors="replace")
                return text[:5000] + ("\n...[truncated]" if len(text) > 5000 else "")
            elif action == "write":
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
                return f"Written to {path}"
            elif action == "list":
                if not p.exists(): return f"Not found: {path}"
                items = sorted(p.iterdir())[:100]
                return "\n".join(f"{'[DIR] ' if i.is_dir() else '      '}{i.name}" for i in items)
            elif action == "search":
                matches = list(p.rglob(pattern))[:50]
                return "\n".join(str(m) for m in matches) if matches else f"No matches for '{pattern}'"
            elif action == "copy":
                import shutil
                if p.is_dir(): shutil.copytree(str(p), destination)
                else: shutil.copy2(str(p), destination)
                return f"Copied to {destination}"
            elif action == "move":
                import shutil
                shutil.move(str(p), destination)
                return f"Moved to {destination}"
            elif action == "delete":
                if p.is_dir():
                    import shutil
                    shutil.rmtree(str(p))
                else: p.unlink()
                return f"Deleted {path}"
            elif action == "info":
                stat = p.stat()
                from datetime import datetime
                return f"Size: {stat.st_size:,} bytes\nModified: {datetime.fromtimestamp(stat.st_mtime)}"
            return f"Unknown action: {action}"
        except Exception as e:
            return f"Error: {e}"


@register_tool
class DownloadFileTool(BaseTool):
    name = "download_file"
    description = "Download a file from the internet."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to download."},
            "save_path": {"type": "string", "description": "Absolute path to save to."},
        },
        "required": ["url", "save_path"],
    }

    async def execute(self, url: str, save_path: str, **kwargs) -> str:
        import httpx
        dest = Path(save_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                dest.write_bytes(response.content)
                size = len(response.content)
                return f"Downloaded to {save_path} ({size / 1024:.1f} KB)"
        except Exception as e:
            return f"Download error: {e}"