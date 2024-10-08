import click

from universal_test_runner.commands import find_test_command
from universal_test_runner.context import Context

HELP_LINES = [
    "This command only exists to print information about the package.",
    "To run your actual tests, use the actual test runner: `t`. You can read more in the documentation:",
    "",
    "https://github.com/xavdid/universal-test-runner",
]


@click.group(help="\n".join(HELP_LINES))
@click.version_option()
def cli():
    pass


@cli.command(help="Run command with extra logs so you know why it was chosen")
def debug():
    find_test_command(Context.from_invocation(debugging=True))
