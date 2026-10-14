"""Read the primary workbook's distinct PUF controls without executing its SAS text."""
import math
import re


def round_significant(value, digits=4):
    if not math.isfinite(value) or digits<1:
        raise ValueError('Finite value and positive precision required')
    return float(f'{value:.{digits}g}')


def displayed_c16_dollars(value):
    """Compare the visible whole-dollar cell after four-significant-digit rounding."""
    return round(round_significant(value))


def published_moe90(standard_error):
    """Census 2023 accuracy statement's printed 90% critical factor, 1.645."""
    if not math.isfinite(standard_error) or standard_error<0:
        raise ValueError('Finite nonnegative standard error required')
    return 1.645*standard_error


def parse_c16_targets(markdown):
    start=markdown.find('## Home Improvement Costs')
    if start<0:
        raise ValueError('Missing C-16 section')
    end=markdown.find('\n## ',start+4)
    section=markdown[start:end if end>=0 else None]
    if 'SOURCE FILE | PUF estimate | Table Creator estimate' not in section:
        raise ValueError('Distinct PUF and Table Creator columns required')
    names={'Number of projects (1,000)':'project_count_thousands',
           'Median expenditures (dollars)':'positive_cost_median',
           'Mean expenditures (dollars)':'positive_cost_mean',
           'Total expenditures (1,000)':'spending_thousands'}
    rows=[]
    label=None
    for line in section.splitlines():
        if not line.startswith('|'):
            continue
        fields=[f.strip() for f in line.split('|')[1:-1]]
        if len(fields)!=8:
            continue
        if fields[0].endswith(':'):
            label=fields[0][:-1]
        if fields[0] not in names:
            continue
        if label is None:
            raise ValueError('Control has no category label')
        codes=re.findall(r"JOBTYPE\s*=\s*'(\d{2})'",fields[2])
        if not codes and label!='Total':
            raise ValueError('Unsupported category predicate')
        metric=names[fields[0]]
        def number(token):
            if token in ['', '.', 'NA', 'S']:
                return None
            if token=='Z':
                return 0.
            return float(token.replace(',',''))
        puf=number(fields[4])
        if fields[4]=='' and metric in ['project_count_thousands','spending_thousands']:
            puf=0.
        rows.append(dict(label=label,codes=codes if codes else 'ALL',metric=metric,
                         specification=fields[2],puf_target=puf,
                         table_creator_target=number(fields[5]),table_creator_moe90=number(fields[6]),
                         reason_for_puf_difference=fields[7],source_line=line))
    if not rows:
        raise ValueError('No numeric controls parsed')
    return rows
