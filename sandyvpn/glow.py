"""Connected-state top banner with glow and uptime drawn on canvas."""

from __future__ import annotations

import tkinter as tk

from sandyvpn.mascot import GingerCatMascot
from sandyvpn.theme import ACCENT_LINE, BG, FG_MUTED, ORANGE_BRIGHT, blend_hex

GLOW_GREEN = "#3d9a5c"
UPTIME_Y = 22
HEADER_Y_CONNECTED = 46
ACCENT_HEIGHT = 3
BANNER_CONNECTED_HEIGHT = 188
BANNER_DISCONNECTED_HEIGHT = 128
TITLE_FONT = ("Segoe UI", 18, "bold")
SUBTITLE_FONT = ("Segoe UI", 10)


def draw_connected_glow(canvas: tk.Canvas, width: int, height: int) -> None:
    if width < 2 or height < 2:
        return

    cx = width / 2
    steps = 36
    for i in range(steps):
        t = (1 - i / steps) ** 1.3
        color = blend_hex(BG, GLOW_GREEN, 0.24 * t)
        y1 = height * i / steps
        y2 = height * (i + 1) / steps
        canvas.create_rectangle(0, y1, width, y2, fill=color, outline="", tags="glow")

    for i, strength in enumerate((0.18, 0.11, 0.06)):
        radius = width * (0.64 - i * 0.14)
        color = blend_hex(BG, GLOW_GREEN, strength)
        canvas.create_oval(
            cx - radius,
            -radius * 0.4,
            cx + radius,
            radius * 0.8,
            fill=color,
            outline="",
            tags="glow",
        )


class TopBanner(tk.Canvas):
    """Top section: glow, uptime, title text, mascot, accent line."""

    def __init__(self, master: tk.Misc, **kwargs) -> None:
        super().__init__(master, bg=BG, highlightthickness=0, height=BANNER_DISCONNECTED_HEIGHT, **kwargs)
        self._mascot: GingerCatMascot | None = None
        self._uptime_item: int | None = None
        self._connected = False
        self._uptime_text = ""
        self.bind("<Configure>", self._on_resize)

    def set_mascot(self, mascot: GingerCatMascot) -> None:
        self._mascot = mascot
        self._redraw()

    def set_connected(self, connected: bool) -> None:
        self._connected = connected
        self.update_idletasks()
        self._redraw()

    def set_uptime_text(self, text: str) -> None:
        self._uptime_text = text
        if self._connected:
            self._redraw()

    def _on_resize(self, _event: tk.Event) -> None:
        self._redraw()

    def _draw_titles(self, header_y: int) -> None:
        title_y = header_y + 22
        subtitle_y = header_y + 44
        self.create_text(
            0,
            title_y,
            text="sandyOVPN",
            anchor=tk.W,
            fill=ORANGE_BRIGHT,
            font=TITLE_FONT,
            tags="titles",
        )
        self.create_text(
            0,
            subtitle_y,
            text="OpenVPN 3 session launcher",
            anchor=tk.W,
            fill=FG_MUTED,
            font=SUBTITLE_FONT,
            tags="titles",
        )

    def _redraw(self) -> None:
        self.delete("glow", "uptime", "accent", "titles", GingerCatMascot.TAG)
        self._uptime_item = None

        width = max(self.winfo_width(), 2)
        height = BANNER_CONNECTED_HEIGHT if self._connected else BANNER_DISCONNECTED_HEIGHT
        self.configure(height=height)

        header_y = HEADER_Y_CONNECTED if self._connected else 0

        if self._connected:
            draw_connected_glow(self, width, height)
            if self._uptime_text:
                self._uptime_item = self.create_text(
                    width / 2,
                    UPTIME_Y,
                    text=self._uptime_text,
                    fill="#9ef09e",
                    font=("Segoe UI", 13, "bold"),
                    tags="uptime",
                )

        self._draw_titles(header_y)

        if self._mascot is not None:
            self._mascot.draw(self, width - 4, header_y)

        accent_y = height - ACCENT_HEIGHT
        self.create_rectangle(0, accent_y, width, height, fill=ACCENT_LINE, outline="", tags="accent")

        if self._uptime_item is not None:
            self.tag_raise("uptime")
        self.tag_raise("titles")
        self.tag_raise(GingerCatMascot.TAG)
        self.tag_raise("accent")
