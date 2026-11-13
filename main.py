"""Chronos — a quiet, glass-inspired clock, built with Python and Flet."""

from __future__ import annotations

import argparse
import asyncio
import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import flet as ft
import flet.canvas as cv

try:
    from .clock_engine import Countdown, Stopwatch, format_duration
except ImportError:
    from clock_engine import Countdown, Stopwatch, format_duration


BG = "#0B1019"
WHITE = "#EFF5F6"
MUTED = "#93A2B5"
MINT = "#BDFADE"
LINE = "#18FFFFFF"
ZONES = {
    "Local time": None,
    "Windhoek": "Africa/Windhoek",
    "London": "Europe/London",
    "New York": "America/New_York",
    "Tokyo": "Asia/Tokyo",
    "Paris": "Europe/Paris",
    "Dubai": "Asia/Dubai",
    "Sydney": "Australia/Sydney",
    "Los Angeles": "America/Los_Angeles",
    "Singapore": "Asia/Singapore",
}


def label(value: str, size: float = 14, color: str = WHITE, **kwargs) -> ft.Text:
    return ft.Text(value, size=size, color=color, **kwargs)


def eyebrow(value: str) -> ft.Text:
    return label(value, 10, MUTED, weight=ft.FontWeight.W_600,
                 style=ft.TextStyle(letter_spacing=2))


def glass(content: ft.Control, **kwargs) -> ft.Container:
    """Actual backdrop blur, with a translucent tint and a soft edge highlight."""
    return ft.Container(
        content=content,
        padding=26,
        border_radius=26,
        blur=ft.Blur(sigma_x=22, sigma_y=22),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=["#192E3D45", "#101C2838"],
        ),
        border=ft.Border.all(1, LINE),
        shadow=ft.BoxShadow(blur_radius=32, color="#16000000", offset=ft.Offset(0, 12)),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        **kwargs,
    )


def pill(text: str, icon=None, color=MUTED) -> ft.Container:
    controls = [label(text, 11, color)]
    if icon:
        controls.insert(0, ft.Icon(icon, size=13, color=color))
    return ft.Container(
        ft.Row(controls, spacing=6, tight=True),
        padding=ft.Padding.symmetric(horizontal=11, vertical=7),
        bgcolor="#0CFFFFFF", border=ft.Border.all(1, "#0FFFFFFF"), border_radius=30,
    )


