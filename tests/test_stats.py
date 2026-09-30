import unittest

from tools.update_stats import aggregate, languages_svg, overview_svg


class StatsTests(unittest.TestCase):
    def setUp(self):
        repos = [{"name": "one", "stargazers_count": 2}, {"name": "two", "stargazers_count": 1}]
        self.stats = aggregate(repos, lambda repo: {"Python": 100, "JavaScript": 50} if repo["name"] == "one" else {"Python": 50})

    def test_aggregation(self):
        self.assertEqual(self.stats["repositories"], 2)
        self.assertEqual(self.stats["stars"], 3)
        self.assertEqual(self.stats["languages"]["Python"], 150)

    def test_cards_are_valid_svg_text(self):
        import xml.etree.ElementTree as ET
        for card in (languages_svg(self.stats, "30.09.2026"), overview_svg(self.stats, "30.09.2026")):
            self.assertEqual(ET.fromstring(card).tag, "{http://www.w3.org/2000/svg}svg")

    def test_empty_language_state(self):
        card = languages_svg({"languages": {}, "repositories": 0, "stars": 0}, "30.09.2026")
        self.assertIn("Пока нет данных", card)


if __name__ == "__main__":
    unittest.main()
