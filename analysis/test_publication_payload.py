import importlib, importlib.util, unittest


class PublicationPayloadTests(unittest.TestCase):
    def core(self):
        self.assertIsNotNone(importlib.util.find_spec('publication_payload'), 'Publication guard missing')
        return importlib.import_module('publication_payload')

    def test_failed_control_cannot_be_published(self):
        with self.assertRaises(ValueError):
            self.core().assert_publication_ready({'officialControlsReproduced':False,'failed':1}, {'archiveEditionVerified':True})

    def test_control_pass_does_not_establish_unpinned_source_identity(self):
        with self.assertRaises(ValueError):
            self.core().assert_publication_ready({'officialControlsReproduced':True,'failed':0,'passed':183,'comparisons':183}, {'archiveEditionVerified':False})

    def test_public_export_removes_small_cell_estimates_and_replicates(self):
        rows=[{'code':'28','vintage':'2000_or_later','category':'Septic tanks','cell_policy_pass':False,
               'household_rows':6000,'event_rows':21,'estimate':3.3,'lower':2.2,'upper':4.5,'replicate_estimates':[3.3]*160},
              {'code':'26','vintage':'1980_1999','category':'Central A/C','cell_policy_pass':True,
               'household_rows':7000,'event_rows':700,'estimate':90.,'lower':83.,'upper':97.,'replicate_estimates':[90.]*160}]
        output=self.core().public_vintage_rows(rows)
        self.assertIsNone(output[0]['estimate'])
        self.assertIsNone(output[0]['event_rows'])
        self.assertTrue(output[0]['suppressed'])
        self.assertEqual(output[1]['estimate'],90.)
        self.assertNotIn('replicate_estimates',output[0])
        self.assertNotIn('replicate_estimates',output[1])
        self.assertEqual(rows[0]['estimate'],3.3)

    def test_model_contrast_obeys_the_same_cell_policy(self):
        models=[{'code':'28','category':'Septic tanks','coefficients':[0,-1,-3],
                 'lower':[0,-2,-5],'upper':[0,0,-1]}]
        cells=[{'code':'28','vintage':'pre_1980','cell_policy_pass':True},
               {'code':'28','vintage':'1980_1999','cell_policy_pass':True},
               {'code':'28','vintage':'2000_or_later','cell_policy_pass':False}]
        rows=self.core().public_adjusted_rows(models,cells)
        self.assertEqual(rows[0]['estimate'],-1)
        self.assertIsNone(rows[1]['estimate'])
        self.assertIsNone(rows[1]['lower'])


if __name__=='__main__': unittest.main()
