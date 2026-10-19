"""
System information tool — reports on the host machine.
"""

import platform
import shutil
import psutil

from tools.registry import BaseTool, register_tool


@register_tool
class SystemInfoTool(BaseTool):
    name = "get_system_info"
    description = (
        "Get information about the local system — OS, CPU usage, memory, disk space, "
        "battery status, or running processes. Use when the user asks about their "
        "machine's status or resource usage."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "enum": ["overview", "cpu", "memory", "disk", "battery", "processes"],
                "description": "What system info to retrieve.",
            }
        },
        "required": ["query"],
    }

    async def execute(self, query: str = "overview", **kwargs) -> str:
        handlers = {
            "overview": self._overview,
            "cpu": self._cpu,
            "memory": self._memory,
            "disk": self._disk,
            "battery": self._battery,
            "processes": self._processes,
        }
        handler = handlers.get(query, self._overview)
        return handler()

    def _overview(self) -> str:
        uname = platform.uname()
        mem = psutil.virtual_memory()
        disk = shutil.disk_usage("/")
        return (
            f"System: {uname.system} {uname.release} ({uname.machine})\n"
            f"Hostname: {uname.node}\n"
            f"CPU: {psutil.cpu_count(logical=False)} cores "
            f"({psutil.cpu_count()} threads) @ {psutil.cpu_percent()}% usage\n"
            f"Memory: {mem.used // (1024**3):.1f} / {mem.total // (1024**3):.1f} GB "
            f"({mem.percent}%)\n"
            f"Disk: {disk.used // (1024**3):.1f} / {disk.total // (1024**3):.1f} GB "
            f"({disk.used / disk.total * 100:.0f}%)"
        )

    def _cpu(self) -> str:
        freq = psutil.cpu_freq()
        per_core = psutil.cpu_percent(percpu=True)
        lines = [f"CPU Usage: {psutil.cpu_percent()}% overall"]
        if freq:
            lines.append(f"Frequency: {freq.current:.0f} MHz (max {freq.max:.0f} MHz)")
        for i, p in enumerate(per_core):
            lines.append(f"  Core {i}: {p}%")
        return "\n".join(lines)

    def _memory(self) -> str:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return (
            f"RAM: {mem.used // (1024**3):.1f} / {mem.total // (1024**3):.1f} GB ({mem.percent}%)\n"
            f"Available: {mem.available // (1024**3):.1f} GB\n"
            f"Swap: {swap.used // (1024**3):.1f} / {swap.total // (1024**3):.1f} GB ({swap.percent}%)"
        )

    def _disk(self) -> str:
        partitions = psutil.disk_partitions()
        lines = []
        for p in partitions:
            try:
                usage = psutil.disk_usage(p.mountpoint)
                lines.append(
                    f"{p.mountpoint} ({p.fstype}): "
                    f"{usage.used // (1024**3):.1f} / {usage.total // (1024**3):.1f} GB "
                    f"({usage.percent}%)"
                )
            except PermissionError:
                continue
        return "\n".join(lines) or "No accessible disk partitions found."

    def _battery(self) -> str:
        batt = psutil.sensors_battery()
        if batt is None:
            return "No battery detected (desktop or VM)."
        status = "Charging" if batt.power_plugged else "Discharging"
        secs = batt.secsleft
        remaining = f"{secs // 3600}h {(secs % 3600) // 60}m" if secs > 0 else "calculating..."
        return f"Battery: {batt.percent}% — {status}\nTime remaining: {remaining}"

    def _processes(self) -> str:
        procs = sorted(
            psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]),
            key=lambda p: p.info.get("cpu_percent", 0) or 0,
            reverse=True,
        )[:10]
        lines = ["Top 10 processes by CPU:"]
        for p in procs:
            info = p.info
            lines.append(
                f"  {info['name']:<25} PID {info['pid']:<8} "
                f"CPU {info.get('cpu_percent', 0):>5.1f}%  "
                f"MEM {info.get('memory_percent', 0):>5.1f}%"
            )
        return "\n".join(lines)
