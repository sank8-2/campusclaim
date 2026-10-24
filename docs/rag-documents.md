# RAG document shortlist

Status: **shortlist + text-based check done (24 October 2026)**. This is the pre-CP1 part of [#4](https://github.com/sank8-2/campusclaim/issues/4). The RAG build itself waits for CP1, as the issue and `docs/team-plan.md` require.

The team has no named campus document set, so these are **proxy documents from two public Indian institutions**. Every answer in the demo must therefore name the document and page, and the deck must say the policy is a proxy. Swap in the college's own PDFs if the team gets them before CP2.

## Selected documents

| ID | Document | Institution | Public URL | Pages | Extractable characters | Verdict |
|---|---|---|---|---|---|---|
| `snu-reimb` | Policy for Reimbursement of Expenditure by Students on University Events (V1, released 10.01.24) | Shiv Nadar Institution of Eminence | <https://snu.edu.in/site/assets/files/16669/reimburesement_policy_for_students.pdf> | 8 | 11,106 | Text-based |
| `iiitu-sac` | Student Activity Council Policy | Indian Institute of Information Technology Una | <https://iiitu.ac.in/assets/IIITUna-Student-Activity-Council-Policy-URsaLXRv.pdf> | 15 | 25,479 | Text-based (cover and final page have almost no text) |

Checksums of the copies that were checked:

```
4cb39f569273603de5d09b6ae86c74e30fb51323fe2e7311349838a8b84f2b19  snu_student_event_reimbursement_policy.pdf
66e8dd7db83cb876f798eb3c25553002f2c9cde5573bc47c95e94ac8a0acdca0  iiituna_student_activity_council_policy.pdf
```

## Why these two

- `snu-reimb` is the closest match to CampusClaim's workflow: event approval, vendor purchase orders, bill formats, GST and PAN details, submission deadlines, reimbursement cycles, external participation, and refund rules. Most of the 15-question test can come from this one document.
- `iiitu-sac` adds the club-governance side: who raises and approves a budget, where sponsorship money sits, and what the Treasurer and Dean (Student Welfare) may approve. It stops the demo from treating reimbursement as a purely clerical step.
- Both are official, publicly reachable, and text-based, so page-level citations can be extracted without OCR.

Documents considered and dropped:

| Candidate | Why dropped |
|---|---|
| IIT Kanpur Students' Gymkhana purchase guidelines and constitution | Host `www.iitk.ac.in` was unreachable from the build machine (connection timeout), so the text-based check could not be run. |
| IIT Ropar Student Affairs activity forms | The published URL returns 404. |
| IISc Travelling Allowance rules (2020) | Two content pages (10–11) contain no extractable text and pages 4–6 are OCR of a Government of India memorandum; fails the "text-based, not scans" test. |
| Shiv Nadar Student Handbook | Repeats the reimbursement policy inside a much larger handbook; the standalone policy is a cleaner citation target. |

## Text-based check

`scripts/check_rag_docs.py` opens each PDF with `pypdf`, counts extractable characters per page, and flags pages below 200 characters:

```bash
python -m pip install pypdf
python scripts/check_rag_docs.py
```

Result on the checked copies:

```
snu_student_event_reimbursement_policy.pdf
  pages: 8, characters: 11106
  per page: p1=524 p2=333 p3=1920 p4=1985 p5=1983 p6=1714 p7=2028 p8=619
  verdict: TEXT-BASED

iiituna_student_activity_council_policy.pdf
  pages: 15, characters: 25479
  per page: p1=138 p2=1127 p3=2258 p4=2013 p5=2018 p6=1996 p7=2206 p8=1956 p9=1961 p10=2441 p11=2063 p12=1946 p13=2219 p14=1092 p15=45
  low-text pages: [1, 15]
  verdict: TEXT-BASED (cover/blank pages skipped)
```

`iiitu-sac` page 1 is the title page and page 15 is blank. Pages 2–14 carry the policy text, so the document is usable. Neither document needs OCR.

## Page map for citations

Citations in the question set use **PDF page numbers**, not the printed page labels. `iiitu-sac` prints its own numbers in the footer and they drift from the PDF index (for example PDF page 14 is printed page 9).

`snu-reimb`:

| PDF page | Content |
|---|---|
| 3 | Objective; event approval authorities and process |
| 4 | Vendor entry, purchase requisition/order; bills handed to Associate Dean / Student Affairs Coordinator; logistics and budget email seven days prior |
| 5 | Logistics table; external participants 15 days prior; bill submission within seven days; original bills and event report |
| 6 | Reimbursement cycles; email format, recipients and subject line; external participation approval |
| 7 | External registration fees; transport; no food reimbursement externally; GST/PAN bill rules; approval-date rule; exam blackout windows |
| 8 | Financial indemnity, financial review, revenue disclosure, fraudulent GST bills |

`iiitu-sac`:

| PDF page | Content |
|---|---|
| 3 | Societies; annual event calendar and approved budget |
| 11 | Dean/FIC (SW) duties: supervise finances; approve purchases and cash advances |
| 12 | Treasurer duties: records, majority vote before purchase, competent-authority approval |
| 13 | Organising major events; committees |
| 14 | SAC budget, sponsorship, account, and the approval hierarchy up to the Director |

## Licence and storage

- `snu-reimb` carries a restrictive notice ("exclusive use of Shiv Nadar IoE ... no part may be copied, reproduced, stored in any retrieval system ... without prior written permission"). Do **not** commit the PDF or a full extracted text to the repo. Fetch it at runtime, quote short passages for citation, and keep the URL in the notebook.
- `iiitu-sac` has no such notice, but the same handling keeps the repo small and the sources unambiguous.
- `data/rag/source/` and `data/rag/text/` are therefore git-ignored. `docs/rag-documents.md` and `data/rag/questions.json` are the committed artifacts.

## Risks and fallbacks

| Risk | Fallback |
|---|---|
| A public URL moves or is taken down | Re-download before CP2; if it fails, replace the document and re-run the 15-question test. Do not cite a document the demo cannot show. |
| A judge asks whose policy this is | Say plainly that these are proxy documents from two public Indian institutions and that citations are to the PDF page. Do not imply they are the team's college rules. |
| `snu-reimb` is silent on a question | Refuse and name the office the document does name (Secretary of Treasury, Student Affairs Coordinator, Associate Dean – Student Engagement, Finance Department). |
| RAG not green by CP2 | Hide the tab; the bonus does not run (issue #4 and the cut-line table both say this). |

## Not done here

The second notebook, retrieval index, prompt, and refusal logic are **not** built yet. They start only after CP1 (baseline + fine-tuned comparison + app working) is green.
