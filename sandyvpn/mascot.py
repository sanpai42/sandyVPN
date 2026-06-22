"""Ginger cat mascot drawn on a tkinter canvas."""

from __future__ import annotations

import random
import tkinter as tk

# One pun is chosen at random each time the app launches.
CONNECTED_PUNS: tuple[str, ...] = (
    "Purrfect!",
    "Claw-some link!",
    "Meow's connected!",
    "Pawsitively on!",
    "Fur-real secure!",
    "Tail-ored tunnel!",
    "Whiskers synced!",
    "Cat-alyst online!",
    "Purr protocol on!",
    "Feline fine!",
    "No cat-astrophe!",
    "Tabby tunnel up!",
    "Paw-some ping!",
    "Meow-tunnel live!",
    "Fur-midable link!",
    "Purr-sistant VPN!",
    "Mew-nited nets!",
    "Orange you online?",
    "Ginger snap link!",
    "Nine lives, one VPN!",
    "Scratch that lag!",
    "Purr-imeter sealed!",
    "Cat-ch the signal!",
    "Litter-ally secure!",
    "Meow-mentum gained!",
    "Pounce on packets!",
    "Fur-st class tunnel!",
    "Hiss-terically fast!",
    "Claw-ver routing!",
    "Tunnel of treats!",
    "Lap-top secured!",
    "Kitty tunnel go!",
    "Sandypaws online!",
    "Paws and reflect!",
    "You've got cat-mail!",
)

CAT_WIDTH = 102
CAT_HEIGHT = 110


