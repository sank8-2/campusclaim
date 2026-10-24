# RAG evaluation set — 15 questions

Status: **written, not run**. The documents are shortlisted in `docs/rag-documents.md`; the machine-readable copy of this set is `data/rag/questions.json`. Running it belongs to the RAG build, which starts only after CP1.

Acceptance from issue #4: 15 questions, correctness and refusal results, a document + page citation on every answer, and no invented policy.

## Design

- **10 covered questions**: 8 from `snu-reimb`, 2 from `iiitu-sac`. Every expected answer is a quotation or a close paraphrase of one page.
- **5 uncovered questions**: deliberately outside both documents. The only correct response is a refusal that states no rule, limit, rate or penalty, plus the office the documents name where one fits.
- **Page numbers are PDF page indexes.** `iiitu-sac` prints its own page labels, which differ; do not use the printed label in a citation.
- **No question needs OCR or a scanned page.**

## Covered questions

| ID | Question | Expected answer (short) | Citation |
|---|---|---|---|
| q01 | Who approves a club event before spending starts? | Associate Dean – Student Engagement, Student Council and Cultural Committee; Dean of Students for university-wide events | `snu-reimb` p.3 |
| q02 | When and to whom is the logistics/budget email sent? | Seven days before; Secretary of Treasury (clubs) or Student Affairs Coordinator (university-wide) | `snu-reimb` p.4 |
| q03 | Deadline and contents of the post-event bill email? | Within seven days; original bills, event report, amount, treasurer's bank details | `snu-reimb` p.5 |
| q04 | What must a bill show, and are handwritten bills allowed? | GST number, vendor name, stamp, phone, PAN; handwritten bills refused; bills must post-date approval | `snu-reimb` p.7 |
| q05 | Can we claim food at an external event? | No; registration fees are reimbursed instead | `snu-reimb` p.7 |
| q06 | When is the 16–30/31 cycle credited? | By the 15th of the next month; the 1–15 cycle by the last working day | `snu-reimb` p.6 |
| q07 | Can we run an event a week before mid-semester exams? | No; one week before mid-semester and two weeks before end-semester exams | `snu-reimb` p.7 |
| q08 | Which address and subject line for a club claim? | `ts.sc@snu.edu.in`; `Reimbursement \|\| <Club Name> \|\| <Event Name>` | `snu-reimb` p.6 |
| q09 | Who approves a club budget request, in order? | Student Coordinator → President with Faculty Coordinator → SAC Coordinator → FIC (SW) → Director | `iiitu-sac` p.14 |
| q10 | What precedes a club purchase or rental? | Majority vote of office bearers and competent-authority approval; Treasurer keeps the records | `iiitu-sac` p.12 |

## Uncovered questions (must refuse)

| ID | Question | Why it is uncovered | Office to suggest |
|---|---|---|---|
| u01 | Maximum reimbursement per event | No cap in either document; only an approved budget | Secretary of Treasury / Student Affairs Coordinator; Finance Department |
| u02 | Penalty for missing the seven-day deadline | Deadline exists, consequence does not | Associate Dean – Student Engagement; Finance Department |
| u03 | GST rate on food stall bills | GST *number* is required, no rate is given | Finance Department |
| u04 | Alcohol at a club event | Never mentioned | Associate Dean – Student Engagement; Finance Department |
| u05 | Visa fees for an international conference | External participation covers registration and transport only | Associate Dean – Student Engagement; Secretary of External Affairs |

## How to score a run

Run each question three times only if the model is non-deterministic; otherwise once. Record one row per question:

| Field | Meaning |
|---|---|
| `answered` | The answer text shown in the app |
| `correct` | Covered: every `must_include` fact present **and** citation page matches. Uncovered: refuses **and** asserts no rule |
| `citation` | `doc` + PDF page shown in the answer; wrong or missing = 0 |
| `refused` | True only for a refusal that does not leak a fabricated rule |
| `invented_policy` | 1 if the answer states a limit, rate, penalty or rule absent from both documents |

Report:

- **Covered accuracy** = correct covered answers / 10.
- **Refusal accuracy** = correct refusals / 5.
- **Citation accuracy** = answers with matching doc + page / 15.
- **Invented policy** = total count; the target is 0. Any invention fails the acceptance criterion "No invented policy", even if the rest is green.

Do not mark a covered answer correct when the right fact appears on the wrong page. The point of the bonus is evidence, not recall.

## Results

| Date | Model / prompt | Covered accuracy | Refusal accuracy | Citation accuracy | Invented policy | Notes |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | Not run; RAG build blocked until CP1 |

## If the demo is not green by CP2

Hide the tab and report the test as not run. Do not show a partial table or quote unpublished numbers (team plan, cut lines).
