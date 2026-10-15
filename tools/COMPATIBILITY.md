# Service-mix workbook: Google Sheets compatibility check

The [blank planner](lonta-service-mix-v1.xlsx) was imported into an ordinary Google
Sheets session on October 15, 2026. The checks below used invented inputs through
the spreadsheet UI, then read the actual recalculated values and exported XLSX
caches. This is a bounded compatibility check, not app/version certification or
independent human review. Prepared by Lonta AI with OpenAI Codex.

## Open a working copy

Download the XLSX, open Google Sheets' file picker and upload it. Work in your own
copy. Enter a qualified team pool, one start/end window, available technician-hours
and your service inputs in the yellow cells. Use Records, Estimate or Mixed for
the input basis. The supplied worksheet starts blank; its separate worked example
does not populate the plan. Display separators can follow your Google Sheets locale.

## Representative checks

All example amounts are USD. Contribution is net collections minus the entered
variable costs, before fixed overhead, taxes and marketing. It is not profit.

The complete invented fixture has five maintenance jobs at 900 collected, 650
variable cost and two all-in technician-hours each; plus three replacement jobs at
3,600 collected, 2,800 variable cost and ten technician-hours each. Both lines use
Estimate as their basis. The same qualified team has 50 available hours in one
window. These amounts are teaching inputs, not observed customers, market prices,
demand, a forecast or an advertising-budget recommendation.

| Condition | Actual result checked |
| --- | --- |
| Blank template | No fabricated hours/contribution totals; prompt to enter a service plan. |
| Complete two-service fixture | 40 planned technician-hours, 10 remaining and 3,650 contribution. Unit contributions/hour are 125 and 80; both lines show Ready. |
| Replacement variable cost cleared | Top-level totals withheld, with Add job inputs for that row. The missing amount is not replaced with zero or a partial total. |
| Replacement planned jobs set to zero | 10 total hours and 1,250 contribution; the zero-job line shows Zero planned and n.a. unit economics. Its total zeros display as dashes under the workbook's number format. |
| Complete fixture, only 30 hours available | 40 hours planned, negative 10 hours remaining and an explicit capacity-shortage message; contribution stays 3,650. |

The downloaded Google Sheets XLSX for the capacity-shortage fixture retained all
52 formula cells (including shared-formula references). Eighteen selected numeric
and text cached results matched the expected values; no cached formula errors were
present. After testing, all 46 editable inputs were cleared and the blank output
matched the initial state. The original downloadable XLSX was not rewritten.

## Limits and file identity

The separate authoring-engine run tested 41 mutations. It is different from this
Google Sheets check. Microsoft Excel and Apple Numbers were not recalculated;
Google Sheets results do not establish their behavior. These checks do not prove
that an entered plan has customers, suitable licensing, equipment or local demand.

Original blank XLSX: 8,351 bytes, SHA-256
`a3e3d5ce493afb997c7ec9596b6c6c25874a782b6305a4898ba3dccf78f8a4e6`.
The research dataset remains version 1.0, with estimates and figures unchanged.
Original Lonta worksheet and this documentation: CC BY 4.0. Original survey/source
rights remain separate.
