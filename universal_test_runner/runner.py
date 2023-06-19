import os
import subprocess
import sys

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
            # e.g. if `pytest` is run, but not installed
            # we capture the error so there's not a Python traceback shown
            print(f"command not found: {command[0]}")
            return 1
    else:
        print("no testing method found!")
        return 1


# not a click handler, since this is just a passthrough for the underlying test runner
def run():
    current_dir = os.getcwd()

    c = Context.build(current_dir, sys.argv[1:])

    sys.exit(run_test_command(c))


if __name__ == "__main__":
    run()
