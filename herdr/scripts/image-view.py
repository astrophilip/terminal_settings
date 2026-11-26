#!/usr/bin/env python3
"""Show an image in the current terminal pane with chafa's kitty graphics, sized to the pane.

The file name goes in the terminal title, where a pane header can show it. q closes the
viewer. Resizing the pane redraws the image once the size has settled. When the pane
reports no pixel size (herdr-app), chafa asks the terminal for its cell size instead, or it
would guess the cell shape and squash the image. Standard library only; needs chafa on PATH.

Usage: image-view.py IMAGE [--close-pane]
  --close-pane  close the herdr TUI pane ($HERDR_PANE_ID) on exit; the TUI's show-image.sh
                passes this. In herdr-app, run the viewer with exec instead.
"""
import os
import fcntl
import re
import select
import signal
import struct
import subprocess
import sys
import termios
import time
import tty

RESIZE_SETTLE = 0.12   # seconds without a resize before redrawing

MUTED_FG = "\x1b[38;2;109;112;132m"  # #6d7084, palette bright black
RESET = "\x1b[0m"

# Save the title, alternate screen, hidden cursor.
ENTER = "\x1b[22;2t\x1b[?1049h\x1b[?25l"
LEAVE = "\x1b[?25h\x1b[?1049l\x1b[23;2t"
DELETE_IMAGES = "\x1b_Ga=d,d=A\x1b\\"   # remove every image placement and free its data

ANY_CSI = re.compile(rb"\x1b\[[0-?]*[ -/]*[@-~]")
CSI_SO_FAR = re.compile(rb"\x1b\[[0-?]*[ -/]*")
KITTY_Q = re.compile(rb"\x1b\[(?:113|81)(?:;1)?u")   # q / Q in the kitty keyboard protocol


def parse_quit(buf):
    """Scan terminal input for q. Returns (quit?, unparsed tail to prepend next read)."""
    i = 0
    while i < len(buf):
        if buf[i] != 0x1b:
            if buf[i] in b"qQ":
                return True, b""
            i += 1
            continue
        if i + 1 >= len(buf):
            return False, buf[i:]           # a lone ESC may be the start of a sequence
        if buf[i + 1] != ord("["):
            i += 1                          # ESC + key (alt+key): drop the ESC, keep the key
            continue
        m = ANY_CSI.match(buf, i)
        if not m:
            if CSI_SO_FAR.fullmatch(buf, i):
                return False, buf[i:]       # incomplete sequence: wait for the rest
            i += 1                          # malformed: drop the ESC, read on
            continue
        if KITTY_Q.fullmatch(m.group(0)):
            return True, b""
        i = m.end()
    return False, b""


def title(name):
    """OSC 2: set the terminal title, without control characters that would end it early."""
    return "\x1b]2;" + "".join(c for c in name if c.isprintable()) + "\x07"


def chafa_command(path, cols, rows, probe=False):
    """chafa drawing the image over the whole pane. One spare row stops chafa's closing
    newline from scrolling the image's top row away. probe: ask the terminal for its cell
    size, through the controlling tty, waiting at most half a second for the answer."""
    probe_args = ["--probe=0.5", "--probe-mode=ctty"] if probe else ["--probe=off"]
    return (["chafa", "-f", "kitty"] + probe_args
            + ["--passthrough=none", "--animate=off", "--scale=max", "--align=mid,mid",
               f"--view-size={cols}x{max(1, rows - 1)}", path])


def draw(path):
    rows, cols, xpixel, ypixel = struct.unpack("HHHH", fcntl.ioctl(1, termios.TIOCGWINSZ, bytes(8)))
    os.write(1, (DELETE_IMAGES + "\x1b[2J\x1b[1;1H").encode())
    # chafa writes straight to the pane so it can read the pane's pixel size.
    # No pixel size (herdr-app): chafa asks the terminal for its cell size.
    done = subprocess.run(chafa_command(path, cols, rows, probe=not (xpixel and ypixel)),
                          stdin=subprocess.DEVNULL, stderr=subprocess.PIPE)
    os.write(1, b"\x1b[?25l")
    if done.returncode != 0:
        msg = done.stderr.decode(errors="replace").strip() or "chafa failed"
        os.write(1, ("\x1b[1;2H" + MUTED_FG + msg[: cols - 2] + RESET).encode())


def run(path):
    wake_r, wake_w = os.pipe()
    os.set_blocking(wake_w, False)

    def on_resize(signum, frame):
        try:
            os.write(wake_w, b"r")
        except BlockingIOError:
            pass

    signal.signal(signal.SIGWINCH, on_resize)
    draw(path)
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
            draw(path)
        if 0 in ready:
            data = os.read(0, 4096)
            if not data:
                return
            quit, buf = parse_quit(buf + data)
            if quit:
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
        os.write(1, (ENTER + title(os.path.basename(path))).encode())
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
