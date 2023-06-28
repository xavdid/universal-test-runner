import os
import subprocess
import sys

from colorama import Style, just_fix_windows_console

from universal_test_runner.context import Context
from universal_test_runner.matchers import find_test_command


def run_test_command(command: list[str]) -> int:
    if not command:
        print("no testing method found!")
        return 1

    if "UTR_DISABLE_ECHO" not in os.environ:
        just_fix_windows_console()
        print(Style.DIM + "-> " + " ".join(command) + Style.RESET_ALL)
    try:
        return subprocess.run(command).returncode
    except FileNotFoundError:
        # e.g. if `pytest` is run, but not installed
        # we capture the error so there's not a Python traceback shown
        print(f"command not found: {command[0]}")
        return 1


# not a click handler, since this is just a passthrough for the underlying test runner
def run():
    context = Context.from_invocation()
    command = find_test_command(context)
    sys.exit(run_test_command(command))


if __name__ == "__main__":
    run()
