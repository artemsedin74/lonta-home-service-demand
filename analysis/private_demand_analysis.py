"""Private survey calculations; this module does not authorize publication."""
import numpy as np
import survey_core as core

REPLICATES = [f'REPWEIGHT{i}' for i in range(1, 161)]


def category_metrics(households, projects, code):
    """Inputs are already-decoded occupied-owner records and retained project rows."""
    selected = projects.loc[projects.JOBTYPE.eq(code)].copy()
    linked = core.validated_link(households, selected, '_source_row_number')
    pro = selected.JOBDIY.eq('2').fillna(False).to_numpy(dtype=bool)
    known = selected.JOBDIY.isin(['1', '2']).to_numpy(dtype=bool)
    eligible = np.ones(len(households), dtype=bool)
    vectors = core.household_project_vectors(households, selected, eligible, pro)
    weights = households.WEIGHT.to_numpy(float)
    replicas = households[REPLICATES].to_numpy(float)
    pw, pr = linked.WEIGHT.to_numpy(float), linked[REPLICATES].to_numpy(float)
    costs = selected.JOBCOST.to_numpy(float)
    cost_known = np.isfinite(costs) & (costs >= 0)
    professional_costs = pro & cost_known
    frequency = core.ratio_estimate(vectors['any_project'], vectors['eligible'], weights, replicas, scale=1000)
    count_share = core.ratio_estimate(pro.astype(float), known.astype(float), pw, pr, scale=100)
    spending_share = core.ratio_estimate(np.where(pro & cost_known, costs, 0),
                                       np.where(known & cost_known, costs, 0), pw, pr, scale=100)
    quartiles = {name: core.replicate_quantile_estimate(costs[professional_costs], pw[professional_costs],
                                                     pr[professional_costs], probability)
                 for name, probability in [('q1_cost', .25), ('median_cost', .5), ('q3_cost', .75)]}
    sensitivity_masks = {
        'completed_only_median': professional_costs & selected.JOBCOMP.eq('1').to_numpy(dtype=bool),
        'cost_flag_zero_median': professional_costs & selected.JJOBCOST.eq('0').to_numpy(dtype=bool),
        'exclude_cost_one_median': professional_costs & (costs != 1),
    }
    sensitivities = {name: {'rows': int(mask.sum()),
                            'estimate': core.weighted_quantile(costs[mask], pw[mask], .5)}
                     for name, mask in sensitivity_masks.items()}
    return dict(code=code, housing_unit_rows=len(households), project_rows=len(selected),
                professional_project_rows=int(pro.sum()), professional_home_rows=int(vectors['any_project'].sum()),
                professional_known_cost_rows=int(professional_costs.sum()),
                professional_missing_cost_rows=int((pro & ~cost_known).sum()),
                unknown_diy_project_rows=int((~known).sum()), missing_cost_project_rows=int((~cost_known).sum()),
                cost_one_project_rows=int((costs == 1).sum()),
                frequency_per1000=frequency, professional_project_share_pct=count_share,
                professional_spending_share_pct=spending_share, sensitivities=sensitivities, **quartiles)
