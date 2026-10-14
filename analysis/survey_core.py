"""Survey estimates for the Lonta AHS study. No real survey data are bundled."""

from statistics import NormalDist
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd

VARIANCE_GUIDE = 'https://www.census.gov/programs-surveys/ahs/tech-documentation/help-guides/quickguide_repweight.html'


def _weights(weights, replicate_weights, size):
    w = np.asarray(weights, dtype=float)
    rw = np.asarray(replicate_weights, dtype=float)
    if w.shape != (size,) or rw.shape != (size, 160):
        raise ValueError('Expected one weight and 160 supplied replicate weights per housing unit')
    if not np.isfinite(w).all() or not np.isfinite(rw).all() or (w < 0).any() or (rw < 0).any():
        raise ValueError('Weights must be finite and nonnegative')
    return w, rw


def ratio_estimate(numerator, denominator, weights, replicate_weights, *, scale=1., confidence=.90):
    """Recompute the same full-sample/domain statistic with each AHS replicate.

    Census/HUD's AHS guide specifies Fay BRR and variance 4/160 * sum((rep-full)^2).
    Inputs are already-defined unit-level contributions, not guessed categorical codes.
    """
    n, d = np.asarray(numerator, dtype=float), np.asarray(denominator, dtype=float)
    if n.ndim != 1 or d.shape != n.shape or not np.isfinite(n).all() or not np.isfinite(d).all():
        raise ValueError('Contributions must be finite, aligned one-dimensional arrays')
    if (d < 0).any() or not np.isfinite(scale) or scale <= 0 or not 0 < confidence < 1:
        raise ValueError('Invalid denominator, scale or confidence')
    w, rw = _weights(weights, replicate_weights, len(n))
    full_denom = float(d @ w)
    result = dict(estimate=None, variance=None, standard_error=None, lower=None, upper=None,
                  confidence=confidence, replicate_estimates=[], undefined_replicates=0,
                  denominator_weighted=full_denom, method='AHS Fay BRR, 160 replicates')
    if full_denom == 0:
        result['reason'] = 'empty_full_sample_denominator'
        return result
    point = float(scale * (n @ w) / full_denom)
    replica_denoms = d @ rw
    valid = replica_denoms > 0
    replicas = np.full(160, np.nan)
    replicas[valid] = scale * (n @ rw)[valid] / replica_denoms[valid]
    result.update(estimate=point, replicate_estimates=[float(x) if np.isfinite(x) else None for x in replicas],
                  undefined_replicates=int((~valid).sum()))
    if not valid.all():
        result['reason'] = 'undefined_replicate_domain; interval_withheld'
        return result
    variance = float((4. / 160) * np.sum((replicas - point) ** 2))
    standard_error = float(np.sqrt(variance))
    margin = NormalDist().inv_cdf((1 + confidence) / 2) * standard_error
    result.update(variance=variance, standard_error=standard_error, lower=point-margin, upper=point+margin)
    return result


def paired_difference_estimate(first, second, *, confidence=.90):
    """Difference of two estimates sharing the same ordered AHS replicates."""
    if not 0 < confidence < 1:
        raise ValueError('Invalid confidence level')
    points = [first.get('estimate'), second.get('estimate')]
    result = dict(estimate=None, variance=None, standard_error=None, lower=None, upper=None,
                  confidence=confidence, replicate_estimates=[], undefined_replicates=0,
                  method='Paired difference; AHS Fay BRR, 160 shared replicates')
    if any(p is None or not np.isfinite(p) for p in points):
        result['reason'] = 'undefined_component_estimate'
        return result
    point = float(points[0]-points[1])
    a, b = first.get('replicate_estimates', []), second.get('replicate_estimates', [])
    if len(a) != 160 or len(b) != 160:
        raise ValueError('Exactly 160 corresponding replicate estimates required')
    replicas = [float(x-y) if x is not None and y is not None and np.isfinite(x) and np.isfinite(y)
                else None for x, y in zip(a, b)]
    undefined = sum(r is None for r in replicas)
    result.update(estimate=point, replicate_estimates=replicas, undefined_replicates=undefined)
    if undefined:
        result['reason'] = 'undefined_paired_replicate; interval_withheld'
        return result
    variance = float((4. / 160)*np.sum((np.asarray(replicas)-point)**2))
    standard_error = float(np.sqrt(variance))
    margin = NormalDist().inv_cdf((1+confidence)/2)*standard_error
    result.update(variance=variance, standard_error=standard_error, lower=point-margin, upper=point+margin)
    return result


