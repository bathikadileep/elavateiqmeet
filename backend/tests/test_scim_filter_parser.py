"""
ElevateIQ — Unit Test Suite for SCIM Filter Expression Parser
==============================================================
Tests parsing SCIM 2.0 query filter expressions.
"""

import unittest
from backend.services.enterprise.scim_filter_parser import SCIMFilterParser


class SCIMFilterParserTestSuite(unittest.TestCase):

    def setUp(self):
        self.parser = SCIMFilterParser()

    def test_filter_parsing(self):
        """Test parsing SCIM filter string eq operator."""
        res = self.parser.parse_filter_string('userName eq "john@enterprise.com"')
        self.assertEqual(res["attribute"], "userName")
        self.assertEqual(res["operator"], "eq")
        self.assertEqual(res["value"], "john@enterprise.com")


if __name__ == "__main__":
    unittest.main()
