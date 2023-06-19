import click

help_lines = [
    "This command only exists to print information about the package.",
    "To run your actual tests, use the actual test runner: `t`. You can read more in the documentation:",
    "",
    "https://github.com/xavdid/universal-test-runner",
]


@click.group(help="\n".join(help_lines))
@click.version_option()
def cli():
    print(cli.get_help(click.get_current_context()))
