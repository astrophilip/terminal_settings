"""Tests for image-view.py's pure parts (input parsing, header layout, chafa command).

Run: python3 -m unittest discover -s herdr/scripts -p 'test_*.py'
"""
import importlib.util
import os
import re
import unittest

_spec = importlib.util.spec_from_file_location(
    "image_view", os.path.join(os.path.dirname(os.path.abspath(__file__)), "image-view.py"))
iv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(iv)

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def visible(s):
    return ANSI.sub("", s)


class ParseEvents(unittest.TestCase):
    def test_q_quits(self):
        self.assertEqual(iv.parse_events(b"q"), ([("quit",)], b""))

    def test_capital_q_quits(self):
        self.assertEqual(iv.parse_events(b"Q"), ([("quit",)], b""))

    def test_other_keys_ignored(self):
        self.assertEqual(iv.parse_events(b"xj "), ([], b""))

    def test_sgr_motion(self):
        # button 35 = motion with no button held (32 + 3)
        self.assertEqual(iv.parse_events(b"\x1b[<35;80;1M"),
                         ([("move", 80, 1)], b""))

    def test_sgr_left_press_and_release(self):
        self.assertEqual(iv.parse_events(b"\x1b[<0;79;1M\x1b[<0;79;1m"),
                         ([("press", 79, 1), ("release", 79, 1)], b""))

    def test_drag_counts_as_move(self):
        self.assertEqual(iv.parse_events(b"\x1b[<32;5;5M"), ([("move", 5, 5)], b""))

    def test_wheel_and_other_buttons_ignored(self):
        self.assertEqual(iv.parse_events(b"\x1b[<64;5;5M\x1b[<2;5;5M"), ([], b""))

    def test_focus_out_is_blur_and_focus_in_ignored(self):
        self.assertEqual(iv.parse_events(b"\x1b[O\x1b[I"), ([("blur",)], b""))

    def test_partial_sequence_kept_for_next_read(self):
        self.assertEqual(iv.parse_events(b"\x1b[<35;8"), ([], b"\x1b[<35;8"))

    def test_lone_escape_kept_for_next_read(self):
        self.assertEqual(iv.parse_events(b"\x1b"), ([], b"\x1b"))

    def test_malformed_sequence_does_not_swallow_later_keys(self):
        self.assertEqual(iv.parse_events(b"\x1b[\x01q"), ([("quit",)], b""))

    def test_kitty_keyboard_q(self):
        self.assertEqual(iv.parse_events(b"\x1b[113u\x1b[113;1u"),
                         ([("quit",), ("quit",)], b""))

    def test_q_inside_garbage_still_found(self):
        events, rest = iv.parse_events(b"\x1b[Aq")
        self.assertEqual(events, [("quit",)])
        self.assertEqual(rest, b"")


class CloseBox(unittest.TestCase):
    def test_box_is_last_three_columns_of_top_row(self):
        self.assertTrue(iv.in_close_box(80, 78, 1))
        self.assertTrue(iv.in_close_box(80, 80, 1))
        self.assertFalse(iv.in_close_box(80, 77, 1))
        self.assertFalse(iv.in_close_box(80, 80, 2))


class Header(unittest.TestCase):
    def test_fills_exact_width(self):
        for cols in (10, 40, 120):
            for hover in (False, True):
                self.assertEqual(len(visible(iv.header_line(cols, "plot.png", hover))), cols)

    def test_close_box_at_right_edge(self):
        self.assertTrue(visible(iv.header_line(40, "plot.png", False)).endswith(" ✕ "))

    def test_name_shown_and_long_name_truncated(self):
        self.assertIn("plot.png", visible(iv.header_line(40, "plot.png", False)))
        line = visible(iv.header_line(20, "a-very-long-file-name-indeed.png", False))
        self.assertEqual(len(line), 20)
        self.assertIn("…", line)

    def test_hover_changes_box_colour(self):
        self.assertNotEqual(iv.header_line(40, "p.png", False), iv.header_line(40, "p.png", True))
        self.assertIn(iv.RED_BG, iv.header_line(40, "p.png", True))
        self.assertNotIn(iv.RED_BG, iv.header_line(40, "p.png", False))

    def test_tiny_pane_does_not_break(self):
        self.assertEqual(len(visible(iv.header_line(3, "plot.png", False))), 3)


class ChafaCommand(unittest.TestCase):
    def test_sized_to_pane_below_header(self):
        cmd = iv.chafa_command("/tmp/p.png", 80, 24)
        self.assertEqual(cmd[0], "chafa")
        self.assertIn("--view-size=80x22", cmd)   # header row and one spare row for chafa's newline
        for opt in ("-f", "kitty", "--probe=off", "--passthrough=none", "--animate=off",
                    "--scale=max", "--align=mid,mid"):
            self.assertIn(opt, cmd)
        self.assertEqual(cmd[-1], "/tmp/p.png")

    def test_never_below_one_row(self):
        self.assertIn("--view-size=5x1", iv.chafa_command("x.png", 5, 2))


if __name__ == "__main__":
    unittest.main()
