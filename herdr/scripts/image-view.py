#!/usr/bin/env python3
"""Show an image in the current terminal pane with chafa's kitty graphics, sized to the pane.

A one-row header carries the file name and a close box (✕) in the top-right corner that
turns red under the mouse. q or a click on the box closes the viewer. Resizing the pane
redraws the image once the size has settled. Standard library only; needs chafa on PATH.

Usage: image-view.py IMAGE [--close-pane]
  --close-pane  close the herdr pane ($HERDR_PANE_ID) on exit; show-image.sh passes this.
"""
import os
import re
import select
import signal
import subprocess
import sys
import termios
import time
import tty

RESIZE_SETTLE = 0.12   # seconds without a resize before redrawing

PANEL_BG = "\x1b[48;2;30;30;45m"     # #1e1e2d, herdr's panel_bg
MUTED_FG = "\x1b[38;2;109;112;132m"  # #6d7084, palette bright black
RED_BG = "\x1b[48;2;213;78;83m"      # #d54e53, palette bright red
LIGHT_FG = "\x1b[38;2;228;229;234m"  # #e4e5ea, palette bright white
BOLD, RESET = "\x1b[1m", "\x1b[0m"
CLOSE_BOX = " ✕ "

# Alternate screen, hidden cursor, mouse reporting for every movement in SGR form, focus events.
ENTER = "\x1b[?1049h\x1b[?25l\x1b[?1003h\x1b[?1006h\x1b[?1004h"
LEAVE = "\x1b[?1004l\x1b[?1006l\x1b[?1003l\x1b[?25h\x1b[?1049l"
DELETE_IMAGES = "\x1b_Ga=d,d=A\x1b\\"   # remove every image placement and free its data

SGR_MOUSE = re.compile(rb"\x1b\[<(\d+);(\d+);(\d+)([Mm])")
ANY_CSI = re.compile(rb"\x1b\[[0-?]*[ -/]*[@-~]")
CSI_SO_FAR = re.compile(rb"\x1b\[[0-?]*[ -/]*")
KITTY_Q = re.compile(rb"\x1b\[(?:113|81)(?:;1)?u")   # q / Q in the kitty keyboard protocol


def parse_events(buf):
    """Split terminal input into events. Returns (events, unparsed tail to prepend next read).

    Events: ("quit",), ("move", x, y), ("press", x, y), ("release", x, y), ("blur",).
    Coordinates are 1-based columns and rows. Other input is dropped.
    """
    events, i = [], 0
    while i < len(buf):
        if buf[i] != 0x1b:
            if buf[i] in b"qQ":
                events.append(("quit",))
            i += 1
            continue
        if i + 1 >= len(buf):
            return events, buf[i:]          # a lone ESC may be the start of a sequence
        if buf[i + 1] != ord("["):
            i += 1                          # ESC + key (alt+key): drop the ESC, keep the key
            continue
        m = ANY_CSI.match(buf, i)
        if not m:
            if CSI_SO_FAR.fullmatch(buf, i):
                return events, buf[i:]      # incomplete sequence: wait for the rest
            i += 1                          # malformed: drop the ESC, read on
            continue
        seq, i = m.group(0), m.end()
        mouse = SGR_MOUSE.fullmatch(seq)
        if mouse:
            button, x, y = (int(g) for g in mouse.group(1, 2, 3))
            button &= ~(4 | 8 | 16)         # ignore shift / alt / ctrl held with the mouse
            if button & 32:
                events.append(("move", x, y))
            elif button == 0:
                events.append(("press" if mouse.group(4) == b"M" else "release", x, y))
        elif seq == b"\x1b[O":              # focus out
            events.append(("blur",))
        elif KITTY_Q.fullmatch(seq):
            events.append(("quit",))
    return events, b""


def in_close_box(cols, x, y):
    return y == 1 and x > cols - len(CLOSE_BOX)


