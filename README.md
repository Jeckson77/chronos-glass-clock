# Chronos · Glass Clock

A Python clock app with a calm, modern glass interface: frosted panels, soft
background light, mint accents, live time, and tools for measuring a moment or
making space to focus. Built with Flet 1.1.2.

## Features

| Area | What it does |
| --- | --- |
| Clock | Live hours, minutes, and seconds; a matching analog dial; full date; selected timezone and UTC offset. |
| Time format | Switch between 12-hour and 24-hour displays for the main clock and world clocks. |
| Day progress | A progress bar and percentage based on the selected clock's wall-clock time. |
| World clocks | Three customizable clocks, relative UTC-offset differences, and Today / Tomorrow / Yesterday labels. |
| Stopwatch | Start, pause, resume, reset, centisecond formatting, and individual lap durations shown newest first. |
| Focus timer | 5, 25, and 50-minute presets, custom whole-minute durations from 1 to 1440, pause / resume, reset, and an in-app completion message. |
| Glass design | Actual Flet backdrop blur, translucent gradients, rounded borders, soft shadows, and radial background light. |
| Layout | Responsive cards, smaller typography in narrow windows, scrolling, and a desktop fullscreen button. |

The app starts in **Clock** mode, using **Local time**, a 12-hour display, world
clocks for **London**, **New York**, and **Tokyo**, and a 25-minute focus duration.

## Requirements and compatibility

- Python **3.10 or newer** with `pip` and virtual-environment support.
- `flet[desktop,web]==1.1.2` for the interface and desktop / web runtimes.
- `tzdata>=2025.2` for IANA timezone data, including on Windows systems without an
  operating-system IANA database.
- A graphical desktop for desktop mode, or a browser for web mode.

Development validation used **Windows and Python 3.13.16**. Setup instructions
for macOS and Linux are provided, but those platforms have not been validated
for this project. Flet may need to download its desktop client on first launch.
The interface requests Segoe UI and Consolas; font availability and fallback
can change its appearance on other systems and in browsers.

No account, database, API key, or external time service is required. Browser
mode uses a local Python server. Installing dependencies requires access to
their package downloads; the app does not fetch time from a remote service.

## Get the source

```sh
git clone https://github.com/Jeckson77/chronos-glass-clock.git
cd chronos-glass-clock
```

If you downloaded a ZIP instead, extract it and open a terminal in the folder
containing `main.py` and `requirements.txt`.

## Install and run

### Windows

From the project folder, run:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

These commands use the virtual environment directly, so PowerShell script
activation is not needed. If your Python installation uses the `py` launcher,
you can use `py -3 -m venv .venv` for the first command.

After installation, you can also double-click **`start_clock.bat`**. The launcher
changes to its own folder, uses `.venv\Scripts\python.exe` when present, and
otherwise uses `python` from your PATH. It does not install dependencies.

### macOS / Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

If the operating system reports missing native desktop libraries, follow the
Flet installation instructions for that platform or try browser mode.

### Browser mode

On Windows:

```powershell
.venv\Scripts\python.exe main.py --web
```

On macOS / Linux:

```sh
.venv/bin/python main.py --web
```

Browser mode opens the local app at port **8550** by default. Keep the Python
process running while using it. To serve the app without automatically opening
a browser, or to use another port:

```powershell
.venv\Scripts\python.exe main.py --web --headless --port 8551
```

Then open `http://localhost:8551` in your browser. Use `.venv/bin/python` in the
same command on macOS / Linux. Stop the web server with **Ctrl+C** in its terminal.

### Command-line options

| Option | Behavior |
| --- | --- |
| No options | Open a Flet desktop window. |
| `--web` | Run in browser mode and open the browser automatically. |
| `--headless` | With `--web`, run the local server without opening a browser. It does not change desktop behavior when used alone. |
| `--port NUMBER` | Choose the web-mode port; default `8550`. Ignored in desktop mode. |
| `-h`, `--help` | Print command-line help. |