def validated_link(households, projects, project_id_column):
    """Validate roster grain and many-to-one CONTROL join before weighting."""
    if not project_id_column or 'CONTROL' not in households or 'CONTROL' not in projects or project_id_column not in projects:
        raise ValueError('Verified household and project key columns are required')
    if households.CONTROL.isna().any() or projects.CONTROL.isna().any() or projects[project_id_column].isna().any():
        raise ValueError('Missing roster keys')
    if households.CONTROL.duplicated().any():
        raise ValueError('Duplicate housing-unit keys')
    if projects.duplicated(['CONTROL', project_id_column]).any():
        raise ValueError('Duplicate project roster keys')
    if not projects.CONTROL.isin(households.CONTROL).all():
        raise ValueError('Orphan projects')
    return projects.merge(households, on='CONTROL', how='left', validate='many_to_one', suffixes=('', '_household'))


def _mask(values, size):
    a = np.asarray(values)
    if a.shape != (size,) or a.dtype.kind != 'b':
        raise ValueError('Use an explicit aligned boolean mask; unknown values are not true')
    return a


def household_project_vectors(households, projects, eligible_mask, qualifying_project_mask):
    """Separate a housing-unit participation indicator from its project count."""
    if households.CONTROL.isna().any() or households.CONTROL.duplicated().any():
        raise ValueError('Household keys must be nonmissing and unique')
    if not projects.CONTROL.isin(households.CONTROL).all():
        raise ValueError('Orphan projects')
    eligible = _mask(eligible_mask, len(households))
    qualifying = _mask(qualifying_project_mask, len(projects))
    counts = projects.loc[qualifying].groupby('CONTROL').size().reindex(households.CONTROL, fill_value=0).to_numpy()
    counts = np.where(eligible, counts, 0)
    return {'eligible':eligible.astype(float), 'any_project':(counts > 0).astype(float), 'project_count':counts.astype(float)}


def classify_professional(values, *, professional_codes, diy_codes):
    """Requires externally verified labels. Unknown/mixed work stays separate."""
    professional_codes, diy_codes = set(professional_codes), set(diy_codes)
    if not professional_codes or not diy_codes or professional_codes & diy_codes:
        raise ValueError('Verified disjoint nonempty professional and DIY codes required')
    pro = values.isin(professional_codes)
    diy = values.isin(diy_codes)
    return {'professional':pro, 'diy':diy, 'unknown':~(pro | diy)}


def parse_numeric(values, *, missing_codes):
    """Only documented sentinel tokens are missing; negative income can be valid."""
    tokens = values.astype('string').str.strip()
    return pd.to_numeric(tokens.mask(tokens.isin(set(missing_codes))), errors='raise').astype(float)


def weighted_quantile(values, weights, probability):
    """Weighted inverse empirical CDF; no implicit removal of unknown spending."""
    x, w = np.asarray(values, dtype=float), np.asarray(weights, dtype=float)
    if x.ndim != 1 or w.shape != x.shape or not 0 <= probability <= 1:
        raise ValueError('Invalid aligned quantile inputs')
    if not np.isfinite(x).all() or not np.isfinite(w).all() or (w < 0).any():
        raise ValueError('Explicitly resolve/filter missing values and invalid weights first')
    keep = w > 0
    if not keep.any():
        return None
    x, w = x[keep], w[keep]
    order = np.argsort(x, kind='stable')
    x, w = x[order], w[order]
    index = np.searchsorted(np.cumsum(w), probability * w.sum(), side='left')
    return float(x[min(int(index), len(x)-1)])


def normalize_puf_character_codes(values):
    """Decode the CSV's single-quote wrappers without changing code meanings."""
    tokens = values.astype('string').str.strip()
    starts, ends = tokens.str.startswith("'"), tokens.str.endswith("'")
    if (starts ^ ends).fillna(False).any():
        raise ValueError('Malformed single-quote wrapper in an AHS character code')
    wrapped = (starts & ends).fillna(False)
    return tokens.mask(wrapped, tokens.str.slice(1, -1))


