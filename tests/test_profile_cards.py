import os
import sys
import tempfile
import unittest
from xml.dom import minidom

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import profile_cards  # noqa: E402

PROJECT = {
    "name": "Demo<Repo>",
    "description": "A tool that does many useful things for the team & the company every single day",
    "stack": [("Python", "#3572A5"), ("Docker", "#2496ED")],
    "license": "MIT",
}


class WrapTests(unittest.TestCase):
    def test_wrap_respects_width(self):
        lines = profile_cards.wrap("one two three four five six seven", 10)
        self.assertTrue(all(len(line) <= 10 for line in lines))
        self.assertEqual(" ".join(lines), "one two three four five six seven")

    def test_wrap_truncates_to_max_lines(self):
        lines = profile_cards.wrap("word " * 50, 12, max_lines=3)
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[-1].endswith("…"))


class ProjectCardTests(unittest.TestCase):
    def test_project_card_is_valid_svg(self):
        doc = minidom.parseString(profile_cards.project_card(PROJECT))
        self.assertEqual(doc.documentElement.getAttribute("width"), str(profile_cards.CARD_WIDTH))

    def test_project_card_escapes_and_shows_content(self):
        svg = profile_cards.project_card(PROJECT)
        self.assertIn("Demo&lt;Repo&gt;", svg)
        self.assertIn("&amp; the", svg)
        self.assertIn(">Python<", svg)
        self.assertIn(">Docker<", svg)
        self.assertIn(">MIT<", svg)

    def test_every_project_has_a_card_file_name(self):
        names = [profile_cards.card_file(p) for p in profile_cards.PROJECTS]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(n.startswith("assets/projects/") and n.endswith(".svg") for n in names))


class SectionCardTests(unittest.TestCase):
    def test_what_i_do_has_every_area(self):
        svg = profile_cards.what_i_do_card()
        minidom.parseString(svg)
        for title, _icon, _text in profile_cards.WHAT_I_DO:
            self.assertIn(profile_cards.escape(title), svg)

    def test_education_shows_programs_and_status(self):
        svg = profile_cards.education_card()
        minidom.parseString(svg)
        self.assertIn("SENAI", svg)
        self.assertIn("UNIASSELVI", svg)
        self.assertIn(">In progress<", svg)
        self.assertIn(">Completed<", svg)


class WriteAllTests(unittest.TestCase):
    def test_write_all_creates_every_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = profile_cards.write_all(tmp)
            for rel in written:
                minidom.parse(os.path.join(tmp, rel))
        self.assertEqual(len(written), len(profile_cards.PROJECTS) + 2)


if __name__ == "__main__":
    unittest.main()
