import os
import subprocess
import sys
from pathlib import Path

from universal_test_runner.context import Context
from universal_test_runner.matchers import ALL_MATCHERS


def run_test_command(context: Context) -> int:
    for matcher in ALL_MATCHERS:
        if not matcher.matches(context):
            continue

        command = [*matcher.command, *context.args]

        try:
            return subprocess.run(command).returncode
        except FileNotFoundError:
            print("command not found:", command[0])
            return 1
    else:
        print("no testing method found!")
        return 1


def run():
    # Get the current directory
    current_dir = os.getcwd()

    c = Context(
        # makes the file list deterministic
        sorted(Path(current_dir).iterdir()),
        # Pass any arguments to the test runner through to the test command
        sys.argv[1:],
    )

    sys.exit(run_test_command(c))


if __name__ == "__main__":
    run()
