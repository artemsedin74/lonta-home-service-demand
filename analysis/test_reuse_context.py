"""Regression checks for findings that must survive standalone file reuse."""
import unittest, tempfile
from pathlib import Path
from unittest.mock import patch
import publication_payload
try:
    import render_public_figures as figures
except ModuleNotFoundError:
    import render_figures as figures

class ReuseContextTests(unittest.TestCase):
    def test_standalone_vintage_csv_has_units_period_proxy_and_source(self):
        context={'universe':'Occupied owner homes, including no-project homes',
                 'window':'Preceding 24 months at the 2023 interview',
                 'professional':'Most work outside the household; paid invoices not verified',
                 'uncertainty':'Pointwise 90% Fay BRR normal intervals; no multiplicity adjustment',
                 'archiveUrl':'https://doi.org/10.3886/E217661V2'}
        source=[{'code':'28','estimate':None,'suppressed':True}]
        raw=publication_payload.contextual_csv_rows(source,context,adjusted=False)[0]
        adjusted=publication_payload.contextual_csv_rows(source,context,adjusted=True)[0]
        self.assertIn('per 1,000',raw['units'])
        self.assertIn('difference',adjusted['units'].lower())
        for row in [raw,adjusted]:
            self.assertEqual(row['population'],context['universe'])
            self.assertEqual(row['period'],context['window'])
            self.assertEqual(row['professional_definition'],context['professional'])
            self.assertEqual(row['interval_definition'],context['uncertainty'])
            self.assertEqual(row['source'],context['archiveUrl'])
            self.assertIsNone(row['estimate'])
        self.assertNotIn('units',source[0])

    def test_actual_rendered_figures_keep_professional_proxy(self):
        metric=lambda x: {'estimate':x,'lower':x-1,'upper':x+1}
        row={'code':'20','label':'Insulation','frequency_per1000':metric(10),
             'professional_project_share_pct':metric(60),'professional_spending_share_pct':metric(80),
             'q1_cost':metric(100),'median_cost':metric(200),'q3_cost':metric(300)}
        data={'categories':[row],'vintage':[dict(code='20',vintage=g,estimate=10,lower=9,upper=11,suppressed=False)
              for g in ['pre_1980','1980_1999','2000_or_later']]}
        figures.plt.close('all')
        try:
            with tempfile.TemporaryDirectory() as temp, patch.object(figures.plt,'close'):
                names=figures.render(data,temp)
                self.assertEqual(len(names),4)
                rendered=[figures.plt.figure(n) for n in figures.plt.get_fignums()]
                for i in [0,2,3]:
                    text=' '.join([t.get_text() for t in rendered[i].texts]+[rendered[i].axes[0].get_title()])
                    self.assertIn('most work outside household',text)
                cost_text=' '.join([t.get_text() for t in rendered[2].texts]+[rendered[2].axes[0].get_title()])
                self.assertIn('professional-category projects',cost_text)
                self.assertTrue(all((Path(temp)/(name+'.png')).exists() for name in names))
        finally:figures.plt.close('all')

if __name__=='__main__':unittest.main()
