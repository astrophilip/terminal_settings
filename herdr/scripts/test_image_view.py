"""Tests for image-view.py's pure parts (input parsing, title, chafa command).

Run: python3 -m unittest discover -s herdr/scripts -p 'test_*.py'
"""
import importlib.util
import os
import unittest

_spec = importlib.util.spec_from_file_location(
    "image_view", os.path.join(os.path.dirname(os.path.abspath(__file__)), "image-view.py"))
iv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(iv)


class ParseQuit(unittest.TestCase):
    def test_q_quits(self):
        self.assertEqual(iv.parse_quit(b"q"), (True, b""))

    def test_capital_q_quits(self):
        self.assertEqual(iv.parse_quit(b"Q"), (True, b""))

    def test_other_keys_ignored(self):
        self.assertEqual(iv.parse_quit(b"xj "), (False, b""))

    def test_q_inside_escape_sequence_ignored(self):
        # a stray SGR mouse report must not read as q
        self.assertEqual(iv.parse_quit(b"\x1b[<35;8;1M"), (False, b""))

    def test_partial_sequence_kept_for_next_read(self):
        self.assertEqual(iv.parse_quit(b"\x1b[<35;8"), (False, b"\x1b[<35;8"))

    def test_lone_escape_kept_for_next_read(self):
        self.assertEqual(iv.parse_quit(b"\x1b"), (False, b"\x1b"))

    def test_malformed_sequence_does_not_swallow_later_keys(self):
        self.assertEqual(iv.parse_quit(b"\x1b[\x01q"), (True, b""))

    def test_kitty_keyboard_q(self):
        self.assertEqual(iv.parse_quit(b"\x1b[113u"), (True, b""))
        self.assertEqual(iv.parse_quit(b"\x1b[81;1u"), (True, b""))

    def test_q_after_other_sequence(self):
        self.assertEqual(iv.parse_quit(b"\x1b[Aq"), (True, b""))


class Title(unittest.TestCase):
    def test_osc2_with_name(self):
        self.assertEqual(iv.title("plot.png"), "\x1b]2;plot.png\x07")

    def test_control_characters_dropped(self):
        self.assertEqual(iv.title("a\x07b\x1bc\n.png"), "\x1b]2;abc.png\x07")


class ChafaCommand(unittest.TestCase):
    def test_probe_asks_through_tty_with_short_wait(self):
        cmd = iv.chafa_command("/tmp/p.png", 80, 24, probe=True)
        self.assertIn("--probe=0.5", cmd)
        self.assertIn("--probe-mode=ctty", cmd)
        self.assertNotIn("--probe=off", cmd)

    def test_no_probe_by_default(self):
        cmd = iv.chafa_command("/tmp/p.png", 80, 24)
        self.assertIn("--probe=off", cmd)
        self.assertFalse(any(a.startswith("--probe-mode") for a in cmd))

    def test_sized_to_whole_pane(self):
        cmd = iv.chafa_command("/tmp/p.png", 80, 24)
        self.assertEqual(cmd[0], "chafa")
        self.assertIn("--view-size=80x23", cmd)   # one spare row for chafa's newline
        for opt in ("-f", "kitty", "--passthrough=none", "--animate=off",
                    "--scale=max", "--align=mid,mid"):
            self.assertIn(opt, cmd)
        self.assertEqual(cmd[-1], "/tmp/p.png")

    def test_never_below_one_row(self):
        self.assertIn("--view-size=5x1", iv.chafa_command("x.png", 5, 1))


if __name__ == "__main__":
    unittest.main()
