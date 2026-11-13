# Contributing to Chronos

## Development setup

Clone the repository and follow the virtual-environment installation steps in
[README.md](README.md). Use the pinned Flet 1.1.2 dependency rather than examples
written for older Flet APIs.

Run the app with the virtual environment's Python executable:

```powershell
.venv\Scripts\python.exe main.py
```

For a local browser server without opening a browser automatically:

```powershell
.venv\Scripts\python.exe main.py --web --headless --port 8550
```

On macOS / Linux, replace `.venv\Scripts\python.exe` with `.venv/bin/python`.

## Automated checks

From the repository root:

```powershell
.venv\Scripts\python.exe -m unittest discover -s . -p "test_*.py" -v
.venv\Scripts\python.exe -m compileall -q main.py clock_engine.py
.venv\Scripts\python.exe -m pip check
```

The engine tests inject a fake monotonic clock. Extend them when changing
pause / resume, reset, laps, deadline behavior, formatting, or timezone
conversion. Avoid tests that depend on waiting for real time to pass.

## Manual interface checks

For changes to the interface, verify the rendered app in a desktop window and,
when relevant, in a browser. Structural construction checks alone cannot prove
that controls are visible, aligned, or reachable.

1. Check the clock at a wide size and near the 390-pixel minimum desktop width.
   Confirm scrolling, text, glass effects, and the analog dial remain usable.
2. Switch between 12-hour and 24-hour time. Change the main timezone and each
   world clock; check date labels and UTC-offset differences.
3. Start the stopwatch, record several laps, pause, resume, and reset. Check that
   switching tabs does not stop it and resetting clears its lap list.
4. Select each focus preset. Try custom durations of 1 and 1440 minutes, plus
   empty, fractional, out-of-range, and non-numeric input. Check error feedback.
5. Start, pause, resume, and reset a countdown. Confirm that completion switches
   to the focus view, shows one message, and offers a full-duration restart.
6. Check desktop fullscreen and confirm the app's fullscreen button is absent
   in browser mode.
7. Close the app / server and confirm no preview processes are left running.

If browser automation cannot capture the app, report that limitation. Do not
label a screenshot or platform as verified without inspecting its output.

## Code and documentation

- Keep timing logic in `clock_engine.py` independent of Flet.
- Keep UI work non-blocking; use the existing asynchronous update pattern.
- Preserve the distinction between wall-clock time and monotonic durations.
- Update README usage, defaults, timezone lists, and limitations when behavior
  changes. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the current design.
- Do not commit virtual environments, caches, logs, local browser profiles,
  credentials, or generated preview output.
- Include screenshots with interface changes only when they show actual,
  inspected rendering. Describe the platform and window size used.

## Issues and pull requests

For a bug report, include the Python and Flet versions, operating system,
desktop or browser mode, reproduction steps, expected result, and actual result.
Include the error text or an inspected screenshot when useful, with private
information removed.

For a pull request, explain the behavior being changed, the reason for it, and
the automated and manual checks performed. Note any target platforms or visual
paths that remain untested.

## Licensing

The project currently does not include a project license file. Discuss license
changes with the repository owner before including them. Third-party
dependencies keep their own licenses.