The desktop window defaults to **1180 × 900**, with a minimum size of
**390 × 640**. Browser fullscreen is controlled by the browser; the app's
fullscreen button is shown only in desktop mode.

## Using the app

### Clock and timezones

1. Open the **Clock** tab.
2. Click the timezone label, initially **Local time**, to choose the main clock's
   timezone. Select a value and click **Save**.
3. Click **12h / 24h** to switch the time format. This also updates world clocks.
4. Use the sliders icon beside **Elsewhere, right now** to choose the three world
   clock locations, then click **Save**.

The digital and analog displays use the same selected timezone. World-clock
offset differences and date labels are relative to this main clock. Sun / moon
icons use a simple **06:00–17:59 daytime** rule; they do not calculate sunrise or
sunset.

Supported selections:

| Location | IANA timezone |
| --- | --- |
| Local time | Python host's configured local timezone |
| Windhoek | `Africa/Windhoek` |
| London | `Europe/London` |
| New York | `America/New_York` |
| Tokyo | `Asia/Tokyo` |
| Paris | `Europe/Paris` |
| Dubai | `Asia/Dubai` |
| Sydney | `Australia/Sydney` |
| Los Angeles | `America/Los_Angeles` |
| Singapore | `Asia/Singapore` |

Named zones apply daylight-saving rules from the installed timezone database.
**Local time** follows the computer running Python. In browser mode, this is
the Python server's timezone, which may differ from a remote browser's timezone.
Chronos displays the system clock; it does not synchronize or correct that clock.

### Stopwatch

1. Open **Stopwatch** and click **Start**.
2. Click **Lap** while running to record a lap. The side panel displays the
   duration since the previous lap, or since Start for the first lap.
3. Click **Pause**, then **Start** to resume without including the paused period.
4. Use the reset icon to stop the stopwatch and clear both elapsed time and laps.

The display uses `MM:SS.xx`, adding hours when needed. Centiseconds describe the
display format; the UI is not refreshed 100 times per second.

### Focus timer

1. Open **Focus timer**.
2. Choose a preset or click **Set duration** and enter a whole number of minutes
   from **1 to 1440**. Choosing a duration resets and stops the current countdown.
3. Click **Start focus**, use **Pause** to pause, and click the start button to
   resume. The reset icon stops the countdown and restores its configured duration.
4. At completion, the app switches to the focus view and displays an in-app
   message. **Start again** begins another countdown with the same duration.

Switching tabs does not stop a running stopwatch or countdown. Keep the app open
to receive the completion message. There is no alarm sound, system notification,
or scheduled wake-up feature.

## How it works

`main.py` builds and updates the Flet interface. `clock_engine.py` keeps timing
logic independent from the UI:

- Wall clocks use timezone-aware `datetime` values and `zoneinfo.ZoneInfo`.
- The stopwatch accumulates intervals measured with `time.perf_counter()`.
- The countdown stores a monotonic deadline and computes the remaining duration
  from that deadline. Delayed rendering does not subtract or add artificial ticks.
- An asynchronous task refreshes clock data when the second changes. It polls at
  about 0.2-second intervals normally, or 0.04 seconds while a running stopwatch
  is visible. It uses `asyncio.sleep()` to leave the event loop responsive.

See [Architecture and timing details](docs/ARCHITECTURE.md) for the model APIs,
rendering structure, lifecycle, and customization points.

## Project structure

```text
chronos-glass-clock/
├── main.py                 # Flet UI, event handlers, live updates, CLI
├── clock_engine.py         # Stopwatch, countdown, formatting, timezone helper
├── test_clock_engine.py    # Deterministic timing and timezone tests
├── requirements.txt        # Runtime dependencies
├── start_clock.bat         # Windows desktop launcher
├── README.md               # Setup, usage, behavior, limitations
├── CONTRIBUTING.md         # Development and review workflow
├── docs/
│   └── ARCHITECTURE.md      # Implementation and timing reference
├── .gitignore              # Excludes environments, caches, logs, local outputs
└── .gitattributes          # Repository text-file handling
```