def replicate_quantile_estimate(values, weights, replicate_weights, probability, *, confidence=.90):
    """Inverse-CDF quantile with a disclosed Fay BRR normal approximation."""
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all() or not 0 <= probability <= 1 or not 0 < confidence < 1:
        raise ValueError('Finite values and valid quantile/confidence required')
    w, rw = _weights(weights, replicate_weights, len(x))
    point = weighted_quantile(x, w, probability)
    result = dict(estimate=point, variance=None, standard_error=None, lower=None, upper=None,
                  confidence=confidence, undefined_replicates=0, replicate_estimates=[],
                  method='Inverse weighted CDF; AHS Fay BRR normal approximation')
    if point is None:
        result['reason'] = 'empty_full_sample_weights'
        return result
    replicas = [weighted_quantile(x, rw[:, j], probability) for j in range(160)]
    result.update(replicate_estimates=replicas, undefined_replicates=sum(r is None for r in replicas))
    if result['undefined_replicates']:
        result['reason'] = 'undefined_replicate_quantile; interval_withheld'
        return result
    variance = float((4. / 160) * np.sum((np.asarray(replicas)-point) ** 2))
    standard_error = float(np.sqrt(variance))
    margin = NormalDist().inv_cdf((1+confidence)/2) * standard_error
    result.update(variance=variance, standard_error=standard_error, lower=point-margin, upper=point+margin)
    return result


def weighted_linear_estimate(design, target, weights, replicate_weights, *, confidence=.90):
    """Descriptive weighted linear coefficients, not a causal/predictive model."""
    x, y = np.asarray(design, dtype=float), np.asarray(target, dtype=float)
    if x.ndim != 2 or not x.shape[1] or y.shape != (len(x),) or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Finite aligned design and target required')
    if not 0 < confidence < 1:
        raise ValueError('Invalid confidence level')
    w, rw = _weights(weights, replicate_weights, len(x))

    def fit(weight):
        if weight.sum() <= 0:
            return None
        normalized = weight / weight.sum()
        gram = (x.T * normalized) @ x
        if np.linalg.matrix_rank(gram) != x.shape[1]:
            return None
        return np.linalg.solve(gram, x.T @ (normalized*y))

    point = fit(w)
    if point is None:
        raise ValueError('Rank-deficient full weighted design')
    replicas = [fit(rw[:, j]) for j in range(160)]
    undefined = sum(r is None for r in replicas)
    result = dict(coefficients=point.tolist(), covariance=None, standard_errors=None,
                  lower=None, upper=None, confidence=confidence, undefined_replicates=undefined,
                  method='Weighted linear association; AHS Fay BRR')
    if undefined:
        result['reason'] = 'rank_deficient_replicate; uncertainty_withheld'
        return result
    differences = np.asarray(replicas)-point
    covariance = (4. / 160) * differences.T @ differences
    standard_errors = np.sqrt(np.maximum(0, np.diag(covariance)))
    margin = NormalDist().inv_cdf((1+confidence)/2) * standard_errors
    result.update(covariance=covariance.tolist(), standard_errors=standard_errors.tolist(),
                  lower=(point-margin).tolist(), upper=(point+margin).tolist())
    return result


SOURCE_FILES = {
    'microdata': 'AHS 2023 National PUF v1.1 CSV.zip',
    'value_labels': 'AHS 2023 Value Labels Package.zip',
    'verification': 'AHS 2023 Table Specifications and PUF Estimates for User Verification.xlsx',
    'version_notes': 'AHS 2023 National PUF Version Control.pdf',
}


def source_readiness(folder):
    """Inventory alone cannot establish trustworthy data or national findings."""
    folder = Path(folder)
    present, missing = {}, []
    for kind, name in SOURCE_FILES.items():
        path = folder / name
        if not path.is_file():
            missing.append({'kind':kind, 'filename':name})
            continue
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024), b''):
                digest.update(chunk)
        present[kind] = {'filename':name, 'bytes':path.stat().st_size, 'sha256':digest.hexdigest()}
    return {
        'status':'MISSING_PRIMARY_FILES' if missing else 'FILES_PRESENT_NOT_VALIDATED',
        'present':present, 'missing':missing, 'analysis_ready':False,
        'actual_household_count':None, 'actual_project_count':None,
        'codes_validated':False, 'official_controls_reproduced':False,
        'original_statistics_computed':False,
        'next':'Validate ZIP/schema, exact 2023 value labels and keys; reproduce official PUF controls before publishing estimates.',
    }
