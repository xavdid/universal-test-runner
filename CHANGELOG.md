# Changelog

This project uses [SemVer](https://semver.org/) for versioning. Its public APIs, runtime support, and documented file locations won't change incompatibly outside of major versions (once version 1.0.0 has been released). There may be breaking changes in minor releases before 1.0.0 and will be noted in these release notes.

## 0.4.0

_released `TBD`_

- add django support (https://github.com/xavdid/universal-test-runner/pull/1)
- print the command being run; disable by setting `UTR_DISABLE_ECHO` in the environment (https://github.com/xavdid/universal-test-runner/pull/2)

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
