# Figure captions and alt text

Use the complete image with its notes, or preserve the definitions below when
redrawing. All four figures summarize US occupied owner homes in the 2023 AHS,
using DataLumos 217661/V2, for projects in the preceding 24 months at interview.
Professional category means most work outside the household, not verified paid
invoices. Original Lonta figures and aggregate exports: CC BY 4.0.

Credit: **Lonta AI analysis of the 2023 American Housing Survey, DataLumos
217661/V2. Prepared with OpenAI Codex.** Link to the
[report](https://lonta.io/research/home-service-demand/) and
[input edition](https://doi.org/10.3886/E217661V2). Name any modifications.

## 01-project-frequency

**Caption:** Estimated homes with at least one professional-category project per
1,000 occupied owner homes, by service category. The denominator includes homes
reporting no project. Categories overlap and should not be added. Bounds show
pointwise 90% Fay BRR intervals. Historical reported work is not a local lead forecast.

**Alt text:** Horizontal bars compare eight project categories. Central A/C has
the highest displayed rate; septic tanks have the lowest. Bars include uncertainty
intervals and use homes with at least one project as the numerator.

**Data:** `results/categories.csv`, `homes_per1000`, `homes_lower90`, `homes_upper90`.

## 02-project-spending-shares

**Caption:** The professional-category share of project counts and of known
reported spending use separate denominators. For plumbing fixtures, the estimated
shares are 52.6% and 74.8%. Bounds show pointwise 90% Fay BRR intervals. The spending
measure covers reported outlays with varying scope and materials, not contractor
revenue or profit.

**Alt text:** Paired point-and-interval marks compare professional-category project
shares with spending shares across eight services. The spending share is higher
in each displayed category; the gap differs by service.

**Data:** `results/categories.csv`, `professional_project_pct`,
`professional_spending_pct`. Interval bounds are in `results/data.json`.

## 03-cost-distributions

**Caption:** For professional-category projects with known nonnegative costs,
dots show weighted medians and horizontal spans show first-to-third quartiles.
The spans describe the middle half of each reported-outlay distribution, not
confidence intervals. The central A/C median is $6,500 and its quartile span is
$4,000–$9,500. Nominal historical outlays are not current local quotes or margins.

**Alt text:** Dots and horizontal spans show median reported project costs and
quartile ranges for eight services. Central A/C has the largest displayed median.
The marks describe a distribution of different project scopes, including known zeros.

**Data:** `results/categories.csv`, `cost_q1`, `cost_median`, `cost_q3`.
Median confidence bounds are separate fields, `cost_median_lower90` and `cost_median_upper90`.

## 04-home-vintage

**Caption:** Raw rates of homes with at least one professional-category project
per 1,000 occupied owner homes in three construction-vintage groups. Central A/C
rates are 56.9 for pre-1980, 90.0 for 1980–1999 and 71.7 for 2000+. Bounds show
pointwise 90% Fay BRR intervals. The septic 2000+ cell is withheld for reliability.
Equipment stock is uncontrolled, and home construction year is not equipment age.

**Alt text:** Three point-and-interval series compare service categories across
pre-1980, 1980–1999 and 2000+ homes. The ordering differs by service. The septic
2000+ point is omitted; it must not be interpreted as zero.

**Data:** `results/vintage.csv`. The adjusted income/division comparisons in
`results/adjusted-vintage.csv` are separate estimates and are not the points drawn here.
