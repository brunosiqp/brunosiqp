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


class TechStackCardTests(unittest.TestCase):
    def test_tech_stack_card_is_valid_and_full_width(self):
        doc = minidom.parseString(profile_cards.tech_stack_card())
        self.assertEqual(doc.documentElement.getAttribute("width"), str(profile_cards.FULL_WIDTH))

    def test_tech_stack_card_lists_every_category_and_tool(self):
        svg = profile_cards.tech_stack_card()
        for category, tools in profile_cards.TECH_STACK:
            self.assertIn(profile_cards.escape(category), svg)
            for name, _key in tools:
                self.assertIn(f">{profile_cards.escape(name)}<", svg)

    def test_every_tool_has_an_icon(self):
        for _category, tools in profile_cards.TECH_STACK:
            for _name, key in tools:
                self.assertIn(key, profile_cards.TECH_ICONS)


class StackContentTests(unittest.TestCase):
    def tools_in(self, category):
        return [name for cat, tools in profile_cards.TECH_STACK if cat == category for name, _ in tools]

    def test_ai_and_agents_category(self):
        self.assertEqual(self.tools_in("AI & agents"),
                         ["Anthropic API", "Claude Code", "MCP", "AI Agents", "LLM Automation"])

    def test_security_category(self):
        self.assertEqual(self.tools_in("Security"), ["LGPD", "Cloudflare Zero Trust"])

    def test_new_tools_in_existing_categories(self):
        for category, name in (("Languages", "TypeScript"), ("Languages", "JavaScript"), ("Languages", "CSS"),
                               ("Data", "Excel Automation"), ("Integration & automation", "Webhooks"),
                               ("Infra & tools", "Windows Server / IIS")):
            self.assertIn(name, self.tools_in(category))

    def test_learning_row_is_last_and_styled_apart(self):
        self.assertEqual(profile_cards.TECH_STACK[-1][0], profile_cards.LEARNING)
        learning = self.tools_in(profile_cards.LEARNING)
        self.assertEqual(learning, ["Hermes Agent", "Cloudflare", "Information Security", "Power BI"])
        svg = profile_cards.tech_stack_card()
        self.assertEqual(svg.count('class="chip-learning"'), len(learning))

    def test_what_i_do_includes_invi(self):
        titles = [title for title, _icon, _text in profile_cards.WHAT_I_DO]
        self.assertIn("AI assistant (Invi)", titles)
        self.assertIn("AI assistant (Invi)", profile_cards.what_i_do_card())


class WriteAllTests(unittest.TestCase):
    def test_write_all_creates_every_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = profile_cards.write_all(tmp)
            for rel in written:
                minidom.parse(os.path.join(tmp, rel))
        self.assertEqual(len(written), len(profile_cards.PROJECTS) + 3)


if __name__ == "__main__":
    unittest.main()
