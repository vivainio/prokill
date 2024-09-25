import itertools
import shlex
from argparse import ArgumentParser
from dataclasses import dataclass

import wmi

# Initializing the wmi constructor
f = wmi.WMI()

# Printing the header for the later columns
print("pid Process name")


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


def main():
    print(print_process_tree())


if __name__ == "__main__":
    main()
