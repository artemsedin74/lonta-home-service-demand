import importlib.util
import importlib
import unittest


class WorkbookControlTests(unittest.TestCase):
    def core(self):
        self.assertIsNotNone(importlib.util.find_spec('workbook_controls'), 'Workbook-control parser missing')
        return importlib.import_module('workbook_controls')

    def test_uses_puf_column_and_pooled_category_codes(self):
        text = """## Home Improvement Costs
| ROWLABEL | INHERITED UNIVERSE | SUBUNIVERSE | SOURCE FILE | PUF estimate | Table Creator estimate | Table Creator Margin of Error | Reason for Difference |
| HVAC: | | | | | | | |
| Number of projects (1,000) | | (JOBTYPE = '26' or JOBTYPE = '27') | | 12,803 | 12,803 | 453 | |
| Mean expenditures (dollars) | | (JOBTYPE = '26' or JOBTYPE = '27') and JOBCOST gt 0 | | 6,835 | 6,836 | 223 | Rounded |
"""
        rows = self.core().parse_c16_targets(text)
        self.assertEqual(rows[0]['codes'], ['26', '27'])
        self.assertEqual(rows[1]['puf_target'], 6835)
        self.assertEqual(rows[1]['table_creator_target'], 6836)

    def test_empty_category_count_is_zero_but_empty_median_is_undefined(self):
        text = """## Home Improvement Costs
| ROWLABEL | INHERITED UNIVERSE | SUBUNIVERSE | SOURCE FILE | PUF estimate | Table Creator estimate | Table Creator Margin of Error | Reason for Difference |
| Landslide: | | | | | | | |
| Number of projects (1,000) | | JOBTYPE = '03' | | | | | |
| Median expenditures (dollars) | | JOBTYPE = '03' and JOBCOST gt 0 | | | | | |
"""
        rows = self.core().parse_c16_targets(text)
        self.assertEqual(rows[0]['puf_target'], 0)
        self.assertIsNone(rows[1]['puf_target'])

    def test_refuses_header_without_distinct_puf_column(self):
        with self.assertRaises(ValueError):
            self.core().parse_c16_targets('## Home Improvement Costs\n| Table Creator estimate |')

    def test_four_significant_digits_is_not_rounding_to_whole_dollars(self):
        self.assertEqual(self.core().round_significant(64847.8), 64850)
        self.assertEqual(self.core().round_significant(2910.8), 2911)

    def test_displayed_workbook_dollars_preserve_whole_dollar_cell_precision(self):
        c=self.core()
        self.assertTrue(hasattr(c,'displayed_c16_dollars'), 'Displayed dollar rounding missing')
        self.assertEqual(c.displayed_c16_dollars(876.1198112675382),876)
        self.assertEqual(c.displayed_c16_dollars(64847.8),64850)

    def test_source_rounded_critical_value_matters_at_thousand_unit_boundary(self):
        c=self.core()
        self.assertTrue(hasattr(c,'published_moe90'), 'Published MOE convention missing')
        self.assertEqual(round(c.published_moe90(75078.74800354561)/1000),124)


if __name__ == '__main__':
    unittest.main()
