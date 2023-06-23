# universal-test-runner

The Universal Test Runner is a zero-configuration, language-aware way to run unit tests in any project. It installs a command, `t`, which will determine how to run your test suite (and then run it).

<p align="center">
   <a href="https://github.com/xavdid/test-runner-demo/raw/main/_demo/demo-min.gif">
      <img src="https://github.com/xavdid/test-runner-demo/raw/main/_demo/demo-min.gif"/>
   </a>
</p>

If you're working on a JS project, it runs `[your package manager here] test`. You've run `pytest` in this folder before? `pytest` it is. Rust project? `cargo test` coming right up. Is also clever about running all your `go` module tests (regardless of how they're organized). No matter the command, all args are passed directly into the test runner.

Currently [supports 7 languages](#supported-languages) (and their respective test frameworks). Please open an issue if I'm missing your favorite!

## Installation

Universal Test Runner is available on [PyPi](https://pypi.org/project/universal-test-runner/) (for installation via [pipx](https://pypa.github.io/pipx/)):

```bash
pipx install universal-test-runner
```

## Usage

> You can also clone the [demo repo](https://github.com/xavdid/test-runner-demo) to play around with the test runner - it's got toy examples to show how tests are run in many languages!

Once installed, the command `t` will be available. Run it in a project folder's root and it'll do its best to run your unit tests:

```
% t
=============================== test session starts ================================
platform darwin -- Python 3.11.0, pytest-7.3.1, pluggy-1.0.0
rootdir: /Users/username/projects/test-runner
collected 78 items

tests/test_cli.py ...                                                        [  3%]
tests/test_context.py .....................                                  [ 30%]
tests/test_matchers.py ..................................................    [ 94%]
tests/test_runner.py ....                                                    [100%]

================================ 78 passed in 0.08s ================================
```

It passes all arguments and environment modifications down to the chosen test runner:

```
% t -k test_builder --verbose
=============================== test session starts ================================
platform darwin -- Python 3.11.0, pytest-7.3.1, pluggy-1.0.0
cachedir: .pytest_cache
rootdir: /Users/username/projects/test-runner
collected 78 items / 77 deselected / 1 selected

tests/test_context.py::test_builder PASSED                                   [100%]

========================= 1 passed, 77 deselected in 0.03s =========================
```

If it can't guess the testing method, it will tell you so. Feel free to open an issue to request wider language support!

### Debugging

The package also ships a command to surface info about itself: `universal-test-runner`. It has a few key pieces of functionality:

- the `universal-test-runner --version` flag, which prints info about your installed package version
- the `universal-test-runner debug` command, which prints info about which matcher would run (and why):

```
% universal-test-runner debug
[universal-test-runner]: checking each handler for first match
[universal-test-runner]:   Checking matcher 01/11: pytest
[universal-test-runner]:     looking for: ".pytest_cache"
[universal-test-runner]:     no match, continuing
[universal-test-runner]:   Checking matcher 02/11: py
[universal-test-runner]:     looking for: "tests.py"
[universal-test-runner]:     no match, continuing
[universal-test-runner]:   Checking matcher 03/11: go_multi
[universal-test-runner]:     looking for: "go.mod" and no arguments
[universal-test-runner]:     no match, continuing
[universal-test-runner]:   Checking matcher 04/11: go_single
[universal-test-runner]:     looking for: "go.mod" or a file named "..._test.go"
[universal-test-runner]:     no match, continuing

...

[universal-test-runner]: no matching test handler. To add a new one, please file an issue: https://github.com/xavdid/universal-test-runner/issues
```

## Supported Languages

1. Python
   - uses `pytest` if you've run `pytest` before. You'll need to run pytest manually on clean installs before `t` will work
   - looks for a `tests.py` file if not
2. Rust
   - `cargo test`
3. Go
   - if there's a `X_test.go`, then runs a plain `go test`
   - if you pass any args at all, runs `go test your-args-here`
   - otherwise, runs `go test ./...`
4. Elixir
   - runs `mix test`
5. Clojure
   - runs `lein test`
6. Makefile
   - looks for a line that starts with `test:`
7. Javascript/Typescript
   - if there's a `package.json` and it has a `test` script, runs `[package manager] test`, where `[package manager]` is:
     - `npm` if there's a `package-lock.json`
     - `yarn` if there's a `yarn.lock`
     - `pnpm` if there's a `pnpm-lock.yaml`

## Motivation

I work in a few languages at a time, so I've actually had a [version of this in my dotfiles](https://github.com/xavdid/dotfiles/blob/6bd5f56b1f9ad2dcef9f8b72413d30779b378aef/node/aliases.zsh#L45-L73) for a while. Also, as I've been doing [Exercism's #12in23 program](https://exercism.org/challenges/12in23), I'm _really_ switching languages. It's nice not to have to re-learn any muscle memory. Plus, increasingly complex `bash` was holding me back.

### Design Philosophy

1. The runner itself should need no configuration - it Just Works
2. It should pass all arguments through to the underlying test command
3. It should have wide language and test runner support; please open an issue if your use case isn't supported!

## Development

This section is people making changes to this package.

When in a virtual environment, run the following:

```bash
pip install -e '.[test]'
```

This installs the package in `--edit` mode and makes its dependencies available. You can now run `t` to run tests and `universal-test-runner` to access help, version, and debugging info.

### Running Tests

In your virtual environment, a simple `pytest` should run the unit test suite. You can also run `pyright` for type checking.

### Releasing New Versions

> these notes are mostly for myself (or other contributors)

0. ensure tests pass (`pytest`)
1. install release tooling (`pip install -e '.[release]'`)
2. build the package (`python -m build`)
3. upload the release (`python -m twine upload dist/*`)
   1. give your username as `__token__`
   2. give your password as your stored API key
   3. If you're getting invalid password, verify that `~/.pypirc` is empty
