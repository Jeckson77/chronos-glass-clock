"""Deterministic tests for clock timing, pause/resume, completion, and zones."""

import unittest
from datetime import datetime, timezone

from clock_engine import Countdown, Stopwatch, format_duration, world_time


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class StopwatchTests(unittest.TestCase):
    def test_pause_resume_excludes_paused_time(self):
        clock = FakeClock()
        watch = Stopwatch(clock=clock)
        watch.toggle()
        clock.advance(5.25)
        watch.toggle()
        clock.advance(100)
        self.assertEqual(watch.elapsed(), 5.25)
        watch.toggle()
        clock.advance(2.5)
        self.assertEqual(watch.elapsed(), 7.75)

    def test_laps_are_cumulative_and_reset_stops(self):
        clock = FakeClock()
        watch = Stopwatch(clock=clock)
        self.assertIsNone(watch.lap())
        watch.toggle()
        clock.advance(1)
        self.assertEqual(watch.lap(), 1)
        clock.advance(2)
        self.assertEqual(watch.lap(), 3)
        self.assertEqual(watch.laps, [1, 3])
        watch.reset()
        clock.advance(50)
        self.assertFalse(watch.running)
        self.assertEqual(watch.elapsed(), 0)
        self.assertEqual(watch.laps, [])

    def test_delayed_ui_update_does_not_lose_time(self):
        clock = FakeClock()
        watch = Stopwatch(clock=clock)
        watch.toggle()
        clock.advance(123.456)
        self.assertAlmostEqual(watch.elapsed(), 123.456)


class CountdownTests(unittest.TestCase):
    def test_pause_resume_keeps_remainder(self):
        clock = FakeClock()
        timer = Countdown(60, clock=clock)
        timer.toggle()
        clock.advance(12.5)
        timer.toggle()
        clock.advance(200)
        self.assertEqual(timer.remaining(), 47.5)
        timer.toggle()
        clock.advance(7.5)
        self.assertEqual(timer.remaining(), 40)

    def test_completion_is_latched_and_restart_uses_full_duration(self):
        clock = FakeClock()
        timer = Countdown(10, clock=clock)
        timer.toggle()
        clock.advance(50)
        self.assertTrue(timer.tick())
        self.assertEqual(timer.remaining(), 0)
        self.assertFalse(timer.running)
        self.assertTrue(timer.tick())
        timer.toggle()
        self.assertFalse(timer.finished)
        self.assertTrue(timer.running)
        self.assertEqual(timer.remaining(), 10)

    def test_toggle_after_overdue_deadline_restarts(self):
        clock = FakeClock()
        timer = Countdown(10, clock=clock)
        timer.toggle()
        clock.advance(10)
        timer.toggle()
        self.assertTrue(timer.running)
        self.assertFalse(timer.finished)
        self.assertEqual(timer.remaining(), 10)

    def test_reset_duration_and_invalid_durations(self):
        clock = FakeClock()
        timer = Countdown(clock=clock)
        timer.toggle()
        clock.advance(50)
        timer.reset(300)
        self.assertEqual(timer.total_seconds, 300)
        self.assertEqual(timer.remaining(), 300)
        self.assertFalse(timer.running)
        self.assertFalse(timer.finished)
        for value in [-1, float("inf"), float("nan")]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    timer.reset(value)
        self.assertEqual(timer.remaining(), 300)

    def test_zero_duration_finishes_immediately(self):
        timer = Countdown(0)
        timer.toggle()
        self.assertTrue(timer.finished)
        self.assertFalse(timer.running)
        self.assertEqual(timer.remaining(), 0)


class FormattingTests(unittest.TestCase):
    def test_duration_boundaries_and_centiseconds(self):
        self.assertEqual(format_duration(-1), "00:00")
        self.assertEqual(format_duration(59.999, True), "00:59.99")
        self.assertEqual(format_duration(1.15, True), "00:01.15")
        self.assertEqual(format_duration(60), "01:00")
        self.assertEqual(format_duration(3600), "01:00:00")
        self.assertEqual(format_duration(3661.25, True), "01:01:01.25")
        self.assertEqual(format_duration(100 * 3600), "100:00:00")

    def test_world_time_handles_daylight_saving_and_date_boundary(self):
        winter = datetime(2026, 1, 1, 2, tzinfo=timezone.utc)
        summer = datetime(2026, 7, 1, 2, tzinfo=timezone.utc)
        ny_winter = world_time("America/New_York", winter)
        ny_summer = world_time("America/New_York", summer)
        self.assertEqual(ny_winter.isoformat(), "2025-12-31T21:00:00-05:00")
        self.assertEqual(ny_summer.isoformat(), "2026-06-30T22:00:00-04:00")


if __name__ == "__main__":
    unittest.main()
