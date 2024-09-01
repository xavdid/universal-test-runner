import os
import subprocess
import sys

from colorama import Style, just_fix_windows_console

from universal_test_runner.commands import find_test_command
from universal_test_runner.context import Context


def run_test_command(command: list[str]) -> int:
    if not command:
        print("no testing method found!")
        return 1

    if "UTR_CLEAR_PRE_RUN" in os.environ:
        # https://github.com/kovidgoyal/kitty/issues/268#issuecomment-419342337
        # https://apple.stackexchange.com/questions/31872/how-do-i-reset-the-scrollback-in-the-terminal-via-a-shell-command/318217#318217
        print("\033[2J\033[3J\033[1;1H", end="")

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
    """
    the "main" functionality of the `t` command
    """
    context = Context.from_invocation()
    command = find_test_command(context)
    sys.exit(run_test_command(command))


if __name__ == "__main__":
    run()
