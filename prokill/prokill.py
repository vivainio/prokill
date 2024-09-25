import itertools
import re
import shlex
from argparse import ArgumentParser
from dataclasses import dataclass
import shutil
import subprocess

import wmi

# Initializing the wmi constructor
f = wmi.WMI()


@dataclass
class ProcInfo:
    id: int
    name: str
    args: str


def simplify_args(p: ProcInfo) -> str:
    if not p.args:
        return ""

    arg = p.args
    first_arg = shlex.split(arg)[0] if arg.startswith('"') else arg.split()[0]
    arg = arg.replace(first_arg, "").replace('""', "").strip()
    if len(arg) > 200:
        arg = arg[:200] + "..."
    return arg


BLACKLIST = [
    "svchost.exe",
    "Code.exe",
    "conhost.exe",
    "msedgewebview2.exe",
    "RuntimeBroker.exe",
    "msedge.exe",
]


def is_blacklist(p: ProcInfo) -> bool:
    return p.name in BLACKLIST


def get_processes():
    # Iterating through all the running processes
    for process in f.Win32_Process():
        cmdline = process.CommandLine
        p = ProcInfo(process.ProcessId, process.Name, args=cmdline if cmdline else "")
        if is_blacklist(p):
            continue
        p.args = simplify_args(p)
        yield p


def print_process_tree():
    lines = []

    def emit(s: str):
        lines.append(s)

    all = list(get_processes())
    all.sort(key=lambda p: (p.name, p.args))
    all = itertools.groupby(all, key=lambda p: (p.name))
    for k, v in all:
        aslist = list(v)
        if len(aslist) > 1:
            emit(k + ":")
            for p in aslist:
                emit(f"  {p.id:5} {p.args}")
        else:
            title = k + ":"
            emit(f"{title:20} [{aslist[0].id}] {aslist[0].args}")
    return "\n".join(lines)


def parse_pids_from_output(output: str):
    pids = []
    for line in output.split("\n"):
        if not line:
            continue

        m = re.search(r"  (\d+) ", line)
        if m:
            pids.append(m.group(1))
            continue

        m = re.search(r"\[(\d+)\]", line)
        if m:
            pids.append(m.group(1))

    return pids


def kill_selected_processes():
    tree = print_process_tree()
    fzf_bin = shutil.which("fzf")
    if not fzf_bin:
        print(
            "fzf not found, printing process tree instead. "
            "Install it with: 'winget install fzf'"
        )
        print(tree)
        return

    fzf = subprocess.run(
        [
            fzf_bin,
            "--multi",
            "--no-sort",
            "--tac",
        ],
        input=tree,
        text=True,
        capture_output=True,
    )
    if fzf.returncode != 0:
        print("No process selected. Exiting.")
        return

    print("Proceeding kill of:")
    print(fzf.stdout)
    pids = parse_pids_from_output(fzf.stdout)
    for pid in pids:
        subprocess.run(["taskkill", "/F", "/PID", pid])


def main():
    kill_selected_processes()
    # print(print_process_tree())
