#!/usr/bin/env python3
"""
hpc_monitor.py - Real-time HPC node monitoring dashboard.

Displays CPU, memory, disk, and top processes in the terminal.
Uses psutil for system metrics and rich for terminal UI.

Usage:
    python3 hpc_monitor.py              # refresh every 2 seconds
    python3 hpc_monitor.py --interval 5 # refresh every 5 seconds
    python3 hpc_monitor.py --once       # single snapshot, no loop
"""

import argparse
import time
import psutil
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box
from rich.live import Live
from rich.layout import Layout

console = Console()

def get_cpu_info():
    """Get per-core CPU usage."""
    percent = psutil.cpu_percent(interval=0.5, percpu=True)
    freq = psutil.cpu_freq()
    load = psutil.getloadavg()
    return percent, freq, load

def get_memory_info():
    """Get memory usage."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return mem, swap

def get_disk_info():
    """Get disk usage for common HPC paths."""
    paths = ["/", "/home", "/scratch", "/tmp"]
    disks = []
    for path in paths:
        try:
            usage = psutil.disk_usage(path)
            disks.append((path, usage))
        except:
            pass
    return disks

def get_top_processes(n=8):
    """Get top N processes by CPU usage."""
    procs = []
    for p in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent", "status"]):
        try:
            procs.append(p.info)
        except:
            pass
    return sorted(procs, key=lambda x: x["cpu_percent"] or 0, reverse=True)[:n]

def make_cpu_panel(percents, freq, load):
    """Build CPU panel."""
    table = Table(box=box.SIMPLE, show_header=False, padding=(0,1))
    table.add_column("Core", style="dim", width=8)
    table.add_column("Usage", width=30)
    table.add_column("Pct", width=6)

    for i, pct in enumerate(percents):
        bar_len = int(pct / 5)
        bar = "[green]" + "█" * bar_len + "[/green]" + "░" * (20 - bar_len)
        color = "red" if pct > 90 else "yellow" if pct > 70 else "green"
        table.add_row(f"CPU {i}", bar, f"[{color}]{pct:.0f}%[/{color}]")

    freq_str = f"{freq.current:.0f} MHz" if freq else "N/A"
    load_str = f"Load: {load[0]:.2f} {load[1]:.2f} {load[2]:.2f}"

    return Panel(table, title=f"[bold]CPU[/bold] | {freq_str} | {load_str}", border_style="blue")

def make_memory_panel(mem, swap):
    """Build memory panel."""
    mem_bar_len = int(mem.percent / 5)
    mem_bar = "[green]" + "█" * mem_bar_len + "[/green]" + "░" * (20 - mem_bar_len)
    mem_color = "red" if mem.percent > 90 else "yellow" if mem.percent > 70 else "green"

    swap_bar_len = int(swap.percent / 5) if swap.total > 0 else 0
    swap_bar = "[cyan]" + "█" * swap_bar_len + "[/cyan]" + "░" * (20 - swap_bar_len)

    table = Table(box=box.SIMPLE, show_header=False, padding=(0,1))
    table.add_column("Type", width=8)
    table.add_column("Bar", width=25)
    table.add_column("Info", width=25)

    mem_info = f"[{mem_color}]{mem.percent:.1f}%[/{mem_color}] {mem.used/1e9:.1f}/{mem.total/1e9:.1f} GB"
    swap_info = f"{swap.percent:.1f}% {swap.used/1e9:.1f}/{swap.total/1e9:.1f} GB"

    table.add_row("RAM", mem_bar, mem_info)
    table.add_row("SWAP", swap_bar, swap_info)

    return Panel(table, title="[bold]Memory[/bold]", border_style="green")

def make_disk_panel(disks):
    """Build disk panel."""
    table = Table(box=box.SIMPLE, show_header=False, padding=(0,1))
    table.add_column("Path", width=12)
    table.add_column("Bar", width=25)
    table.add_column("Info", width=20)

    for path, usage in disks:
        bar_len = int(usage.percent / 5)
        color = "red" if usage.percent > 90 else "yellow" if usage.percent > 70 else "blue"
        bar = f"[{color}]" + "█" * bar_len + f"[/{color}]" + "░" * (20 - bar_len)
        info = f"[{color}]{usage.percent:.1f}%[/{color}] {usage.used/1e9:.1f}/{usage.total/1e9:.1f} GB"
        table.add_row(path, bar, info)

    return Panel(table, title="[bold]Disk[/bold]", border_style="yellow")

def make_process_panel(procs):
    """Build top processes panel."""
    table = Table(box=box.SIMPLE, padding=(0,1))
    table.add_column("PID", width=8)
    table.add_column("Name", width=20)
    table.add_column("User", width=12)
    table.add_column("CPU%", width=8)
    table.add_column("MEM%", width=8)
    table.add_column("Status", width=10)

    for p in procs:
        cpu = p["cpu_percent"] or 0
        mem = p["memory_percent"] or 0
        cpu_color = "red" if cpu > 50 else "yellow" if cpu > 20 else "green"
        table.add_row(
            str(p["pid"]),
            (p["name"] or "")[:20],
            (p["username"] or "")[:12],
            f"[{cpu_color}]{cpu:.1f}[/{cpu_color}]",
            f"{mem:.1f}",
            p["status"] or ""
        )

    return Panel(table, title="[bold]Top Processes[/bold]", border_style="magenta")

def render_dashboard():
    """Render complete dashboard."""
    percents, freq, load = get_cpu_info()
    mem, swap = get_memory_info()
    disks = get_disk_info()
    procs = get_top_processes()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hostname = psutil.os.uname().nodename if hasattr(psutil, "os") else "localhost"

    import socket
    hostname = socket.gethostname()

    header = Text(f"HPC Node Monitor | {hostname} | {now}", style="bold white", justify="center")

    return Columns([
        Panel(
            Columns([
                make_cpu_panel(percents, freq, load),
                make_memory_panel(mem, swap),
            ]),
            box=box.SIMPLE
        ),
    ]), make_disk_panel(disks), make_process_panel(procs), header

def main():
    parser = argparse.ArgumentParser(description="HPC node monitoring dashboard")
    parser.add_argument("--interval", type=int, default=2, help="Refresh interval in seconds")
    parser.add_argument("--once", action="store_true", help="Single snapshot, no loop")
    args = parser.parse_args()

    if args.once:
        cols, disk, procs, header = render_dashboard()
        console.print(header)
        console.print(cols)
        console.print(disk)
        console.print(procs)
        return

    with Live(console=console, refresh_per_second=1, screen=True) as live:
        while True:
            cols, disk, procs, header = render_dashboard()
            from rich.console import Group
            live.update(Group(header, cols, disk, procs))
            time.sleep(args.interval)

if __name__ == "__main__":
    main()
