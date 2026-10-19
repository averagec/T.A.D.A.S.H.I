"""
Date and time tool — answers questions about current time, dates, timezones.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from tools.registry import BaseTool, register_tool


@register_tool
class DateTimeTool(BaseTool):
    name = "get_datetime"
    description = (
        "Get the current date, time, or both. Can return time in any timezone. "
        "Use this when the user asks what time or date it is, or needs timezone conversions."
    )
    parameters = {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": (
                    "IANA timezone name, e.g. 'Asia/Singapore', 'America/New_York', 'UTC'. "
                    "Defaults to Asia/Singapore."
                ),
            }
        },
        "required": [],
    }

    async def execute(self, timezone: str = "Asia/Singapore", **kwargs) -> str:
        try:
            tz = ZoneInfo(timezone)
        except (KeyError, Exception):
            return f"Unknown timezone '{timezone}'. Use IANA names like 'America/New_York'."

        now = datetime.now(tz)
        utc_now = datetime.now(ZoneInfo("UTC"))

        return (
            f"Current time in {timezone}:\n"
            f"  Date: {now.strftime('%A, %B %d, %Y')}\n"
            f"  Time: {now.strftime('%I:%M:%S %p')}\n"
            f"  ISO: {now.isoformat()}\n"
            f"  UTC: {utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
