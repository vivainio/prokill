import contextlib
import itertools
import json
import re
import shlex
import shutil
import subprocess
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass

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
    "chrome.exe",
    "firefox.exe",
    "explorer.exe",
    "ms-teams.exe",
    "OUTLOOK.EXE",
]


def is_blacklist(p: ProcInfo) -> bool:
    return p.name in BLACKLIST


def get_processes(args: Namespace):
    # Iterating through all the running processes
    for process in f.Win32_Process():
        cmdline = process.CommandLine
        p = ProcInfo(process.ProcessId, process.Name, args=cmdline if cmdline else "")
        if is_blacklist(p):
            continue
        if not args.raw:
            with contextlib.suppress(ValueError):
                p.args = simplify_args(p)
        if "prokill" in p.args:
            continue
        if args.search and not re.search(args.search, p.args, re.IGNORECASE):
            continue
        yield p


def print_process_tree(args: Namespace):
    lines = []

    def emit(s: str):
        lines.append(s)

    all = list(get_processes(args))
    all.sort(key=lambda p: (p.name.lower(), p.args))
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


def kill_selected_processes(args):
    tree = print_process_tree(args)
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
        subprocess.run(["taskkill", "/F", "/PID", pid], check=False)


def kill_searched_processes(search: str):
    all = list(get_processes(Namespace(raw=True, search=search)))
    for p in all:
        print(f"Killing {p.id} {p.name} {p.args}")
        # subprocess.run(["taskkill", "/F", "/PID", str(p.id)], check=False)


def print_json_list():
    procs = list(get_processes(Namespace(raw=True, search=None)))
    print(json.dumps([p.__dict__ for p in procs], indent=2))


def main():
    parser = ArgumentParser(description="Process killer")
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="Print process tree",
    )
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--search", help="Regex to search in process argument list")
    parser.add_argument(
        "--raw", action="store_true", help="Raw arguments, do not try to simplify"
    )
    parser.add_argument(
        "--killall",
        action="store_true",
        help="Kill all processes without selection (have to use search)",
    )
    args = parser.parse_args()
    print(args)
    if args.list:
        if args.json:
            print_json_list()
        else:
            print(print_process_tree(args))
    elif args.killall:
        if not args.search:
            print("You have to provide a search string to kill all processes")
            return
        kill_searched_processes(args.search)
    else:
        kill_selected_processes(args)
