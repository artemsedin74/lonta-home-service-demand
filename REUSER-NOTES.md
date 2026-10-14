# Reuser notes: three different questions in one home-service dataset

This is source material for a reader, analyst or independent editor, prepared by
Lonta AI with OpenAI Codex. It is not an independently written news story or a
client result. Use the [canonical report](https://lonta.io/research/home-service-demand/)
for the complete interpretation, sources, tables and figures.

## 1. A share of projects and a share of spending have different denominators

For plumbing fixtures, the survey professional category represents
52.6% of weighted projects (pointwise 90% interval
51.0–54.1%) and
74.8% of weighted known reported spending
(71.6–78.0%).
These are two descriptive shares, not a conversion rate, a contractor's revenue
share or evidence that marketing caused the spending difference.
Source fields: results/data.json category 22 professional_project_share_pct and
professional_spending_share_pct; results/categories.csv.

## 2. Variation between projects is different from estimate uncertainty

For professional-category central A/C projects with known nonnegative outlays,
the estimated median is $6,500. The estimated first and third
quartiles are $4,000 and $9,500: the middle half
of the weighted reported-outlay distribution. They are not a confidence interval
for the median. The median's separate pointwise 90% interval is
$5,873–$7,127.
Source fields: category 26 q1_cost/median_cost/q3_cost, with distinct lower/upper fields.

## 3. A national household estimate is not the shop's current price list

The professional-category water-heater median is $1,300; its
pointwise 90% interval is $1,206–$1,394.
The reported work can have different scopes and materials. This does not set a
local quote, job margin, acceptable acquisition cost or a 2026 marketing budget.
Source fields: category 29 median_cost and the report's cost/window notes.

## Context that must travel with every number

The input is the 2023 AHS occupied-owner sample, actual DataLumos 217661/V2 copy,
covering projects in the preceding 24 months at interview. This is not calendar-year
2023 alone. JOBDIY 2 means most work was performed outside the household, not
verified paid invoices or verification of licensing. Values are nominal reported
outlays, not contractor profit. 160 Fay BRR replicates give pointwise 90% intervals;
there is no multiple-comparison adjustment. Original Census-origin binary equality
is unverified. The source-only companion does not contain raw rows or IDs.

One small septic/home-age cell and its adjusted contrast are withheld under the
report's reliability policy. Withheld is not zero. The counts can be recovered by
complement, so this suppression is not a confidentiality guarantee. Home age is
not equipment age, and descriptive adjusted associations are not causal effects.

## Practical use without a sales inference

An owner can separate job counts, mix of work, reported outlays and their own
capacity/margin records before discussing service mix with a marketing provider.
The public service-mix-worksheet.txt supplies questions; this dataset alone cannot
predict local leads, establish advertising ROI or rank agencies.

Original Lonta aggregate data, figures and these notes: CC BY 4.0; code: MIT.
Underlying survey access/source rights are separate. No endorsement, peer review
or independent human review is claimed.
