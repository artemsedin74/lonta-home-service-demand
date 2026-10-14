"""Publication guards and consistent small-cell filtering for all public outputs."""


def assert_publication_ready(controls, provenance):
    if not (controls.get('officialControlsReproduced') is True and controls.get('failed')==0
            and controls.get('comparisons',0)>0 and controls.get('passed')==controls.get('comparisons')):
        raise ValueError('Primary PUF control reproduction has not passed')
    if not (provenance.get('archiveEditionVerified') is True
            and provenance.get('archiveSourceHashPinned') is True
            and provenance.get('businessFieldSemanticsCrosschecked') is True
            and provenance.get('decision')=='READY_FOR_PUBLICATION_WITH_DISCLOSED_ARCHIVAL_PROVENANCE'):
        raise ValueError('Source identity and explicit provenance decision required')


def public_vintage_rows(rows):
    output=[]
    for r in rows:
        suppressed=not r['cell_policy_pass']
        output.append(dict(code=r['code'],category=r['category'],vintage=r['vintage'],
                           household_rows=r['household_rows'],event_rows=None if suppressed else r['event_rows'],
                           estimate=None if suppressed else r['estimate'],lower=None if suppressed else r['lower'],
                           upper=None if suppressed else r['upper'],confidence=r.get('confidence',.9),
                           suppressed=suppressed,
                           suppression_reason='Prespecified minimum 100 homes / 30 events not met' if suppressed else None))
    return output


def public_adjusted_rows(models, vintage_rows):
    supported={(r['code'],r['vintage']):r['cell_policy_pass'] for r in vintage_rows}
    output=[]
    for m in models:
        for i,group in [(1,'1980_1999'),(2,'2000_or_later')]:
            suppressed=not (supported.get((m['code'],'pre_1980'),False) and supported.get((m['code'],group),False))
            output.append(dict(code=m['code'],category=m['category'],vintage=group,reference='pre_1980',
                               estimate=None if suppressed else m['coefficients'][i],
                               lower=None if suppressed else m['lower'][i],upper=None if suppressed else m['upper'][i],
                               confidence=.9,suppressed=suppressed,
                               adjustment='Descriptive weighted linear probability; income bands and Census division',
                               causal=False))
    return output


def contextual_csv_rows(rows, context, *, adjusted):
    """Carry essential measurement definitions with every standalone CSV row."""
    units=('Difference in qualifying homes per 1,000 occupied owner homes versus pre-1980; income/division adjusted'
           if adjusted else 'Homes with at least one professional-category project per 1,000 occupied owner homes in this vintage group')
    return [dict(r, units=units, population=context['universe'], period=context['window'],
                 professional_definition=context['professional'], interval_definition=context['uncertainty'],
                 source=context['archiveUrl']) for r in rows]
