# Changelog

This project uses [SemVer](https://semver.org/) for versioning. Its public APIs, runtime support, and documented file locations won't change incompatibly outside of major versions (once version 1.0.0 has been released). Note that it's not meant to be run as a Python library, so there are no guarantees about the name or structure of its internals; use as your own risk.

There may be breaking changes in minor releases before 1.0.0 and will be noted in these release notes.

## 0.6.1

_released `2024-08-14`_

- add support for the `UTR_CLEAR_PRE_RUN` environment variable, which clears the terminal (and scrollback) before running the test

## 0.6.0

_released `2023-12-06`_

- add support for [bun](https://bun.sh/), which runs `bun test` when it sees a `bun.lockb`
- add support for my [Advent of Code runner](https://github.com/xavdid/advent-of-code)

## 0.5.1

_released `2023-08-11`_

- include `--` after the `exercism test` command, so args are correctly passed through to the underlying test command (e.g. `t --include pending` runs `exercism test -- --include-pending`) ([#6](https://github.com/xavdid/universal-test-runner/pull/6))

## 0.5.0

_released `2023-08-03`_

- add support for [Exercism](https://exercism.org/)'s new `exercism test` CLI command. Read more [in the docs](https://github.com/xavdid/universal-test-runner#exercism) ([#5](https://github.com/xavdid/universal-test-runner/pull/5)).

## 0.4.0

_released `2023-07-01`_

- :exclamation: BREAKING: prioritize `Makefile` (and `justfile`) over running any tools directly. ([#3](https://github.com/xavdid/universal-test-runner/pull/3))
  - This is likely a non-issue unless you have a `Makefile` _and_ an already-supported language and preferred circumventing `make`
  - in that case, use a recipe name besides `test`
- add django support (https://github.com/xavdid/universal-test-runner/pull/1) and ensure it takes precedence over more generic python testing methods ([223d709](https://github.com/xavdid/universal-test-runner/commit/223d709e17882d56c6efcaa42e07c4bb300f1742))
- add [justfile](https://github.com/casey/just) support. Make sure your `test` recipe [accepts arguments](https://github.com/xavdid/universal-test-runner#just-errors-when-passing-cli-args) ([#3](https://github.com/xavdid/universal-test-runner/pull/3), [#4](https://github.com/xavdid/universal-test-runner/pull/4))
- print the command being run; disable by setting `UTR_DISABLE_ECHO` in the environment (https://github.com/xavdid/universal-test-runner/pull/2)
- specify `utf-8` encoding when opening files for wider windows compatibility ([2475e94](https://github.com/xavdid/universal-test-runner/commit/2475e94))

## 0.3.0

_released `2023-06-19`_

- add a `universal-test-runner` command which has info about the package. The main test runner still lives in `t`.
- add the `universal-test-runner debug` command to print an explanation of why a certain test runner is chosen
- remove custom file caching logic

## 0.2.0

_released `2023-06-18`_

- add support for the `test` directive in `Makefile`s
- add support for the `test` script in a `package.json` file

## 0.1.0

_released `2023-06-06`_

- initial public release, with support for the following languages:
  - python
  - rust
  - go
  - elixir
  - clojure
