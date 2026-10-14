"""Reproduce published PUF controls from the pinned archive and primary workbook text."""
from pathlib import Path
from statistics import NormalDist
from datetime import datetime, timezone
import json
import hashlib
import zipfile
import os
import numpy as np
import pandas as pd
import survey_core as core
from workbook_controls import parse_c16_targets, displayed_c16_dollars, published_moe90
from private_demand_analysis import REPLICATES
from source_identity import verify_csv_archive

HERE=Path(__file__).resolve().parent
ROOT=next((p for p in HERE.parents if (p/'.git').exists()),HERE.parent)
ARCHIVE=Path(os.environ.get('LONTA_AHS_ARCHIVE',str(ROOT/'_research/ahs-2023/source/DataLumos-217661-V2-AHS-2023-National-PUF.zip')))
OUTPUT=Path(os.environ.get('LONTA_AHS_OUTPUT_DIR',str(HERE)))
OUTPUT.mkdir(parents=True,exist_ok=True)
SOURCE=HERE.parent/'source-notes/official-verification-selected-sections.md'
csv_hashes=verify_csv_archive(ARCHIVE)
targets=parse_c16_targets(SOURCE.read_text())
with zipfile.ZipFile(ARCHIVE) as z:
    with z.open('household.csv') as stream:
        h=pd.read_csv(stream,usecols=['CONTROL','INTSTATUS','TENURE','WEIGHT']+REPLICATES,dtype=str,keep_default_na=False)
    with z.open('project.csv') as stream:
        p=pd.read_csv(stream,usecols=['CONTROL','JOBTYPE','JOBDIY','JOBCOST'],dtype=str,keep_default_na=False)
for field in ['CONTROL','INTSTATUS','TENURE']:
    h[field]=core.normalize_puf_character_codes(h[field])
for field in ['CONTROL','JOBTYPE','JOBDIY']:
    p[field]=core.normalize_puf_character_codes(p[field])
for field in ['WEIGHT']+REPLICATES:
    h[field]=pd.to_numeric(h[field],errors='raise')
p['JOBCOST']=core.parse_numeric(p.JOBCOST,missing_codes=['-9'])
p['_source_row_number']=np.arange(len(p))
owners=h.loc[h.INTSTATUS.eq('1') & h.TENURE.eq('1')]
linked=core.validated_link(owners,p,'_source_row_number')
checks=[]

def total_and_moe(contributions,weights,repweights):
    full=float(contributions@weights)
    reps=contributions@repweights
    variance=float((4/160)*np.sum((reps-full)**2))
    return full,published_moe90(float(np.sqrt(variance)))

for label,mask,target,moe in [('C-01 occupied total',h.INTSTATUS.eq('1').to_numpy(),133231.,381.),
                              ('C-15 owner total',(h.INTSTATUS.eq('1') & h.TENURE.eq('1')).to_numpy(),86853.,645.)]:
    full,margin=total_and_moe(mask.astype(float),h.WEIGHT.to_numpy(float),h[REPLICATES].to_numpy(float))
    for metric,actual,expected in [('housing_units_thousands',round(full/1000),target),('moe90_thousands',round(margin/1000),moe)]:
        checks.append(dict(label=label,metric=metric,actual=actual,puf_target=expected,pass_check=actual==expected))

pw=linked.WEIGHT.to_numpy(float)
rw=linked[REPLICATES].to_numpy(float)
cost=linked.JOBCOST.to_numpy(float)
known=linked.JOBDIY.isin(['1','2']).to_numpy()
for target in targets:
    domain=np.ones(len(linked),dtype=bool) if target['codes']=='ALL' else linked.JOBTYPE.isin(target['codes']).to_numpy()
    metric=target['metric']
    if metric=='project_count_thousands':
        if target['codes']=='ALL':domain &= known
        point,margin=total_and_moe(domain.astype(float),pw,rw)
        actual=round(point/1000)
        if target['table_creator_moe90'] is not None:
            checks.append(dict(label=target['label'],metric='project_count_moe90_thousands',
                               actual=round(margin/1000),puf_target=target['table_creator_moe90'],
                               pass_check=round(margin/1000)==target['table_creator_moe90']))
    elif metric=='spending_thousands':
        domain &= known & np.isfinite(cost) & (cost>=0)
        actual=round(float(np.where(domain,cost,0)@pw)/1000)
    else:
        domain &= known & np.isfinite(cost) & (cost>0)
        if not domain.any():actual=None
        elif metric=='positive_cost_mean':
            actual=displayed_c16_dollars(float(cost[domain]@pw[domain]/pw[domain].sum()))
        elif metric=='positive_cost_median':
            actual=displayed_c16_dollars(core.weighted_quantile(cost[domain],pw[domain],.5))
        else:raise ValueError('Unrecognized metric')
    expected=target['puf_target']
    checks.append(dict(label=target['label'],metric=metric,codes=target['codes'],
                       specification=target['specification'],actual=actual,puf_target=expected,
                       table_creator_target=target['table_creator_target'],
                       pass_check=actual==expected,undefined_empty_domain=actual is None,
                       reason_for_puf_difference=target['reason_for_puf_difference']))
failed=[c for c in checks if not c['pass_check']]
receipt=dict(checkedAtUtc=datetime.now(timezone.utc).isoformat(),
    sourceUrl='https://www2.census.gov/programs-surveys/ahs/2023/AHS%202023%20Table%20Specifications%20and%20PUF%20Estimates%20for%20User%20Verification.xlsx',
    sourceRepresentation='Primary workbook parsed by document reader, not downloaded original XLSX bytes',
    sourceTextSha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),archiveSha256=hashlib.file_digest(ARCHIVE.open('rb'),'sha256').hexdigest(),
    controlScope='C-01 occupied count/MOE, C-15 owner count/MOE, all C-16 PUF count/positive-cost median/positive-cost mean/spending rows plus project-count MOEs',
    comparisons=len(checks),passed=len(checks)-len(failed),failed=len(failed),checks=checks,inputCsvHashes=csv_hashes,
    officialControlsReproduced=not failed,originalWorkbookBytesAcquired=False,
    reportingConventions={'c16DollarCells':'Four significant digits, displayed as whole dollars in parsed workbook',
                          'controlMoe90CriticalValue':1.645,
                          'criticalValueSource':'2023 AHS National Sample Design, Weighting, and Error Estimation, section5,90% critical factor',
                          'studyIntervals':'Unchanged: exact NormalDist90% critical value; source reporting convention only used to reproduce published rounded controls'},
    note='PUF controls are distinct from Table Creator IUF values. Empty cost domain remains undefined, not zero. C-16 control medians/means use JOBCOST>0; the original eight-category study separately retains nonnegative cost, as disclosed.')
(OUTPUT/'official-control-reproduction.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
pd.DataFrame(checks).to_csv(OUTPUT/'official-control-reproduction.csv',index=False)
print(json.dumps({'comparisons':len(checks),'passed':len(checks)-len(failed),'failed':failed},indent=2))
raise SystemExit(1 if failed else 0)
