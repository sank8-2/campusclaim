# Theme selection discussion

## Decision and motivation

Build **CampusClaim**, a receipt-to-reimbursement assistant for student clubs and campus events. Select **Theme 3B: Receipt Information Extraction** as the primary submission, with components from **Theme 2A: Campus Regulations Assistant** and **Theme 1: Open Model Evaluation**.

The project direction came from two preferences: build an idea that spans all three themes, and choose an ambitious theme that other teams may hesitate to attempt. Vision fine-tuning offers that technical challenge. We do not have participant selection data, so fewer competing teams is an expectation, not an established fact.

The original repository asks each team to choose one theme, with a presentation and live demonstration. The plan therefore treats 3B as the required core and the other themes as supporting extensions. This is our proposed project scope, not a claim that the organisers require a combined submission.

## Alternatives considered

| Idea | Connection across the themes | Tradeoff discussed |
|---|---|---|
| Multilingual Campus Assistant | Evaluate models; retrieve official college regulations; fine-tune English/Hindi or Kannada code-mixed conversion using IndicCMix. | The most straightforward integration and a manageable starting point, but less focused on the challenging vision workflow we wanted. |
| Regional-Language Open-Source Contribution Mentor | Evaluate models; retrieve a real project's contributor documentation; fine-tune regional-language conversion. | Strong connection to Hacktoberfest, with extra care needed to preserve commands, filenames, and code during language conversion. |
| CampusClaim | Evaluate models; retrieve official campus reimbursement rules; fine-tune receipt image extraction using SROIE. | Selected for its connected user workflow, visual demonstration, and measurable extraction task; requires more work on GPU training and image handling. |

## User problem and proposed experience

Student event organisers must copy details from receipts and find the college rules governing reimbursement. CampusClaim brings those tasks into one workflow:

1. Upload one receipt image.
2. Extract `company`, `date`, `address`, and `total` into an editable form.
3. Ask a reimbursement question, such as “What supporting documents do I need to claim this printing expense?”
4. Retrieve relevant passages from official college documents.
5. Explain the requirements with document and page citations, and identify missing information.
6. Produce a claim summary using the user-corrected receipt fields and cited requirements.

Receipt extraction supplies the transaction details. Retrieval supplies the rules. Evaluation measures how reliably each component works. The assistant supports claim preparation; approval remains with the college's authorised reviewers.

## Mapping to the three themes

### Theme 3B: primary deliverable

- Use the ICDAR 2019 SROIE dataset (`jsdnrs/ICDAR2019-SROIE`). The problem statement lists 626 training and 361 test receipt images.
- Fine-tune image-capable Gemma with LoRA using Unsloth's vision workflow on a Colab T4 GPU, following the supplied adaptation guidance.
- Generate JSON containing the four required fields: `company`, `date`, `address`, and `total`.
- Evaluate the plain and fine-tuned models on the same held-out test examples with the same instructions and scoring method.
- Report field-level accuracy and example successes and failures. Document the dataset split and training settings.
- Build and demonstrate a working receipt-upload application.

The starter notebook's IT support ticket classification task is a teaching example. It must be replaced with receipt data, image inference, field scoring, and an image-upload interface.

### Theme 2A: campus policy retrieval

- Collect at least two publicly available official college documents covering finance, student activities, reimbursement, or related regulations.
- Answer only from the retrieved evidence, cite document names and page numbers, and show the retrieved passages.
- Decline unsupported questions and suggest an appropriate college contact when the official sources provide that information.
- Evaluate on at least 15 questions with expected answers, reporting correctness and failure cases.
- Explain chunking, retrieval settings, and other pipeline choices.

The supplied RAG starter supports text-based PDFs. Document collection and any additional format support are implementation work. Multiple document support is necessary for our campus use case even though it also appears in the general bonus list.

### Theme 1: structured model evaluation

- Compare at least four open-weight models, including at least one from each of the two specified platforms: Groq Playground and Google AI Studio.
- Design at least 25 prompts spanning five categories: extraction-output validation, arithmetic, policy reasoning, instruction following, and unsupported-question handling.
- Use identical prompts, system instructions, and temperature settings, with a fresh conversation for each prompt.
- Have at least two people independently score each response before agreeing a final score.
- Present model fact sheets, category scores, failure patterns, and recommendations.

For cross-model comparison, use identical text representations of receipt data when some models do not support images. This tests downstream reasoning and validation, not image extraction. Keep the plain-versus-fine-tuned vision benchmark separate so that the reported conclusions match the tasks actually tested.

## Minimum scope and build order

1. Establish the plain-model receipt extraction baseline and field scoring.
2. Fine-tune, compare on held-out receipts, and save the adapters.
3. Build an image-upload interface with editable extracted fields and a comparison view.
4. Add retrieval over official campus policy documents, with citations and refusals.
5. Combine corrected receipt details and cited requirements into a claim summary.
6. Complete the broader model comparison and prepare the presentation.

If time is constrained, complete the required 3B deliverables first. The selected optional extension is **line-item extraction**, explicitly listed as a 3B bonus. Detecting individual purchases could later help connect receipt contents to expense categories, but this is outside the initial four-field extraction scope.

## Risks and evaluation boundaries

- **Domain shift:** SROIE results do not establish accuracy on Indian campus receipts. Add a small, separately reported local test set; keep evaluation examples out of training.
- **Incomplete evidence:** receipts may omit prior approval, event purpose, expense category, or other information required by policy. Ask for missing information before drawing conclusions.
- **Policy coverage:** collect real official documents before promising coverage. When documents are silent or conflicting, show that uncertainty and the supporting passages.
- **Training limits:** free GPU availability and runtime limits constrain experiments. Save adapters and record settings so runs can be reproduced.
- **Uncertain gains:** fine-tuning may improve some fields and worsen others. Report the actual results, including failures, rather than assuming an improvement.

## Showcase plan

Upload a held-out receipt, show plain and fine-tuned extraction side by side, correct any errors, and ask a reimbursement question. Display the policy answer and its sources. Finish with an unsupported question to demonstrate refusal, then show the extraction metrics and broader model scorecard.

## Source problem statements

These requirements were reviewed on 24 October 2026. Model names, availability, and runtime compatibility should be checked when implementation begins; the starter notebooks have been read, not executed as part of this discussion.

- [Hack Day overview](https://github.com/mithun-srinivas/HacktoberFest-HackDay/blob/main/PROBLEM_STATEMENTS.md)
- [Theme 1: Open Model Evaluation](https://github.com/mithun-srinivas/HacktoberFest-HackDay/blob/main/problem-statements/01_model_evaluation.md)
- [Theme 2: RAG Application](https://github.com/mithun-srinivas/HacktoberFest-HackDay/blob/main/problem-statements/02_rag_application.md)
- [Theme 3: Fine-Tuning Gemma](https://github.com/mithun-srinivas/HacktoberFest-HackDay/blob/main/problem-statements/03_fine_tuning.md)