class Chronos:
    def __init__(self, page: ft.Page):
        self.page = page
        self.mode = "Clock"
        self.use_24h = False
        self.zone = "Local time"
        self.world_cities = ["London", "New York", "Tokyo"]
        self.watch = Stopwatch()
        self.timer = Countdown(25 * 60)
        self.completion_shown = False
        self.narrow = (page.width or 1180) < 720
        self._last_second = None
        self._connected = True
        self._task = None
        self._dialog = None
        self.build()

    def now(self, city: str | None = None) -> datetime:
        zone = ZONES[self.zone if city is None else city]
        return datetime.now(ZoneInfo(zone)) if zone else datetime.now().astimezone()

    def icon_button(self, icon, tooltip, handler) -> ft.IconButton:
        return ft.IconButton(icon, icon_color=MUTED, icon_size=20,
                             tooltip=tooltip, on_click=handler)

    def action(self, text, icon, handler, primary=False) -> ft.Container:
        return ft.Container(
            ft.Row([ft.Icon(icon, size=19, color=BG if primary else WHITE),
                    label(text, 13, BG if primary else WHITE, weight=ft.FontWeight.W_600)],
                   alignment=ft.MainAxisAlignment.CENTER, spacing=7, tight=True),
            bgcolor=MINT if primary else "#0DFFFFFF",
            border=ft.Border.all(1, "#22FFFFFF"),
            padding=ft.Padding.symmetric(horizontal=22, vertical=13),
            border_radius=14, on_click=handler, ink=True,
        )

    def build(self):
        page = self.page
        page.title = "Chronos · Glass Clock"
        page.bgcolor = BG
        page.padding = 0
        page.spacing = 0
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = ft.Theme(font_family="Segoe UI", color_scheme_seed=MINT,
                              scaffold_bgcolor=BG)
        page.window.width = 1180
        page.window.height = 900
        page.window.min_width = 390
        page.window.min_height = 640

        mark = ft.Container(
            ft.Icon(ft.Icons.SCHEDULE_ROUNDED, size=26, color=MINT),
            width=46, height=46, alignment=ft.Alignment.CENTER,
            border_radius=15, bgcolor="#1438CFA0", border=ft.Border.all(1, "#305EF0BD"),
        )
        header = ft.Row([
            ft.Row([mark, label("chronos", 25, weight=ft.FontWeight.W_600,
                               style=ft.TextStyle(letter_spacing=-1))], spacing=12),
            ft.Row([
                pill("YOUR TIME. YOUR PACE.", color=MUTED),
                self.icon_button(ft.Icons.FULLSCREEN_ROUNDED, "Toggle fullscreen", self.fullscreen),
            ], spacing=12),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        self.header_tag = header.controls[1].controls[0]
        header.controls[1].controls[1].visible = not page.web

        self.greeting = label("Make time yours.", 34, weight=ft.FontWeight.W_500,
                              style=ft.TextStyle(letter_spacing=-1.2))
        intro = ft.Column([
            self.greeting,
            label("A little clarity. A little calm. One moment at a time.", 13, MUTED),
        ], spacing=6)

        self.nav_items = {}
        nav = []
        for name, icon in [("Clock", ft.Icons.SCHEDULE_ROUNDED),
                           ("Stopwatch", ft.Icons.TIMER_OUTLINED),
                           ("Focus timer", ft.Icons.HOURGLASS_BOTTOM_ROUNDED)]:
            item = ft.Container(
                ft.Row([ft.Icon(icon, size=17), label(name, 12)], spacing=7, tight=True),
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                border_radius=12, on_click=lambda e, n=name: self.switch_mode(n),
                animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT), ink=True,
            )
            self.nav_items[name] = item
            nav.append(item)
        self.format_button = ft.Container(
            label("12h  /  24h", 12, MINT), on_click=self.toggle_format,
            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            tooltip="Switch between 12-hour and 24-hour time", border_radius=12, ink=True,
        )
        self.navigation = ft.Row([
            ft.Container(ft.Row(nav, spacing=4), padding=5, border_radius=17,
                         bgcolor="#08121E2C", border=ft.Border.all(1, LINE)),
            self.format_button,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True, run_spacing=8)

        self.time_digits = label("00:00", 98, weight=ft.FontWeight.W_300,
                                 font_family="Consolas",
                                 style=ft.TextStyle(letter_spacing=-7))
        self.seconds = label("00", 31, MINT, font_family="Consolas")
        self.meridiem = label("AM", 12, MUTED, weight=ft.FontWeight.W_500)
        self.date_text = label("", 14, MUTED)
        self.zone_title = label(self.zone.upper(), 10, MUTED,
                                style=ft.TextStyle(letter_spacing=2))
        self.zone_control = ft.Container(
            ft.Row([ft.Icon(ft.Icons.MY_LOCATION_ROUNDED, size=14, color=MINT),
                    self.zone_title, ft.Icon(ft.Icons.EXPAND_MORE_ROUNDED, size=16, color=MUTED)],
                   spacing=8, tight=True), on_click=self.choose_main_zone,
            padding=ft.Padding.symmetric(vertical=3), tooltip="Choose clock timezone",
        )
        self.utc_text = label("UTC", 11, MUTED)
        self.day_label = label("TODAY'S JOURNEY", 10, MUTED,
                               style=ft.TextStyle(letter_spacing=1.5))
        self.day_percent = label("0% complete", 11, MUTED)
        self.day_progress = ft.ProgressBar(value=0, color=MINT, bgcolor="#10FFFFFF",
                                           height=4, border_radius=3)
        self.clock_content = ft.Column([
            ft.Row([self.zone_control, self.utc_text],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=6),
            ft.Row([self.time_digits,
                    ft.Column([self.seconds, self.meridiem], spacing=0)],
                   spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED, size=15, color=MUTED),
                    self.date_text], spacing=9),
            ft.Container(expand=True),
            ft.Container(height=1, bgcolor=LINE),
            ft.Container(height=5),
            ft.Row([self.day_label, self.day_percent],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.day_progress,
        ], spacing=12, expand=True)

        self.stopwatch_digits = label("00:00.00", 72, font_family="Consolas",
                                      style=ft.TextStyle(letter_spacing=-4))
        self.stopwatch_status = label("Ready when you are.", 13, MUTED)
        self.stopwatch_start = self.action("Start", ft.Icons.PLAY_ARROW_ROUNDED,
                                          self.toggle_stopwatch, True)
        self.lap_button = self.action("Lap", ft.Icons.FLAG_OUTLINED, self.record_lap)
        self.stopwatch_content = ft.Column([
            eyebrow("EVERY SECOND COUNTS"),
            ft.Container(height=4),
            self.stopwatch_digits,
            self.stopwatch_status,
            ft.Container(expand=True),
            ft.Row([self.stopwatch_start, self.lap_button,
                    self.icon_button(ft.Icons.RESTART_ALT_ROUNDED, "Reset stopwatch", self.reset_stopwatch)],
                   spacing=10, wrap=True),
        ], spacing=12, expand=True, visible=False)

        self.timer_digits = label("25:00", 86, font_family="Consolas",
                                  style=ft.TextStyle(letter_spacing=-5))
        self.timer_status = label("One thing at a time. You've got this.", 13, MUTED)
        self.timer_progress = ft.ProgressBar(value=1, color=MINT, bgcolor="#10FFFFFF",
                                             height=4, border_radius=3)
        self.timer_start = self.action("Start focus", ft.Icons.PLAY_ARROW_ROUNDED,
                                      self.toggle_timer, True)
        self.timer_content = ft.Column([
            ft.Row([eyebrow("ROOM TO FOCUS"),
                    ft.Container(label("Set duration", 11, MINT), on_click=self.custom_duration,
                                 tooltip="Enter minutes", padding=4)],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.timer_digits,
            self.timer_status,
            self.timer_progress,
            ft.Container(expand=True),
            ft.Row([self.timer_start,
                    self.icon_button(ft.Icons.RESTART_ALT_ROUNDED, "Reset timer", self.reset_timer)], spacing=10),
        ], spacing=12, expand=True, visible=False)

        self.hero = glass(ft.Stack([self.clock_content, self.stopwatch_content, self.timer_content]),
                          height=346, col={"xs": 12, "lg": 8})
        self.dial = cv.Canvas(width=224, height=224)
        self.analog_caption = label("A moment of calm.", 12, MUTED)
        self.lap_list = ft.Column(spacing=9, scroll=ft.ScrollMode.AUTO, height=224, visible=False)
        self.preset_column = ft.Column(spacing=12, visible=False, height=224,
                                      alignment=ft.MainAxisAlignment.CENTER)
        for minutes, title, subtitle in [
            (5, "Take a breath", "5 min · a little reset"),
            (25, "Find your flow", "25 min · focused work"),
            (50, "Go a little deeper", "50 min · uninterrupted"),
        ]:
            self.preset_column.controls.append(ft.Container(
                ft.Row([
                    ft.Container(ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=17, color=MINT),
                                 width=34, height=34, bgcolor="#0FFFFFFF", border_radius=11,
                                 alignment=ft.Alignment.CENTER),
                    ft.Column([label(title, 13), label(subtitle, 10, MUTED)], spacing=3),
                ], spacing=12), padding=10, border_radius=14,
                bgcolor="#06FFFFFF", on_click=lambda e, m=minutes: self.set_timer(m), ink=True))
        self.side_heading = eyebrow("A DIFFERENT PERSPECTIVE")
        self.side = glass(ft.Column([
            self.side_heading,
            ft.Container(ft.Stack([self.dial, self.lap_list, self.preset_column]),
                         alignment=ft.Alignment.CENTER, expand=True),
            self.analog_caption,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            height=346, col={"xs": 12, "lg": 4})
        self.main_row = ft.ResponsiveRow([self.hero, self.side], spacing=18, run_spacing=18)

        self.world_row = ft.ResponsiveRow(spacing=16, run_spacing=16)
        self.world_refs = []
        self.build_world_cards()
        world_header = ft.Row([
            ft.Row([label("Elsewhere, right now", 17, weight=ft.FontWeight.W_500),
                    pill("WORLD CLOCK", ft.Icons.PUBLIC_ROUNDED)], spacing=12, wrap=True),
            self.icon_button(ft.Icons.TUNE_ROUNDED, "Customize world clocks", self.choose_world_zones),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.footer_time = label("", 10, MUTED)
        footer = ft.Row([
            ft.Row([ft.Container(width=5, height=5, bgcolor=MINT, border_radius=5),
                    label("In sync with your device", 10, MUTED)], spacing=7),
            self.footer_time,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)

        self.shell = ft.Container(
            ft.Column([
                header, ft.Container(height=18), intro, ft.Container(height=8),
                self.navigation, self.main_row, ft.Container(height=6),
                world_header, self.world_row, ft.Container(height=4), footer,
            ], spacing=18), max_width=1140,
            padding=ft.Padding.symmetric(horizontal=40, vertical=30),
        )
        # Soft radial blooms remain behind the blur, giving the glass real depth.
        background = ft.Stack([
            ft.Container(expand=True, bgcolor=BG),
            ft.Container(width=850, height=850, left=-260, top=-280,
                         gradient=ft.RadialGradient(colors=["#40357168", "#00357168"], radius=.5)),
            ft.Container(width=850, height=850, right=-300, top=0,
                         gradient=ft.RadialGradient(colors=["#453F436C", "#003F436C"], radius=.5)),
            ft.Container(width=850, height=750, left=200, bottom=-450,
                         gradient=ft.RadialGradient(colors=["#26408174", "#00408174"], radius=.5)),
        ], expand=True)
        foreground = ft.Column([
            ft.Row([self.shell], alignment=ft.MainAxisAlignment.CENTER),
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)
        self.root = ft.Stack([background, foreground], expand=True)
        page.add(self.root)
        page.on_resize = self.resize
        page.on_disconnect = self.disconnect
        page.on_connect = self.reconnect
        self.resize()
        self.refresh_mode()
        self.update_clock()
        self.update_tools()
        page.update()

    def build_world_cards(self):
        self.world_row.controls.clear()
        self.world_refs.clear()
        for city in self.world_cities:
            time_text = label("", 29, font_family="Consolas",
                              style=ft.TextStyle(letter_spacing=-1))
            detail = label("", 10, MUTED)
            icon = ft.Icon(ft.Icons.WB_SUNNY_OUTLINED, size=17, color=MINT)
            card = glass(ft.Column([
                ft.Row([label(city, 13, weight=ft.FontWeight.W_500), icon],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                time_text,
                detail,
            ], spacing=9), col={"xs": 12, "sm": 4})
            card.padding = 21
            card.border_radius = 20
            self.world_row.controls.append(card)
            self.world_refs.append((city, time_text, detail, icon))

    def resize(self, e=None):
        width = self.page.width or 1180
        self.narrow = width < 720
        self.shell.padding = ft.Padding.symmetric(horizontal=18 if self.narrow else 40, vertical=24)
        self.header_tag.visible = width > 600
        self.greeting.size = 28 if self.narrow else 34
        self.time_digits.size = 66 if width < 480 else (80 if width < 1000 else 98)
        self.time_digits.style = ft.TextStyle(letter_spacing=-5 if width < 480 else -7)
        self.stopwatch_digits.size = 48 if width < 480 else 72
        self.timer_digits.size = 72 if width < 480 else 86
        for item in self.nav_items.values():
            item.padding = ft.Padding.symmetric(horizontal=11 if self.narrow else 16, vertical=12)
        self.page.update()

    def fullscreen(self, e=None):
        self.page.window.full_screen = not self.page.window.full_screen
        self.page.update()

    def toggle_format(self, e=None):
        self.use_24h = not self.use_24h
        self.format_button.content.value = "24h  /  12h" if self.use_24h else "12h  /  24h"
        self.update_clock()
        self.page.update()

    def switch_mode(self, name):
        self.mode = name
        self.refresh_mode()
        self.update_tools()
        self.page.update()

    def refresh_mode(self):
        for name, item in self.nav_items.items():
            selected = self.mode == name
            item.bgcolor = "#213F675A" if selected else "#00FFFFFF"
            item.border = ft.Border.all(1, "#235DF3BC" if selected else "#00FFFFFF")
            item.content.controls[0].color = MINT if selected else MUTED
            item.content.controls[1].color = MINT if selected else MUTED
        self.clock_content.visible = self.mode == "Clock"
        self.stopwatch_content.visible = self.mode == "Stopwatch"
        self.timer_content.visible = self.mode == "Focus timer"
        self.format_button.visible = self.mode == "Clock"
        self.dial.visible = self.mode == "Clock"
        self.lap_list.visible = self.mode == "Stopwatch"
        self.preset_column.visible = self.mode == "Focus timer"
        self.side_heading.value = {"Clock": "A DIFFERENT PERSPECTIVE", "Stopwatch": "LAP TIMES",
                                   "Focus timer": "SET YOUR PACE"}[self.mode]
        self.analog_caption.value = {"Clock": "A moment of calm.", "Stopwatch": "Small moments. Measurable progress.",
                                     "Focus timer": "Make room for what matters."}[self.mode]
        self.render_laps()

    def draw_dial(self, now):
        center = 112
        shapes = [cv.Circle(center, center, 109, ft.Paint(color="#06FFFFFF")),
                  cv.Circle(center, center, 108, ft.Paint(color="#18FFFFFF", stroke_width=1,
                                                         style=ft.PaintingStyle.STROKE))]
        def point(angle, radius):
            return center + math.sin(angle) * radius, center - math.cos(angle) * radius
        for i in range(60):
            a = i * math.tau / 60
            major = i % 5 == 0
            x1, y1 = point(a, 89 if major else 94)
            x2, y2 = point(a, 99)
            shapes.append(cv.Line(x1, y1, x2, y2, ft.Paint(
                color="#899DAB" if major else "#354853", stroke_width=2 if major else 1)))
        for number in [12, 3, 6, 9]:
            x, y = point(number * math.tau / 12, 73)
            shapes.append(cv.Text(x, y, str(number), alignment=ft.Alignment.CENTER,
                                  style=ft.TextStyle(size=12, color=MUTED, font_family="Segoe UI")))
        for angle, length, width, color in [
            ((now.hour % 12 + now.minute / 60) * math.tau / 12, 47, 5, WHITE),
            ((now.minute + now.second / 60) * math.tau / 60, 70, 3, WHITE),
            (now.second * math.tau / 60, 80, 1.5, MINT),
        ]:
            x, y = point(angle, length)
            bx, by = point(angle, -10)
            shapes.append(cv.Line(bx, by, x, y, ft.Paint(color=color, stroke_width=width,
                                                       stroke_cap=ft.StrokeCap.ROUND)))
        shapes.extend([cv.Circle(center, center, 5, ft.Paint(color=MINT)),
                       cv.Circle(center, center, 2, ft.Paint(color=BG))])
        self.dial.shapes = shapes

    def update_clock(self):
        now = self.now()
        self.time_digits.value = now.strftime("%H:%M" if self.use_24h else "%I:%M")
        self.seconds.value = now.strftime("%S")
        self.meridiem.value = "24 H" if self.use_24h else now.strftime("%p")
        self.date_text.value = f"{now:%A}, {now:%B} {now.day}, {now:%Y}"
        self.zone_title.value = self.zone.upper()
        offset = now.utcoffset() or timedelta()
        mins = int(offset.total_seconds() // 60)
        self.utc_text.value = f"UTC{'+' if mins >= 0 else '-'}{abs(mins) // 60:02d}:{abs(mins) % 60:02d}"
        fraction = (now.hour * 3600 + now.minute * 60 + now.second) / 86400
        self.day_progress.value = fraction
        self.day_percent.value = f"{fraction:.0%} complete"
        self.footer_time.value = f"{now:%Z} · {self.utc_text.value}"
        self.draw_dial(now)
        for city, time_text, detail, icon in self.world_refs:
            city_now = self.now(city)
            difference = int(((city_now.utcoffset() or timedelta()) - offset).total_seconds() / 60)
            sign = "+" if difference >= 0 else "−"
            hours, minutes = divmod(abs(difference), 60)
            diff_text = "Same time" if difference == 0 else f"{sign}{hours}{f':{minutes:02d}' if minutes else ''}h from clock"
            date_diff = (city_now.date() - now.date()).days
            day = "Today" if date_diff == 0 else ("Tomorrow" if date_diff > 0 else "Yesterday")
            time_text.value = city_now.strftime("%H:%M" if self.use_24h else "%I:%M %p")
            detail.value = f"{day} · {diff_text}"
            daylight = 6 <= city_now.hour < 18
            icon.icon = ft.Icons.WB_SUNNY_OUTLINED if daylight else ft.Icons.NIGHTS_STAY_OUTLINED
            icon.color = "#E2CEA4" if daylight else "#ABBBE8"

    def set_action_label(self, control, text, icon):
        control.content.controls[0].icon = icon
        control.content.controls[1].value = text

    def update_tools(self):
        self.stopwatch_digits.value = format_duration(self.watch.elapsed(), centiseconds=True)
        self.stopwatch_status.value = "In motion. Keep going." if self.watch.running else (
            "A moment to pause." if self.watch.elapsed() else "Ready when you are.")
        self.set_action_label(self.stopwatch_start, "Pause" if self.watch.running else "Start",
                              ft.Icons.PAUSE_ROUNDED if self.watch.running else ft.Icons.PLAY_ARROW_ROUNDED)
        self.lap_button.disabled = not self.watch.running
        self.lap_button.opacity = 1 if self.watch.running else .4
        remaining = self.timer.remaining()
        self.timer_digits.value = format_duration(math.ceil(remaining))
        self.timer_digits.size = (58 if self.timer.total_seconds >= 3600 else 72) if (
            self.page.width or 1180) < 480 else 86
        self.timer_progress.value = remaining / self.timer.total_seconds
        self.set_action_label(self.timer_start, "Pause" if self.timer.running else (
            "Start again" if self.timer.finished else "Start focus"),
            ft.Icons.PAUSE_ROUNDED if self.timer.running else ft.Icons.PLAY_ARROW_ROUNDED)
        self.timer_status.value = "Time well spent. Take a breath." if self.timer.finished else (
            "You're here. Stay with it." if self.timer.running else "One thing at a time. You've got this.")

    def toggle_stopwatch(self, e=None):
        self.watch.toggle()
        self.update_tools()
        self.page.update()

    def reset_stopwatch(self, e=None):
        self.watch.reset()
        self.render_laps()
        self.update_tools()
        self.page.update()

    def record_lap(self, e=None):
        self.watch.lap()
        self.render_laps()
        self.page.update()

    def render_laps(self):
        if not self.watch.laps:
            self.lap_list.controls = [ft.Container(
                ft.Column([ft.Icon(ft.Icons.FLAG_OUTLINED, size=30, color="#5D7484"),
                           label("Your laps will appear here.", 12, MUTED)],
                          horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
                alignment=ft.Alignment.CENTER, height=210)]
        else:
            self.lap_list.controls = [ft.Row([
                label(f"Lap {i + 1:02d}", 12, MUTED),
                label(format_duration(total - (self.watch.laps[i - 1] if i else 0), True),
                      15, MINT, font_family="Consolas"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                for i, total in reversed(list(enumerate(self.watch.laps)))]

    def toggle_timer(self, e=None):
        if self.timer.finished:
            self.timer.reset()
        self.timer.toggle()
        self.completion_shown = False
        self.update_tools()
        self.page.update()

    def reset_timer(self, e=None):
        self.timer.reset()
        self.completion_shown = False
        self.update_tools()
        self.page.update()

    def set_timer(self, minutes):
        self.timer.reset(minutes * 60)
        self.completion_shown = False
        self.update_tools()
        self.page.update()

    def dismiss_dialog(self, e=None):
        if self._dialog:
            self.page.pop_dialog()
            self._dialog = None

    def show_dialog(self, title, content, save):
        self._dialog = ft.AlertDialog(
            title=label(title, 22), content=content, bgcolor="#18232E",
            actions=[ft.TextButton("Cancel", on_click=self.dismiss_dialog),
                     ft.TextButton("Save", on_click=save)],
            shape=ft.RoundedRectangleBorder(radius=22),
        )
        self.page.show_dialog(self._dialog)

    def timezone_dropdown(self, selected, title):
        return ft.Dropdown(value=selected, label=title, width=300,
                           options=[ft.DropdownOption(city) for city in ZONES],
                           border_radius=12, color=WHITE)

    def choose_main_zone(self, e=None):
        dropdown = self.timezone_dropdown(self.zone, "Clock timezone")
        def save(e):
            self.zone = dropdown.value
            self.dismiss_dialog()
            self.update_clock()
            self.page.update()
        self.show_dialog("Your corner of the world", dropdown, save)

    def choose_world_zones(self, e=None):
        dropdowns = [self.timezone_dropdown(city, f"World clock {i + 1}")
                     for i, city in enumerate(self.world_cities)]
        def save(e):
            self.world_cities = [d.value for d in dropdowns]
            self.dismiss_dialog()
            self.build_world_cards()
            self.update_clock()
            self.page.update()
        self.show_dialog("Keep your world close", ft.Column(dropdowns, tight=True, spacing=18), save)

    def custom_duration(self, e=None):
        field = ft.TextField(label="Minutes", value=str(int(self.timer.total_seconds / 60)),
                             width=290, keyboard_type=ft.KeyboardType.NUMBER, autofocus=True,
                             border_radius=12, suffix=label("min", 12, MUTED))
        def save(e):
            try:
                minutes = int(field.value or "")
                if not 1 <= minutes <= 1440:
                    raise ValueError
            except ValueError:
                field.error = "Choose a whole number from 1 to 1440."
                self.page.update()
                return
            self.set_timer(minutes)
            self.dismiss_dialog()
        field.on_submit = save
        self.show_dialog("How much space do you need?", field, save)

    async def tick(self):
        while self._connected:
            second = datetime.now(timezone.utc).replace(microsecond=0)
            changed_second = second != self._last_second
            if changed_second:
                self._last_second = second
                self.update_clock()
            self.update_tools()
            if self.timer.finished and not self.completion_shown:
                self.completion_shown = True
                self.mode = "Focus timer"
                self.refresh_mode()
                self.page.show_dialog(ft.SnackBar(
                    content=label("Focus complete. Take a breath — you earned it.", color=BG), bgcolor=MINT))
            if changed_second or (self.mode == "Stopwatch" and self.watch.running):
                self.page.update()
            await asyncio.sleep(.04 if self.watch.running and self.mode == "Stopwatch" else .2)

    def start(self):
        self._connected = True
        self._task = self.page.run_task(self.tick)

    def disconnect(self, e=None):
        self._connected = False
        if self._task:
            self._task.cancel()

    def reconnect(self, e=None):
        if not self._connected:
            self.start()


async def main(page: ft.Page):
    app = Chronos(page)
    app.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web", action="store_true", help="Open in your browser instead of a desktop window")
    parser.add_argument("--port", type=int, default=8550, help="Port used by browser mode (default: 8550)")
    parser.add_argument("--headless", action="store_true", help="Serve browser mode without opening a browser")
    args = parser.parse_args()
    ft.run(main, assets_dir=None, no_cdn=True,
           view=ft.AppView.WEB_BROWSER if args.web and not args.headless else (
               ft.AppView.FLET_APP if not args.web else None),
           port=args.port if args.web else 0)
