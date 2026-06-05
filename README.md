# HPC Monitoring Dashboard

Real-time terminal dashboard for HPC node monitoring.
Built with psutil and rich - no external dependencies beyond pip.

## What it shows

- CPU usage per core with color-coded bar charts
- Memory and swap usage
- Disk usage for common HPC paths (/, /home, /scratch, /tmp)
- Top processes by CPU usage

## Usage

Single snapshot:

    python3 hpc_monitor.py --once

Live dashboard (refresh every 2 seconds):

    python3 hpc_monitor.py

Custom refresh interval:

    python3 hpc_monitor.py --interval 5

## Install dependencies

    pip install psutil rich

## Use case in HPC support

Run on a compute node to diagnose performance issues:
- High load average with low CPU usage - I/O bottleneck
- Memory at 100% - OOM risk, check running jobs
- Swap usage - memory pressure, jobs may be slow
- Zombie processes - job cleanup issue

## Environment

- Tested on macOS 26 (Apple M1) and Ubuntu 24.04 ARM64 (Lima VM)
- psutil works on Linux, macOS, Windows
