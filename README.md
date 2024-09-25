# Prokill - kill processes like a pro

Kills Windows processes.

## Installation:

```
winget install fzf
pip install -U prokill
```

## Usage:

- Run prokill in admin command prompt
- Use the [fzf](https://github.com/junegunn/fzf) UI to select processes to kill
  - Use tab to mark processes (multiselection)
  - Enter text for incremental, fuzzy search
  - Press enter to start killing
  - Press ESC to leave without killing


## Use case:

- You need to kill processes
- You want to see command line of processes you are killing
    - E.g. you want to see "python myscript.py" instead of "python.exe"
- You want to use fuzzy find to search for the process quickly
- You want to see processes grouped under binary name, e.g. all Python
  processes grouped under python.exe
