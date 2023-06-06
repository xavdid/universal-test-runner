import os
import subprocess
import sys
from pathlib import Path

from universal_test_runner.context import Context
from universal_test_runner.matchers import ALL_MATCHERS

# TODO: build a context object that has
# - cwd
# - filenames
# - a dict of {name => path object?}
# - the args the command is run with
# and pass it to each function
# i'll be able to put functions in a few file then, I think, since I have all the info I need.


def run_tests(context: Context):
    for matcher in ALL_MATCHERS:
        if matcher.test(context):
            command = [*matcher.command, *context.args]

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

    c = Context(
        list(Path(current_dir).iterdir()),
        # Pass any arguments to the test runner through to the test command
        sys.argv[1:],
    )

    run_tests(c)


if __name__ == "__main__":
    run()
