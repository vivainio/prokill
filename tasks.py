"""Simple, fast and fun task runner, not unlike gulp / grunt (but fast, fun and zero dep)"""

import os
import shutil
import subprocess
import sys
import textwrap

PACKAGE = "prokill"


def do_format(args) -> None:
    c("ruff format .")


def do_4test(args) -> None:
    c("py -m pytest")


def clean() -> None:
    nuke(["dist", "sdist", "build"])


def do_publish(args) -> None:
    clean()
    c("python -m build")
    c("twine upload dist/*")


def default() -> None:
    show_help()


# library functions here (or in own module, whatever, I don't care)


def nuke(dirs: list[str]) -> None:
    for pth in dirs:
        if os.path.isdir(pth):
            shutil.rmtree(pth)



def c_spawn(cmd, cwd):
    print(">", cmd)
    subprocess.Popen(cmd, cwd=cwd, shell=True)


def copy_files(sources, destinations):
    """copy each source to each destinatios"""
    for src in sources:
        for dest in destinations:
            src = os.path.abspath(src)
            dest = os.path.abspath(dest)
            print("cp %s -> %s" % (src, dest))
            if not os.path.isdir(dest):
                print("File not found", dest)
                continue
            shutil.copy(src, dest)


def c(cmd):
    print(">", cmd)
    subprocess.check_call(cmd, shell=True)


def c_ignore(cmd):
    print(">", cmd)
    subprocess.call(cmd, shell=True)


def c_dir(cmd, dir):
    print("%s > %s" % (dir, cmd))
    subprocess.check_call(cmd, cwd=dir, shell=True)


# scaffolding starts. Do not edit below


def show_help():
    g = globals()
    print(
        "Command not found, try",
        sys.argv[0],
        " | ".join([n[3:] for n in g if n.startswith("do_")]),
        "| <command> -h",
    )


def main():
    """Launcher. Do not modify"""
    if len(sys.argv) < 2:
        default()
        return
    func = sys.argv[1]
    f = globals().get("do_" + func)
    if sys.argv[-1] == "-h":
        print(
            textwrap.dedent(f.__doc__).strip()
            if f.__doc__
            else "No documentation for this command"
        )
        return
    if not f:
        show_help()
        return
    f(sys.argv[2:])


if __name__ == "__main__":
    main()
