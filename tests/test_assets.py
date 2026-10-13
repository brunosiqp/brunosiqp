import glob
import os
import unittest
from xml.dom import minidom

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")


class AssetTests(unittest.TestCase):
    def test_every_asset_svg_is_valid_xml(self):
        paths = glob.glob(os.path.join(ASSETS, "*.svg"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=os.path.basename(path)):
                minidom.parse(path)


if __name__ == "__main__":
    unittest.main()