Local `.venv`, `__pycache__`, and preview output are excluded from the source
repository.

## Testing and current validation status

Run the included test suite from the project folder:

```powershell
.venv\Scripts\python.exe -m unittest discover -s . -p "test_*.py" -v
```

On macOS / Linux:

```sh
.venv/bin/python -m unittest discover -s . -p 'test_*.py' -v
```

The suite uses `unittest` and injected fake clocks, so it does not need a GUI or
real-time sleeps. Its **10 tests** cover pause / resume, laps, reset, delayed
updates, countdown completion and restart, invalid durations, formatting
boundaries, daylight-saving offsets, and timezone date rollover.

Validation performed during development:

| Check | Result |
| --- | --- |
| Included engine tests | 10 passed in the project's Windows virtual environment. |
| Python compilation | Passed for the app and timing module. |
| Dependency consistency (`pip check`) | No broken requirements reported. |
| Structural UI smoke checks | Full control-tree construction and mode, format, timing, timezone, dialog, validation, completion, and narrow-resize paths passed under Flet 1.1.2. |
| Rendered screenshots / visual review | Incomplete: headless Edge screenshot capture timed out. No visual-verification claim or verified screenshot is included. |
| macOS / Linux / mobile validation | Not performed. No packaged mobile or desktop installer is included. |

The structural UI checks were ad hoc development checks; the committed automated
suite is `test_clock_engine.py`. See [Contributing](CONTRIBUTING.md) for manual
checks to run when changing the interface.

## Current limitations

- Settings, laps, and timer state are kept in memory for the current app session;
  they are not saved across restarts.
- Only the listed locations are selectable until `ZONES` is extended in source.
- The day-progress bar describes a nominal 24-hour wall-clock day, including on
  daylight-saving transition dates.
- The app does not provide alarms, audio, operating-system notifications,
  automatic focus / break cycles, or timing history export.
- It must remain open for live updates and in-app completion feedback. It does
  not guarantee delivery while the process is closed, suspended, or disconnected.
- Browser mode is a Python-served Flet app; this repository does not include a
  standalone static website, authentication, or production hosting configuration.
- Glass effects, fonts, and layout still need rendered testing on target devices.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `python` is not recognized | Install a supported Python version, enable its PATH entry, or use the Windows `py` launcher to create the environment. |
| `ModuleNotFoundError: flet` | Install `requirements.txt` with the same interpreter used to launch `main.py`. Prefer the explicit `.venv` commands above. |
| Launcher fails after finding `.venv` | Install dependencies into that `.venv`; the batch file selects it whenever its Python executable exists. |
| `ZoneInfoNotFoundError` | Install or update `tzdata` in the app environment: `python -m pip install --upgrade tzdata`. Use your environment's Python path. |
| Errors referring to old Flet APIs | Reinstall the pinned requirements. This project uses Flet 1.1.2 APIs such as `ft.run`, `ft.Alignment`, and `page.window`. |
| Desktop client download or startup fails | Check package / runtime download access, then try `main.py --web`. First desktop launch can require a Flet client download. |
| Web port is already in use | Stop the earlier local server or choose another port, for example `--web --port 8551`. |
| Local time appears incorrect | Check the Python host's system time and timezone, or choose a named clock timezone. |
| Web view looks different or glass effects are slow | Check browser graphics support, available fonts, and window size. Rendering has not yet been visually validated across platforms. |
| No sound at the end of a timer | Completion currently uses an in-app message only. |

## Customization and contributing

Change the palette constants and `glass()` helper in `main.py` to adjust the
appearance. Edit `ZONES`, `world_cities`, or the focus-preset list to change
locations and defaults. Keep timing calculations in `clock_engine.py` so they
remain independently testable.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes. Potential
future work includes persisted preferences, audio / system notifications,
accessible interaction checks, verified screenshots, and platform packaging;
these are ideas, not implemented features.

## License

No project license file has been selected or included. Third-party dependencies
retain their own licenses.