class GingerCatMascot:
    """Ginger cat illustration drawn directly on the top banner canvas."""

    GINGER = "#e8892b"
    GINGER_DARK = "#c46f1a"
    GINGER_LIGHT = "#f5a84a"
    BELLY = "#f0c080"
    EYE = "#ff1a1a"
    EYE_HIGHLIGHT = "#ffc8c8"
    EYE_OUTLINE = "#8b0000"
    NOSE = "#e87888"
    WHISKER = "#d4c4b0"
    OUTLINE = "#8a4f12"
    TAG = "mascot"

    def __init__(self) -> None:
        self._connected_pun = random.choice(CONNECTED_PUNS)
        self._connected = False

    def set_mood(self, connected: bool) -> None:
        self._connected = connected

    def draw(self, canvas: tk.Canvas, right_x: int, top_y: int) -> None:
        ox = right_x - CAT_WIDTH
        oy = top_y
        self._draw_cat(canvas, ox, oy, awake=self._connected)
        self._draw_speech(canvas, ox, oy)

    def _draw_cat(self, canvas: tk.Canvas, ox: int, oy: int, *, awake: bool) -> None:
        tag = self.TAG
        canvas.create_arc(
            ox + 4, oy + 62, ox + 44, oy + 102,
            start=200, extent=120, style=tk.ARC, outline=self.GINGER_DARK, width=8, tags=tag,
        )
        canvas.create_oval(
            ox + 34, oy + 66, ox + 92, oy + 106, fill=self.GINGER, outline=self.OUTLINE, width=2, tags=tag,
        )
        canvas.create_oval(ox + 48, oy + 76, ox + 78, oy + 100, fill=self.BELLY, outline="", tags=tag)
        canvas.create_oval(
            ox + 38, oy + 22, ox + 98, oy + 82, fill=self.GINGER, outline=self.OUTLINE, width=2, tags=tag,
        )
        canvas.create_polygon(
            ox + 40, oy + 38, ox + 48, oy + 12, ox + 58, oy + 34,
            fill=self.GINGER_DARK, outline=self.OUTLINE, width=1, tags=tag,
        )
        canvas.create_polygon(
            ox + 78, oy + 34, ox + 88, oy + 12, ox + 96, oy + 38,
            fill=self.GINGER_DARK, outline=self.OUTLINE, width=1, tags=tag,
        )
        canvas.create_polygon(ox + 44, oy + 34, ox + 50, oy + 20, ox + 54, oy + 36, fill=self.GINGER_LIGHT, outline="", tags=tag)
        canvas.create_polygon(ox + 82, oy + 36, ox + 86, oy + 20, ox + 92, oy + 34, fill=self.GINGER_LIGHT, outline="", tags=tag)
        if awake:
            canvas.create_oval(ox + 52, oy + 44, ox + 62, oy + 56, fill=self.EYE, outline=self.EYE_OUTLINE, width=1, tags=tag)
            canvas.create_oval(ox + 74, oy + 44, ox + 84, oy + 56, fill=self.EYE, outline=self.EYE_OUTLINE, width=1, tags=tag)
            canvas.create_oval(ox + 55, oy + 47, ox + 58, oy + 50, fill=self.EYE_HIGHLIGHT, outline="", tags=tag)
            canvas.create_oval(ox + 77, oy + 47, ox + 80, oy + 50, fill=self.EYE_HIGHLIGHT, outline="", tags=tag)
        else:
            canvas.create_arc(
                ox + 52, oy + 48, ox + 62, oy + 56,
                start=0, extent=180, style=tk.ARC, outline=self.OUTLINE, width=1, tags=tag,
            )
            canvas.create_arc(
                ox + 74, oy + 48, ox + 84, oy + 56,
                start=0, extent=180, style=tk.ARC, outline=self.OUTLINE, width=1, tags=tag,
            )
        canvas.create_polygon(
            ox + 66, oy + 56, ox + 70, oy + 60, ox + 62, oy + 60,
            fill=self.NOSE, outline=self.OUTLINE, width=1, tags=tag,
        )
        canvas.create_line(ox + 66, oy + 60, ox + 66, oy + 64, fill=self.OUTLINE, tags=tag)
        canvas.create_arc(
            ox + 58, oy + 62, ox + 66, oy + 70, start=200, extent=80, style=tk.ARC, outline=self.OUTLINE, width=1, tags=tag,
        )
        canvas.create_arc(
            ox + 66, oy + 62, ox + 74, oy + 70, start=280, extent=80, style=tk.ARC, outline=self.OUTLINE, width=1, tags=tag,
        )
        for y_off in (-2, 4):
            canvas.create_line(ox + 44, oy + 58 + y_off, ox + 58, oy + 58 + y_off, fill=self.WHISKER, width=1, tags=tag)
            canvas.create_line(ox + 96, oy + 58 + y_off, ox + 82, oy + 58 + y_off, fill=self.WHISKER, width=1, tags=tag)
        canvas.create_oval(ox + 42, oy + 98, ox + 54, oy + 110, fill=self.GINGER_DARK, outline=self.OUTLINE, width=1, tags=tag)
        canvas.create_oval(ox + 76, oy + 98, ox + 88, oy + 110, fill=self.GINGER_DARK, outline=self.OUTLINE, width=1, tags=tag)
        if not awake:
            self._draw_sleep_zzzs(canvas, ox, oy)

    def _draw_letter_z(
        self,
        canvas: tk.Canvas,
        x: int,
        y: int,
        size: int,
        color: str,
        *,
        width: int = 2,
    ) -> None:
        tag = self.TAG
        canvas.create_line(x, y, x + size, y, fill=color, width=width, tags=tag)
        canvas.create_line(x + size, y, x, y + size, fill=color, width=width, tags=tag)
        canvas.create_line(x, y + size, x + size, y + size, fill=color, width=width, tags=tag)

    def _draw_sleep_zzzs(self, canvas: tk.Canvas, ox: int, oy: int) -> None:
        """Small Z's drifting up over the forehead, clear of the speech bubble."""
        self._draw_letter_z(canvas, ox + 64, oy + 40, 3, "#7a8a9e", width=1)
        self._draw_letter_z(canvas, ox + 70, oy + 34, 4, "#95a5b8", width=1)
        self._draw_letter_z(canvas, ox + 76, oy + 28, 5, "#b0c0d4", width=1)

    def _draw_speech(self, canvas: tk.Canvas, ox: int, oy: int) -> None:
        if self._connected:
            message = self._connected_pun
            color = "#7fd67f"
        else:
            message = "Cofee with milk.."
            color = "#ffaa55"
        canvas.create_text(
            ox + 51,
            oy + 6,
            text=message,
            fill=color,
            font=("Segoe UI", 6, "italic"),
            width=96,
            anchor=tk.N,
            justify=tk.CENTER,
            tags=self.TAG,
        )