def header_line(cols, name, hover):
    """The top row: file name on the left, close box on the right, exactly cols wide."""
    avail = max(0, cols - len(CLOSE_BOX))
    text = " " + name
    if len(text) > avail:
        text = text[:avail - 1] + "…" if avail > 0 else ""
    box_style = RED_BG + LIGHT_FG + BOLD if hover else PANEL_BG + MUTED_FG
    return (PANEL_BG + MUTED_FG + text.ljust(avail) + RESET
            + box_style + CLOSE_BOX[-cols:] + RESET)


def chafa_command(path, cols, rows):
    """chafa drawing the image below the header. One spare row stops chafa's closing
    newline from scrolling the header off the top."""
    return ["chafa", "-f", "kitty", "--probe=off", "--passthrough=none", "--animate=off",
            "--scale=max", "--align=mid,mid", f"--view-size={cols}x{max(1, rows - 2)}", path]


class Viewer:
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.hover = False
        self.pressed = False
        self.cols, self.rows = os.get_terminal_size(1)

    def write(self, s):
        os.write(1, s.encode())

    def draw_header(self):
        self.write("\x1b7\x1b[1;1H" + header_line(self.cols, self.name, self.hover) + "\x1b8")

    def draw(self):
        self.cols, self.rows = os.get_terminal_size(1)
        self.write(DELETE_IMAGES + "\x1b[2J\x1b[1;1H"
                   + header_line(self.cols, self.name, self.hover) + "\x1b[2;1H")
        if self.rows < 3:
            return
        # chafa writes straight to the pane so it can read the pane's pixel size.
        done = subprocess.run(chafa_command(self.path, self.cols, self.rows),
                              stdin=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self.write("\x1b[?25l")
        if done.returncode != 0:
            msg = done.stderr.decode(errors="replace").strip() or "chafa failed"
            self.write("\x1b[3;2H" + MUTED_FG + msg[: self.cols - 2] + RESET)

    def handle(self, event):
        """Apply one input event. Returns True when the viewer should close."""
        kind = event[0]
        if kind == "quit":
            return True
        if kind in ("move", "press", "release"):
            inside = in_close_box(self.cols, event[1], event[2])
            if inside != self.hover:
                self.hover = inside
                self.draw_header()
            if kind == "press":
                self.pressed = inside
            elif kind == "release":
                close, self.pressed = self.pressed and inside, False
                return close
        elif kind == "blur" and self.hover:
            self.hover = False
            self.draw_header()
        return False


def run(path):
    wake_r, wake_w = os.pipe()
    os.set_blocking(wake_w, False)

    def on_resize(signum, frame):
        try:
            os.write(wake_w, b"r")
        except BlockingIOError:
            pass

    signal.signal(signal.SIGWINCH, on_resize)
    viewer = Viewer(path)
    viewer.draw()
    pending = None   # time at which to redraw after a resize
    buf = b""
    while True:
        timeout = None if pending is None else max(0.0, pending - time.monotonic())
        ready, _, _ = select.select([0, wake_r], [], [], timeout)
        if wake_r in ready:
            os.read(wake_r, 1024)
            pending = time.monotonic() + RESIZE_SETTLE
        if pending is not None and time.monotonic() >= pending:
            pending = None
            viewer.draw()
        if 0 in ready:
            data = os.read(0, 4096)
            if not data:
                return
            events, buf = parse_events(buf + data)
            if any(viewer.handle(e) for e in events):
                return


def main(argv):
    args = [a for a in argv[1:] if a != "--close-pane"]
    close_pane = "--close-pane" in argv[1:]
    if len(args) != 1:
        sys.exit("usage: image-view.py IMAGE [--close-pane]")
    path = os.path.abspath(args[0])
    saved = termios.tcgetattr(0)
    try:
        tty.setcbreak(0)
        os.write(1, ENTER.encode())
        run(path)
    except KeyboardInterrupt:
        pass
    finally:
        os.write(1, (DELETE_IMAGES + LEAVE).encode())
        termios.tcsetattr(0, termios.TCSADRAIN, saved)
    pane = os.environ.get("HERDR_PANE_ID")
    if close_pane and pane:
        subprocess.run(["herdr", "pane", "close", pane],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main(sys.argv)
