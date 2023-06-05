import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# a series of functions that, if a function returns a command, it should run that command
# if they return None, go to the next

MaybeCommand = Optional[str | list[str]]

# TODO: build a context object that has
# - cwd
# - filenames
# - a dict of {name => path object?}
# - the args the command is run with
# and pass it to each function
# i'll be able to put functions in a few file then, I think, since I have all the info I need.


def _js(files: set[str]) -> MaybeCommand:
    # TODO: check for zapier package dep
    # TODO: check for correct runner
    if "package.json" not in files:
        return

    return ["yarn", "test"]


def _python(files: set[str]) -> MaybeCommand:
    # check .pytest_cache
    # check `pytest` is available
    # check if tests.py is present
    if ".pytest_cache" in files:
        return "pytest"
    # else:
    # should I do this? or just try and run and they'll figure it out
    # print(
    # "WARNING: it looks like you want to run tests via `pytest`, but it's not available. Have you activated your virtual environment?"
    # )
    # sys.exit(1)

    if "tests.py" in files:
        return ["python", "tests.py"]


def _go(files: set[str]) -> MaybeCommand:
    # TODO: check if there's a root package and don't include the `./...`
    # TODO: also check for args, per readme. will require updating the way this is all structured
    # will need that for reading the JSON above anyway
    if "go.mod" in files:
        return ["go", "test", "./..."]


def _rust(files: set[str]) -> MaybeCommand:
    if "Cargo.toml" in files:
        return ["cargo", "test"]


def _elixir(files: set[str]) -> MaybeCommand:
    if "mix.exs" in files:
        return ["mix", "test"]


def run_tests(file_list, args):
    for test in [_python, _js, _rust, _go, _elixir]:
        if command := test(file_list):
            if isinstance(command, str):
                command = [command]

            command.extend(args)

            try:
                return subprocess.run(command)
            except FileNotFoundError:
                print("command not found:", command[0])
                sys.exit(1)

    print("No testing method found!")
    sys.exit(1)


def run():
    # Get the current directory
    current_dir = os.getcwd()

    # Get the file list
    files = set(f.name for f in Path(current_dir).iterdir())

    # Pass any arguments to the test runner through to the test command
    args = sys.argv[1:]

    run_tests(files, args)


if __name__ == "__main__":
    run()
