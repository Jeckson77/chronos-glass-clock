# Architecture and timing reference

## Components

The app has one Flet page, three tool modes, and a timing module without Flet
dependencies. There is no database, external time API, or saved configuration.

| File / component | Responsibility |
| --- | --- |
| `main.py: main()` | Create one `Chronos` instance for the Flet page and start its update task. |
| `main.py: Chronos` | Build controls, own per-session state, handle interactions, compute view values, and manage the update lifecycle. |
| `main.py: glass()` | Apply backdrop blur, translucent gradient, border, clipping, radius, and shadow to cards. |
| `clock_engine.py: Stopwatch` | Accumulate monotonic running intervals and record cumulative lap timestamps. |
| `clock_engine.py: Countdown` | Track remaining duration against a monotonic deadline and latch completion. |
| `clock_engine.py: format_duration()` | Format non-negative durations with optional centiseconds. |
| `clock_engine.py: world_time()` | Convert a supplied or current instant to an IANA timezone. |
| `test_clock_engine.py` | Verify timing logic with a fake clock and fixed UTC datetimes. |

## Page and rendering structure

The root is a stack of a dark background, radial gradient light blooms, and a
scrollable foreground. A centered shell contains the brand header, navigation,
main cards, world-clock cards, and status footer.

The main card contains three stacked control trees whose visibility changes
with the selected mode. The side card similarly switches between an analog
canvas, lap list, and focus presets. Switching mode changes visibility; it does
not stop the timing models.

Flet `ResponsiveRow` controls place the main and side cards next to each other
at the `lg` breakpoint and stack them at smaller widths. The three world clocks
use the `sm` breakpoint. `resize()` reduces spacing and typography on narrow
windows. The analog canvas is a fixed 224 × 224 logical-pixel drawing.

The analog clock draws tick marks, four numerals, three hands, and a central
pin. The hour hand includes minutes, the minute hand includes seconds, and the
second hand advances in whole-second steps.

## State and defaults

Each `Chronos` instance owns:

- Selected mode: `Clock`.
- Main clock zone: `Local time`.
- Time format: 12-hour.
- World-clock cities: London, New York, Tokyo.
- A stopped, zeroed `Stopwatch`.
- A stopped `Countdown` configured for 1500 seconds.
- A flag used to show each timer-completion message once.
- UI references, current dialog, connection state, and the update-task handle.

State exists in memory only. A new app session reconstructs these defaults.

## Clock values and zones

`Chronos.now()` uses `datetime.now().astimezone()` for Local time and
`datetime.now(ZoneInfo(zone))` for named cities. The UI uses this method directly;
the module-level `world_time()` helper provides the same conversion capability
independently for tests or other callers.

The selected main clock's timezone controls the digital time, analog hands,
date, UTC offset, and day-progress display. World-clock difference labels compare
each city's UTC offset with the main clock's offset. Date labels compare their
calendar dates. Changing the main zone therefore changes the reference used by
those labels.

The day fraction is:

```text
(hour * 3600 + minute * 60 + second) / 86400
```

This is a wall-clock progress indicator. It is not the elapsed fraction of a
23- or 25-hour daylight-saving transition day. World-clock sun / moon icons
classify hours 06 through 17 as daytime without astronomical calculations.

## Stopwatch model

`Stopwatch` accepts an injectable `clock` callable, defaulting to
`time.perf_counter`.

| Member | Behavior |
| --- | --- |
| `elapsed()` | Return accumulated completed intervals plus the current running interval. |
| `toggle()` | Start / resume, or pause while preserving elapsed time. |
| `reset()` | Stop and clear elapsed time and laps. |
| `lap()` | While running, append and return cumulative elapsed seconds; otherwise return `None`. |
| `running` | Whether an interval is currently active. |
| `laps` | Cumulative elapsed values recorded by `lap()`. |

Paused time is excluded. The UI converts cumulative lap timestamps into
individual durations by subtracting the preceding timestamp, then displays
newest laps first. Rendering delays do not affect the elapsed calculation.

## Countdown model

`Countdown(total_seconds=1500, clock=...)` validates that duration values are
finite and non-negative. The UI imposes its narrower user-facing input range
of 1–1440 whole minutes.

When running, remaining time is `max(0, deadline - clock())`. Pausing preserves
that remaining value. Resuming establishes a new deadline from it. Reaching
zero sets `running=False` and latches `finished=True`.

| Member | Behavior |
| --- | --- |
| `remaining()` | Return seconds remaining and update completion state. |
| `tick()` | Refresh completion and return the latched finished state. |
| `toggle()` | Pause / resume; after completion, start a full new duration. |
| `reset(seconds=None)` | Stop and restore the configured duration, optionally replacing it. |
| `total_seconds` | The configured full duration. |
| `running`, `finished` | Current run state and completion latch. |

The UI rounds remaining seconds upward for display, divides remaining time by
the full configured duration for its progress bar, and switches to Focus timer
when completion is first detected. It displays a Flet SnackBar rather than
playing audio or scheduling an operating-system notification.

## Duration formatting

`format_duration(seconds, centiseconds=False)` clamps negative input to zero,
rejects non-finite values, and returns `MM:SS` or `HH:MM:SS` when hours are
present. Centisecond mode appends `.xx`. A small floating-point tolerance avoids
displaying values such as 1.15 as 1.14 due to binary representation.

## Update lifecycle

`start()` schedules `tick()` with `page.run_task`. The coroutine polls with
`asyncio.sleep`, updates clock data when the UTC second changes, refreshes tool
values, detects timer completion, and sends explicit page updates.

The polling delay is 0.04 seconds while a running stopwatch is visible and
0.2 seconds otherwise. It does not decrement time by that delay; both timing
models read their monotonic source instead.

Disconnecting cancels the task; reconnecting starts it again if needed. The
models stay in memory for as long as that session remains available. This does
not provide durable persistence or guaranteed background completion delivery.
Behavior while the computer is suspended depends on the platform and is not
validated by the included tests.

## Customization points

| Desired change | Source location |
| --- | --- |
| Colors | `BG`, `WHITE`, `MUTED`, `MINT`, and `LINE` constants in `main.py`. |
| Glass blur, borders, gradient, radius, shadow | `glass()` in `main.py`. |
| Background light | Background stack near the end of `Chronos.build()`. |
| Available locations | `ZONES`; use valid IANA identifiers. |
| Default world clocks | `Chronos.__init__(): world_cities`. |
| Initial focus duration | `Chronos.__init__(): Countdown(25 * 60)`. |
| Preset labels and durations | Focus-preset list in `Chronos.build()`. |
| Custom-duration limits | Validation in `Chronos.custom_duration()`. |
| Window dimensions / minimums | `Chronos.build()` window configuration. |
| Narrow typography / spacing | `Chronos.resize()` and timer sizing in `update_tools()`. |
| Timing behavior | `clock_engine.py`, with deterministic regression tests. |

Keep new timing rules separate from Flet event handlers where possible. For
public-facing changes, update the README's behavior and validation notes.
