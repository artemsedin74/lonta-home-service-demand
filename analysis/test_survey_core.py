"""Invented fixtures: tests of estimator behaviour, never US market findings."""
import math
import unittest
import tempfile
import importlib.util
import importlib
from pathlib import Path
import numpy as np
import pandas as pd
import survey_core as core


class SurveyCoreTests(unittest.TestCase):
    def call(self, name, *args, **kwargs):
        fn = getattr(core, name, None)
        self.assertIsNotNone(fn, f"Missing estimator behaviour: {name}")
        return fn(*args, **kwargs)

    def test_ratio_uses_weighted_denominator_not_mean_of_rows(self):
        # A row mean gives 50%; the declared population-weighted answer is 25%.
        r = self.call('ratio_estimate', [1, 0], [1, 1], [10, 30],
                      np.tile([10, 30], (160, 1)).T, scale=100)
        self.assertEqual(r['estimate'], 25)

    def test_undefined_denominator_is_not_zero(self):
        r = self.call('ratio_estimate', [0, 0], [0, 0], [10, 30],
                      np.tile([10, 30], (160, 1)).T)
        self.assertIsNone(r['estimate'])
        self.assertIsNone(r['standard_error'])

    def test_replication_recomputes_both_sides_of_ratio(self):
        rw = np.tile([10, 30], (160, 1)).T.astype(float)
        rw[:, 0] = [20, 20]
        r = self.call('ratio_estimate', [1, 0], [1, 1], [10, 30], rw, scale=100)
        self.assertEqual(r['replicate_estimates'][0], 50)
        self.assertAlmostEqual(r['variance'], 15.625)

    def test_empty_replicate_domain_retains_point_but_withholds_interval(self):
        rw = np.tile([10, 30], (160, 1)).T.astype(float)
        rw[:, 0] = 0
        r = self.call('ratio_estimate', [1, 0], [1, 1], [10, 30], rw)
        self.assertEqual(r['estimate'], .25)
        self.assertIsNone(r['standard_error'])
        self.assertEqual(r['undefined_replicates'], 1)

    def test_wrong_replicate_count_is_rejected(self):
        with self.assertRaises(ValueError):
            self.call('ratio_estimate', [1], [1], [1], np.ones((1, 159)))

    def test_nonfinite_or_negative_weights_are_rejected(self):
        for weights in ([1, -1], [1, float('nan')], [1, float('inf')]):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                self.call('ratio_estimate', [1, 0], [1, 1], weights, np.ones((2, 160)))

    def test_linkage_rejects_duplicate_households(self):
        with self.assertRaises(ValueError):
            self.call('validated_link', pd.DataFrame({'CONTROL':['01','01']}),
                      pd.DataFrame({'CONTROL':['01'], 'job_id':['a']}), 'job_id')

    def test_linkage_rejects_orphans(self):
        with self.assertRaises(ValueError):
            self.call('validated_link', pd.DataFrame({'CONTROL':['01']}),
                      pd.DataFrame({'CONTROL':['02'], 'job_id':['a']}), 'job_id')

    def test_linkage_rejects_duplicate_projects(self):
        with self.assertRaises(ValueError):
            self.call('validated_link', pd.DataFrame({'CONTROL':['01']}),
                      pd.DataFrame({'CONTROL':['01','01'], 'job_id':['a','a']}), 'job_id')

    def test_household_participation_deduplicates_multiple_projects(self):
        h = pd.DataFrame({'CONTROL':['01','02','03'], 'WEIGHT':[10.,20.,30.]})
        p = pd.DataFrame({'CONTROL':['01','01','02'], 'job_id':['a','b','a']})
        r = self.call('household_project_vectors', h, p, [True,True,True], [True,True,True])
        self.assertEqual(r['any_project'].tolist(), [1,1,0])
        self.assertEqual(r['project_count'].tolist(), [2,1,0])
        self.assertEqual(float(np.dot(r['any_project'], h.WEIGHT)), 30)
        self.assertEqual(float(np.dot(r['project_count'], h.WEIGHT)), 40)

    def test_outside_universe_households_do_not_enter_numerator(self):
        h = pd.DataFrame({'CONTROL':['01','02','03']})
        p = pd.DataFrame({'CONTROL':['01','02'], 'job_id':['a','a']})
        r = self.call('household_project_vectors', h, p, [True,False,True], [True,True])
        self.assertEqual(r['any_project'].tolist(), [1,0,0])
        self.assertEqual(r['eligible'].tolist(), [1,0,1])

    def test_unknown_diy_codes_are_not_called_professional(self):
        r = self.call('classify_professional', pd.Series(['pro','diy','declined','']),
                      professional_codes={'pro'}, diy_codes={'diy'})
        self.assertEqual(r['professional'].tolist(), [True,False,False,False])
        self.assertEqual(r['unknown'].tolist(), [False,False,True,True])

    def test_unverified_or_overlapping_diy_code_map_is_rejected(self):
        for pro, diy in [(set(), {'diy'}), ({'same'}, {'same'})]:
            with self.assertRaises(ValueError):
                self.call('classify_professional', pd.Series(['x']),
                          professional_codes=pro, diy_codes=diy)

    def test_zero_project_cost_is_distinct_from_missing_code(self):
        r = self.call('parse_numeric', pd.Series(['0','120','missing']), missing_codes={'missing'})
        self.assertEqual(r.iloc[0], 0)
        self.assertEqual(r.iloc[1], 120)
        self.assertTrue(math.isnan(r.iloc[2]))

    def test_negative_income_is_not_automatically_missing(self):
        r = self.call('parse_numeric', pd.Series(['-2000','not-reported']), missing_codes={'not-reported'})
        self.assertEqual(r.iloc[0], -2000)
        self.assertTrue(math.isnan(r.iloc[1]))

    def test_weighted_median_is_not_unweighted_median(self):
        self.assertEqual(self.call('weighted_quantile', [100,200,1000], [1,1,8], .5), 1000)

    def test_missing_spending_requires_explicit_filter(self):
        with self.assertRaises(ValueError):
            self.call('weighted_quantile', [100,float('nan')], [1,1], .5)

    def test_absent_primary_files_do_not_become_empty_market_results(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.call('source_readiness', Path(d))
        self.assertEqual(r['status'], 'MISSING_PRIMARY_FILES')
        self.assertFalse(r['analysis_ready'])
        self.assertIsNone(r['actual_household_count'])
        self.assertFalse(r['original_statistics_computed'])

    def test_file_presence_does_not_prove_codes_or_controls_valid(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ['AHS 2023 National PUF v1.1 CSV.zip',
                         'AHS 2023 Value Labels Package.zip',
                         'AHS 2023 Table Specifications and PUF Estimates for User Verification.xlsx',
                         'AHS 2023 National PUF Version Control.pdf']:
                (Path(d) / name).write_bytes(b'invented file-presence fixture, not survey data')
            r = self.call('source_readiness', Path(d))
        self.assertEqual(r['status'], 'FILES_PRESENT_NOT_VALIDATED')
        self.assertFalse(r['analysis_ready'])
        self.assertFalse(r['codes_validated'])
        self.assertFalse(r['official_controls_reproduced'])

    def test_character_codes_keep_leading_zero_and_unknown_values(self):
        r = self.call('normalize_puf_character_codes', pd.Series(["'01'", " '2' ", '-9', None, '']))
        self.assertEqual(r.iloc[[0, 1, 2, 4]].tolist(), ['01', '2', '-9', ''])
        self.assertTrue(pd.isna(r.iloc[3]))

    def test_character_codes_reject_broken_single_quote_wrappers(self):
        for value in ["'2", "2'"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.call('normalize_puf_character_codes', pd.Series([value]))

    def test_quantile_uncertainty_uses_replicate_quantiles_not_value_spread(self):
        rw = np.empty((3, 160))
        rw[:, :80] = np.array([6, 2, 2])[:, None]
        rw[:, 80:] = np.array([2, 2, 6])[:, None]
        r = self.call('replicate_quantile_estimate', [0, 100, 1000], [4, 4, 2], rw, .5)
        self.assertEqual(r['estimate'], 100)
        self.assertAlmostEqual(r['variance'], 1640000)

    def test_quantile_empty_replicate_withholds_interval_not_point(self):
        rw = np.tile([1, 1], (160, 1)).T.astype(float)
        rw[:, 0] = 0
        r = self.call('replicate_quantile_estimate', [100, 200], [1, 1], rw, .5)
        self.assertEqual(r['estimate'], 100)
        self.assertIsNone(r['standard_error'])
        self.assertEqual(r['undefined_replicates'], 1)

    def test_quantile_empty_full_weights_are_unknown_not_zero(self):
        r = self.call('replicate_quantile_estimate', [0, 100], [0, 0], np.zeros((2, 160)), .5)
        self.assertIsNone(r['estimate'])

    def test_weighted_linear_adjustment_removes_invented_composition_difference(self):
        x = np.array([[1, 0, 0], [1, 0, 1], [1, 1, 0], [1, 1, 1]])
        w = np.array([6, 1, 1, 6])
        r = self.call('weighted_linear_estimate', x, [0, 10, 0, 10], w, np.tile(w, (160, 1)).T)
        np.testing.assert_allclose(r['coefficients'], [0, 0, 10], atol=1e-11)

    def test_weighted_linear_model_rejects_rank_deficient_full_design(self):
        with self.assertRaises(ValueError):
            self.call('weighted_linear_estimate', [[1, 1], [1, 1]], [0, 1], [1, 1], np.ones((2, 160)))

    def test_weighted_linear_empty_replicate_withholds_uncertainty(self):
        x = np.array([[1, 0], [1, 0], [1, 1], [1, 1]])
        rw = np.ones((4, 160))
        rw[2:, 0] = 0
        r = self.call('weighted_linear_estimate', x, [0, 0, 1, 1], [1, 1, 1, 1], rw)
        np.testing.assert_allclose(r['coefficients'], [0, 1], atol=1e-11)
        self.assertIsNone(r['covariance'])
        self.assertEqual(r['undefined_replicates'], 1)

    def service_fixture(self):
        households = pd.DataFrame({'CONTROL':['a','b','c'], 'WEIGHT':[10.,20.,30.]})
        replicas = pd.DataFrame({f'REPWEIGHT{i}':[10.,20.,30.] for i in range(1, 161)})
        households = pd.concat([households, replicas], axis=1)
        projects = pd.DataFrame({'CONTROL':['a','a','b'], 'JOBTYPE':['29']*3,
                                'JOBDIY':['2','2','1'], 'JOBCOST':[100.,200.,0.],
                                'JOBCOMP':['1']*3, 'JJOBCOST':['0']*3,
                                '_source_row_number':[1,2,3]})
        return households, projects

    def category_call(self, households, projects):
        self.assertIsNotNone(importlib.util.find_spec('private_demand_analysis'), 'Missing private category estimator')
        return importlib.import_module('private_demand_analysis').category_metrics(households, projects, '29')

    def test_category_keeps_no_project_homes_in_frequency_denominator(self):
        h, p = self.service_fixture()
        r = self.category_call(h, p)
        self.assertAlmostEqual(r['frequency_per1000']['estimate'], 166.6666666667)
        self.assertEqual(r['professional_project_share_pct']['estimate'], 50)
        self.assertEqual(r['professional_spending_share_pct']['estimate'], 100)
        self.assertEqual(r['median_cost']['estimate'], 100)

    def test_category_unknown_cost_still_contributes_to_participation(self):
        h, p = self.service_fixture()
        p = pd.concat([p, pd.DataFrame({'CONTROL':['c'], 'JOBTYPE':['29'], 'JOBDIY':['2'],
                                      'JOBCOST':[np.nan], 'JOBCOMP':['1'], 'JJOBCOST':['0'],
                                      '_source_row_number':[4]})], ignore_index=True)
        r = self.category_call(h, p)
        self.assertAlmostEqual(r['frequency_per1000']['estimate'], 666.6666666667)
        self.assertEqual(r['missing_cost_project_rows'], 1)
        self.assertEqual(r['professional_spending_share_pct']['estimate'], 100)
        self.assertEqual(r['professional_known_cost_rows'], 2)
        self.assertEqual(r['professional_missing_cost_rows'], 1)

    def test_category_zero_costs_make_spending_share_unknown_but_median_zero(self):
        h, p = self.service_fixture()
        p.JOBCOST = 0.
        r = self.category_call(h, p)
        self.assertIsNone(r['professional_spending_share_pct']['estimate'])
        self.assertEqual(r['median_cost']['estimate'], 0)

    def test_share_difference_preserves_paired_replicate_covariance(self):
        a = {'estimate': 40., 'replicate_estimates': [45.]*160}
        b = {'estimate': 20., 'replicate_estimates': [25.]*160}
        r = self.call('paired_difference_estimate', a, b)
        self.assertEqual(r['estimate'], 20)
        self.assertEqual(r['variance'], 0)

    def test_share_difference_does_not_drop_undefined_replicate(self):
        a = {'estimate': 40., 'replicate_estimates': [45.]*160}
        b = {'estimate': 20., 'replicate_estimates': [25.]*159 + [None]}
        r = self.call('paired_difference_estimate', a, b)
        self.assertEqual(r['estimate'], 20)
        self.assertIsNone(r['standard_error'])


if __name__ == '__main__':
    unittest.main()
