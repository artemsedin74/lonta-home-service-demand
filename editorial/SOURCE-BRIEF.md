# Three angles for a home-service business story

Lonta AI source brief, October 15, 2026. These are original descriptive comparisons
from the 2023 American Housing Survey, using DataLumos 217661/V2. They concern US
occupied owner homes and work reported in the preceding 24 months at interview.
The survey's professional category means most work was done outside the household;
paid invoices and contractor licenses were not verified. Code and text were
prepared with OpenAI Codex. No independent or human review is claimed.

## 1. Central A/C work follows a different home-age pattern

**Reader:** an HVAC owner deciding which service-mix assumptions to check.

The estimated rate of professional-category central A/C projects was 90.0 homes
per 1,000 built in 1980–1999, 56.9 per 1,000 built before 1980, and 71.7 per 1,000
built in 2000 or later. These are homes with at least one qualifying project,
divided by all occupied owner homes in the respective vintage group.

The prespecified model adjusting for household income bands and Census division
puts the 1980–1999 versus pre-1980 difference at +27.1 per 1,000, with a pointwise
90% interval of 20.1–34.2. The adjusted contrast is a different estimate from the
difference between the raw rates. It does not control for equipment stock or age.

**Reporting question:** what evidence does an owner use to choose between equipment
replacement, repairs and other service lines? Home construction year alone cannot
answer it. A local operator can compare the mix of requested jobs with available
technician hours and equipment records where those are actually known.

Use figure **04-home-vintage**. Source paths begin `vintage[code=26]` and
`adjusted[code=26,vintage=1980_1999]` in `results/data.json`. The missing septic
2000+ point in the full figure is withheld for reliability, not zero demand.

## 2. Plumbing fixture counts and spending use different denominators

**Reader:** a plumbing owner interpreting a mixed project report.

For plumbing fixtures, the professional category accounts for 52.6% of weighted
projects and 74.8% of weighted known reported spending. The paired spending-minus-
project-share gap is 22.3 percentage points, with a pointwise 90% interval of
19.4–25.1. The gap is rounded from the unrounded paired estimate; subtracting the
two displayed rounded shares gives 22.2 points instead.

This comparison concerns how the same service category is split between work
mostly done inside and outside the household. It is not the share of a local
contractor's sales, a change over time or a measure of profit. Job scope and
material costs can differ between projects.

**Reporting question:** when a business says one service line is its busiest,
does it mean inquiries, projects, paid work or collected dollars? A useful owner
interview would ask how those quantities are recorded separately. The national
comparison motivates the question; it does not supply the business's answer.

Use figure **02-project-spending-shares**. Exact fields are
`categories[code=22].professional_project_share_pct`,
`professional_spending_share_pct` and `spending_minus_count_share_pp`.

## 3. A cost range and uncertainty about the median answer different questions

**Reader:** a business owner or analyst comparing a survey summary with job records.

For professional-category central A/C projects with known nonnegative outlays,
the weighted median was $6,500. The first and third quartiles were $4,000 and
$9,500. That span contains the middle half of the weighted reported-outlay
distribution. The median's separate pointwise 90% interval is $5,873–$7,127.

The quartile span describes variation between reported projects. The confidence
interval describes sampling uncertainty about the estimated median. Neither
supplies a 2026 local price, a replacement-only quote, a margin or an allowable
customer-acquisition cost. The category includes added or replaced central A/C;
individual scopes and materials differ.

**Reporting question:** how does a shop separate job scope, collected revenue and
variable cost before choosing what work to pursue? Ask for the shop's definitions
before comparing its figures with a national distribution.

Use figure **03-cost-distributions**. Source fields are
`categories[code=26].q1_cost`, `median_cost` and `q3_cost`. The figure's horizontal
spans are quartiles, not confidence intervals.

## Checks that belong in any coverage

The input is the actual DataLumos archival copy, DOI
[10.3886/E217661V2](https://doi.org/10.3886/E217661V2). Original Census-origin binary
equality is unverified. The analysis uses 160 Fay BRR replicates and pointwise
90% intervals without a multiple-comparison adjustment. Associations are
descriptive. Home age is not equipment age. The covered projects do not capture
every routine or emergency service call. Nominal reported outlays may include
materials and insurance payments; household labor is excluded.

The [canonical report](https://lonta.io/research/home-service-demand/) contains the
full tables, methods, limitations and downloads. The source repository provides
46 offline tests and receipts for 183 selected published workbook-control
comparisons. Those checks establish the specified calculations, not peer review,
a causal marketing effect or suitability for a particular business decision.
