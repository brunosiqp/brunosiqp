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

    def test_envy_converter_is_featured_first(self):
        first = profile_cards.PROJECTS[0]
        self.assertEqual(first["name"], "envy-converter")
        self.assertEqual([label for label, _ in first["stack"]], ["C#", "WPF"])
        self.assertEqual(first["license"], "MIT")
        self.assertIn(">MIT<", profile_cards.project_card(first))

    def test_readme_shows_every_project_card(self):
        readme = open(os.path.join(os.path.dirname(__file__), "..", "README.md"), encoding="utf-8").read()
        for project in profile_cards.PROJECTS:
            self.assertIn(f'./{profile_cards.card_file(project)}', readme)
            self.assertIn(f'https://github.com/brunosiqp/{project["name"]}', readme)

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
        self.assertIn("Postgraduate in Applied AI Engineering", svg)
        self.assertIn("UNIDPS", svg)
        self.assertEqual(svg.count(">In progress<"), 2)
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
                         ["Anthropic API", "Claude Code", "AI Agents", "LLM Automation"])

    def test_security_category(self):
        self.assertEqual(self.tools_in("Security"), ["LGPD", "Cloudflare Zero Trust", "Information Security"])

    def test_new_tools_in_existing_categories(self):
        for category, name in (("Languages", "TypeScript"), ("Languages", "JavaScript"), ("Languages", "CSS"),
                               ("Data", "Excel Automation"), ("Data", "Power BI"), ("Integration & automation", "Webhooks"),
                               ("Infra & tools", "Windows Server / IIS"), ("Infra & tools", "Docker"), ("Infra & tools", "Kubernetes"), ("Infra & tools", "Minikube")):
            self.assertIn(name, self.tools_in(category))

    def test_learning_row_is_last_and_styled_apart(self):
        self.assertEqual(profile_cards.TECH_STACK[-1][0], profile_cards.LEARNING)
        learning = self.tools_in(profile_cards.LEARNING)
        self.assertEqual(learning, ["MCP", "LMM (Multimodal AI)", "Hermes Agent", "Ollama", "n8n"])
        svg = profile_cards.tech_stack_card()
        self.assertEqual(svg.count('class="chip-learning"'), len(learning))

    def test_what_i_do_includes_invi(self):
        titles = [title for title, _icon, _text in profile_cards.WHAT_I_DO]
        self.assertIn("AI assistant (Invi)", titles)
        self.assertIn("AI assistant (Invi)", profile_cards.what_i_do_card())

    def test_invi_text_says_i_built_it(self):
        text = next(text for title, _icon, text in profile_cards.WHAT_I_DO if "Invi" in title)
        self.assertTrue(text.startswith("I built Invi"))
        self.assertNotIn("help build", text)


class CertificationsCardTests(unittest.TestCase):
    def test_card_is_valid_accessible_and_full_width(self):
        svg = profile_cards.certifications_card()
        doc = minidom.parseString(svg)
        self.assertEqual(doc.documentElement.getAttribute("width"), str(profile_cards.FULL_WIDTH))
        self.assertEqual(len(doc.getElementsByTagName("title")), 1)
        self.assertEqual(len(doc.getElementsByTagName("desc")), 1)

    def test_enabled_entries_render_newest_first(self):
        svg = profile_cards.certifications_card()
        titles = [c["title"] for c in profile_cards.enabled_sorted(profile_cards.CERTIFICATIONS)]
        positions = [svg.index(profile_cards.escape(t.split(":")[0])) for t in titles]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(titles[1], "Python Fundamentals for Data Analysis, Data Science and Machine Learning")
        self.assertNotIn("69c31d106fe1260abe039cb7", svg)
        self.assertIn(">Machine Learning<", svg)

    def test_disabled_entries_are_not_rendered(self):
        entries = [dict(c, enabled=c["issuer"] != "Microsoft") for c in profile_cards.CERTIFICATIONS]
        svg = profile_cards.certifications_card(entries)
        self.assertNotIn("Microsoft Foundry SDK", svg)
        self.assertNotIn("Microsoft Applied Skills", svg)

    def test_applied_skills_is_live_and_newest(self):
        first = profile_cards.enabled_sorted(profile_cards.CERTIFICATIONS)[0]
        self.assertEqual(first["issuer"], "Microsoft")
        self.assertEqual(first["date"], "Nov 2026")
        self.assertIn(">Microsoft Applied Skills<", profile_cards.certifications_card())

    def test_enabled_applied_skills_entry_gets_badge(self):
        entries = [dict(c, enabled=True) for c in profile_cards.CERTIFICATIONS]
        svg = profile_cards.certifications_card(entries)
        minidom.parseString(svg)
        self.assertIn(">Microsoft Applied Skills<", svg)

    def test_sort_puts_newest_first(self):
        entries = [{"title": t, "date": d, "enabled": True} for t, d in (("a", "Oct 2020"), ("b", "Mar 2026"), ("c", "Sep 2024"))]
        self.assertEqual([e["title"] for e in profile_cards.enabled_sorted(entries)], ["b", "c", "a"])


class MicrosoftLearnCardTests(unittest.TestCase):
    def test_card_lists_completed_modules(self):
        svg = profile_cards.microsoft_learn_card()
        doc = minidom.parseString(svg)
        self.assertEqual(len(doc.getElementsByTagName("title")), 1)
        self.assertIn("Completed modules", svg)
        for module in profile_cards.MICROSOFT_LEARN:
            self.assertIn(profile_cards.escape(module["title"]), svg)
        self.assertIn("1 h 20 min", svg)

    def test_disabled_modules_are_not_rendered(self):
        entries = profile_cards.MICROSOFT_LEARN + [dict(profile_cards.MICROSOFT_LEARN[0], title="Hidden module", enabled=False)]
        self.assertNotIn("Hidden module", profile_cards.microsoft_learn_card(entries))

    def test_readme_embeds_new_sections_after_education(self):
        readme = open(os.path.join(os.path.dirname(__file__), "..", "README.md"), encoding="utf-8").read()
        order = [readme.index(h) for h in ("## Education", "## Certifications", "## Microsoft Learn", "## Contact")]
        self.assertEqual(order, sorted(order))
        self.assertIn("./assets/certifications.svg", readme)
        self.assertIn("./assets/microsoft-learn.svg", readme)


class WriteAllTests(unittest.TestCase):
    def test_write_all_creates_every_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = profile_cards.write_all(tmp)
            for rel in written:
                minidom.parse(os.path.join(tmp, rel))
        self.assertEqual(len(written), len(profile_cards.PROJECTS) + 5)


if __name__ == "__main__":
    unittest.main()
