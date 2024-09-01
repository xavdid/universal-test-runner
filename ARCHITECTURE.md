# Architecture

_this is an [architecture file](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html), which outlines the general structure of this codebase._

## Structure

The goal of the library is to, given a list of files, determine the relevant test command to run using ~~machine learning~~ a big if-else statement.

### Context

_in `context.py`_

When the root command (`t`) is run, it collects information about the directory it's been run in. It's passed to the other methods and helps with determining which files are present and their contents.

### Matchers

_in `matchers.py`_

Each available test command (such as `npm test` or `pytest`) has a corresponding `Matcher` instance. They each hold:

- a function to determine if, based on a given context, this `matcher` should be run
- the resulting test command

### Picking a command

_in `matchers.py`_

`find_test_command` is the aforementioned "big `if` statement", which is technically a `return` in a loop. For each matcher, if `matcher.matches(context)` is `True`, the object is returned to be run.
