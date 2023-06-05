# universal-test-runner

The universal test runner is a zero-configuration, language-agnostic way to run your unit tests.

If you're working on a JS project, it runs `[your package manager here] test`. Doing rust? `cargo test` coming right up. It's got a powerful suite of heuristics to ensure it runs the right command.

## Installation

UTR is available on PyPi:

```bash
pipx install universal-test-runner
```

## Design Philosophy

1. The runner itself should need no configuration - it Just Works
2. It should pass all arguments through to the underlying test command
3. It should have wide language and test runner support; please open an issue if your use case isn't supported!

## Supported Languages

1. Python
   - uses `pytest` if available
   - looks for a `tests.py` file if not
2. JS/TS
   - runs `[package manager] test`, where `[package manager]` is:
     - `yarn` if there's a `yarn.lock`
     - `pnpm` if there's a `pnpm-lock.yaml`
     - `npm` otherwise
3. Rust
4. Go
   - if there's a `X_test.go`, then runs a plain `go test`
   - if you pass any args at all, runs `go test your-args-here`
   - otherwise, runs `go test ./...`
5. Elixir
