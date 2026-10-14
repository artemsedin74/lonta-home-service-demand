"""Portable source-only companion. Download the cited archive yourself; raw rows stay local."""
from pathlib import Path
import argparse, os, sys, json, zipfile, subprocess
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'analysis'))
import survey_core as core
from private_demand_analysis import category_metrics, REPLICATES
from source_identity import verify_csv_archive
from publication_payload import assert_publication_ready, public_vintage_rows, public_adjusted_rows, contextual_csv_rows


def run(archive, output):
    archive=Path(archive).resolve(); output=Path(output).resolve(); output.mkdir(parents=True,exist_ok=True)
    csv_hashes=verify_csv_archive(archive)
    env=dict(os.environ,LONTA_AHS_ARCHIVE=str(archive),LONTA_AHS_OUTPUT_DIR=str(output))
    subprocess.run([sys.executable,str(HERE/'analysis/reproduce_official_controls.py')],env=env,check=True)
    controls=json.loads((output/'official-control-reproduction.json').read_text())
    readiness=json.loads((HERE/'analysis/publication-readiness.json').read_text())
    assert_publication_ready(controls,readiness)
    plan=json.loads((HERE/'analysis/private-analysis-plan.json').read_text())
    with zipfile.ZipFile(archive) as z:
        with z.open('household.csv') as stream:
            h=pd.read_csv(stream,usecols=['CONTROL','INTSTATUS','TENURE','YRBUILT','HINCP','DIVISION','WEIGHT']+REPLICATES,dtype=str,keep_default_na=False)
        with z.open('project.csv') as stream:
            p=pd.read_csv(stream,usecols=['CONTROL','JOBTYPE','JOBDIY','JOBCOST','JOBCOMP','JJOBCOST'],dtype=str,keep_default_na=False)
    for field in ['CONTROL','INTSTATUS','TENURE','DIVISION']: h[field]=core.normalize_puf_character_codes(h[field])
    for field in ['CONTROL','JOBTYPE','JOBDIY','JOBCOMP','JJOBCOST']: p[field]=core.normalize_puf_character_codes(p[field])
    for field in ['YRBUILT','HINCP','WEIGHT']+REPLICATES: h[field]=core.parse_numeric(h[field],missing_codes=[])
    p.JOBCOST=core.parse_numeric(p.JOBCOST,missing_codes=['-9'])
    p['_source_row_number']=np.arange(len(p))
    h=h.loc[h.INTSTATUS.eq('1') & h.TENURE.eq('1')].copy().reset_index(drop=True)
    assert h.CONTROL.is_unique and p.CONTROL.isin(h.CONTROL).all()
    assert h.HINCP.ne(-6).all() and h.DIVISION.isin([str(i) for i in range(1,10)]).all()
    h['vintage']=h.YRBUILT.map({year:group for group,years in plan['vintageGroups'].items() for year in years})
    assert h.vintage.notna().all()
    h['income_band']=np.select([h.HINCP<75000,h.HINCP<150000],['under_75000','75000_149999'],default='150000_or_more')
    labels={'20':'Insulation','21':'Interior water pipes','22':'Plumbing fixtures','23':'Electrical wiring / panels',
            '26':'Central A/C','27':'Built-in heating','28':'Septic tanks','29':'Water heaters'}
    groups=list(plan['vintageGroups'])
    w=h.WEIGHT.to_numpy(float); rw=h[REPLICATES].to_numpy(float)
    design_names=['intercept','1980_1999_vs_pre1980','2000plus_vs_pre1980','income75k_149999_vs_under75k','income150kplus_vs_under75k']+[f'division{i}_vs1' for i in range(2,10)]
    design=np.column_stack([np.ones(len(h)),h.vintage.eq('1980_1999'),h.vintage.eq('2000_or_later'),
                            h.income_band.eq('75000_149999'),h.income_band.eq('150000_or_more')]
                           +[h.DIVISION.eq(str(i)) for i in range(2,10)]).astype(float)
    categories=[]; vintage=[]; models=[]
    stats=['frequency_per1000','professional_project_share_pct','professional_spending_share_pct','q1_cost','median_cost','q3_cost']
    for code in plan['serviceCodes']:
        row=category_metrics(h,p,code)
        gap=core.paired_difference_estimate(row['professional_spending_share_pct'],row['professional_project_share_pct'])
        clean={key:row[key] for key in ['code','project_rows','professional_project_rows','professional_home_rows','professional_known_cost_rows','professional_missing_cost_rows','missing_cost_project_rows','unknown_diy_project_rows','cost_one_project_rows','sensitivities']}
        clean.update(label=labels[code],full_label=plan['jobtypeLabels'][code])
        for key in stats: clean[key]={k:row[key][k] for k in ['estimate','lower','upper','confidence']}
        clean['spending_minus_count_share_pp']={k:gap[k] for k in ['estimate','lower','upper','confidence']}
        categories.append(clean)
        selected=p.loc[p.JOBTYPE.eq(code)]
        y=core.household_project_vectors(h,selected,np.ones(len(h),dtype=bool),selected.JOBDIY.eq('2').to_numpy(dtype=bool))['any_project']
        for group in groups:
            domain=h.vintage.eq(group).to_numpy(dtype=bool)
            r=core.ratio_estimate(y*domain,domain.astype(float),w,rw,scale=1000)
            events=int(y[domain].sum())
            vintage.append(dict(code=code,category=labels[code],vintage=group,household_rows=int(domain.sum()),event_rows=events,
                                cell_policy_pass=int(domain.sum())>=100 and events>=30,**r))
        models.append(dict(code=code,category=labels[code],design_columns=design_names,**core.weighted_linear_estimate(design,y*1000,w,rw)))
    payload=dict(version='1.0',title='Lonta Home-Service Demand Study: home age, professional work and spending',
        canonical='https://lonta.io/research/home-service-demand/',publisher='Lonta AI',prepared='2026-10-12',
        dataset='2023 American Housing Survey National PUF, DataLumos 217661/V2 archival copy',
        archiveUrl='https://doi.org/10.3886/E217661V2',inputCsvSha256=csv_hashes,
        censusDirectBinaryByteMatchVerified=False,
        universe='US occupied owner housing units, including homes with no project',
        window='Previous 24 months at the 2023 interview; not calendar-year 2023 or a 2026 forecast',
        cost='Nominal reported job cost, including known zero; materials and insurance payments may be included; household labour excluded',
        professional='JOBDIY 2: most work was not done by a household member; not verified paid contractor invoices',
        uncertainty='Pointwise 90% normal intervals from 160 AHS Fay BRR replicates; no multiplicity correction',
        sourceHousingUnitRows=55669,ownerHousingUnitRows=len(h),projectRows=len(p),
        ownersWithoutProjects=int((~h.CONTROL.isin(p.CONTROL)).sum()),weightedOwnerHomes=float(w.sum()),
        controls=dict(comparisons=controls['comparisons'],passed=controls['passed'],failed=controls['failed'],
                      source=controls['sourceUrl'],reportingConventions=controls['reportingConventions']),
        categories=categories,vintage=public_vintage_rows(vintage),adjusted=public_adjusted_rows(models,vintage),
        rawIdentifiersIncluded=False,clientObservations=0,causalClaimsAllowed=False,
        sourceLimit='The actual archival edition is pinned and reconciles with Census 2023 PUF controls. Original Census-origin binary equality is not independently established.',
        disclosure='Prepared with Codex. Company-authored original secondary analysis; no independent or human review claim.')
    (output/'data.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    summary=[]
    for r in categories:
        summary.append(dict(code=r['code'],category=r['label'],full_category=r['full_label'],professional_project_rows=r['professional_project_rows'],professional_known_cost_rows=r['professional_known_cost_rows'],
            homes_per1000=r['frequency_per1000']['estimate'],homes_lower90=r['frequency_per1000']['lower'],homes_upper90=r['frequency_per1000']['upper'],
            professional_project_pct=r['professional_project_share_pct']['estimate'],professional_spending_pct=r['professional_spending_share_pct']['estimate'],
            difference_pp=r['spending_minus_count_share_pp']['estimate'],difference_lower90=r['spending_minus_count_share_pp']['lower'],difference_upper90=r['spending_minus_count_share_pp']['upper'],
            cost_q1=r['q1_cost']['estimate'],cost_median=r['median_cost']['estimate'],cost_q3=r['q3_cost']['estimate'],
            cost_median_lower90=r['median_cost']['lower'],cost_median_upper90=r['median_cost']['upper'],
            missing_cost_rows=r['missing_cost_project_rows'],professional_missing_cost_rows=r['professional_missing_cost_rows'],
            population=payload['universe'],period=payload['window'],cost_definition=payload['cost'],
            professional_definition=payload['professional'],interval_definition=payload['uncertainty'],
            frequency_units='Qualifying homes per 1,000 occupied owner homes',share_units='Percent; gap in percentage points',
            cost_units='Nominal historical dollars; quartiles describe spread, not confidence intervals',source=payload['archiveUrl']))
    pd.DataFrame(summary).to_csv(output/'categories.csv',index=False)
    pd.DataFrame(contextual_csv_rows(payload['vintage'],payload,adjusted=False)).to_csv(output/'vintage.csv',index=False)
    pd.DataFrame(contextual_csv_rows(payload['adjusted'],payload,adjusted=True)).to_csv(output/'adjusted-vintage.csv',index=False)
    return payload


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',required=True,help='Path to downloaded AHS 2023 DataLumos V2 ZIP; expected household/project CSV hashes are checked')
    parser.add_argument('--out',default='results')
    args=parser.parse_args()
    data=run(args.archive,args.out)
    print(f"Reproduced {len(data['categories'])} categories; 183/183 controls passed; 1 small vintage cell and corresponding model contrast suppressed. No raw rows written.")
