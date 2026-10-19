"""
System control tool — controls OS-level settings like volume, brightness, etc.
Uses PowerShell on Windows.
"""

import subprocess
from tools.registry import BaseTool, register_tool


@register_tool
class SystemControlTool(BaseTool):
    name = "system_control"
    description = (
        "Control OS-level settings on the user's Windows PC. Can adjust system volume, "
        "mute/unmute, change brightness, lock screen, open settings, control Wi-Fi/Bluetooth, "
        "set display mode, empty recycle bin, and more. Use this when the user asks to "
        "change anything about their computer's settings."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": (
                    "PowerShell command or script to execute for the system control action. "
                    "Common patterns:\n"
                    "Volume: use nircmd.exe or SndVol\n"
                    "Brightness: (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, 50)\n"
                    "Lock screen: rundll32.exe user32.dll,LockWorkStation\n"
                    "Screenshot: Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen\n"
                    "Empty recycle bin: Clear-RecycleBin -Force\n"
                    "Or any valid PowerShell command."
                ),
            },
            "description": {
                "type": "string",
                "description": "What this action does (shown to user).",
            },
        },
        "required": ["action", "description"],
    }

    async def execute(self, action: str, description: str = "", **kwargs) -> str:
        try:
            result = subprocess.run(
                ["powershell", "-Command", action],
                capture_output=True, text=True, timeout=15,
            )
            output = result.stdout.strip() if result.stdout else ""
            errors = result.stderr.strip() if result.stderr else ""

            if result.returncode == 0:
                return f"Done: {description}\n{output}" if output else f"Done: {description}"
            else:
                return f"Failed: {errors}"
        except subprocess.TimeoutExpired:
            return "Command timed out."
        except Exception as e:
            return f"Error: {e}"