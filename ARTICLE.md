# Ask-vs-Assume: Calibration of Self-Reported Confidence in Agentic Tool Use

**Abstract.** Across 60 paired ambiguous/clear tasks spanning coding, everyday
planning, and customer support, a current agentic model's self-reported
confidence is not merely uncalibrated but *inversely* related to correctness
in the region that matters most: the model was right 100% of the time when
it self-reported confidence below 40, and only 60–71% of the time when it
self-reported confidence above 80 (overall Expected Calibration Error =
0.633; AUROC for confidence predicting "should have asked" = 0.622,
rising to 0.845 in the coding domain and falling to 0.353 — worse than
chance — in customer support).

---

## 1. Introduction

Agentic systems increasingly act on underspecified instructions rather than
answering questions. When an agent is uncertain, it has two options: ask a
clarifying question, or proceed on an assumption. The second option is
efficient but silently fails when the assumption is wrong — and unlike a
chat assistant giving a bad answer, an agent with tool access can take a
real, sometimes irreversible action based on that wrong assumption (booking
the wrong flight, cancelling the wrong order, deploying to the wrong
environment).

This makes a model's *self-reported confidence* operationally important: if
an agent's stated confidence reliably tracks whether it actually understood
the task, a deployment can gate on it (e.g., "only auto-execute above
confidence X, otherwise ask"). If confidence is poorly calibrated, that gate
is unsafe regardless of how it's set.

Prior work on agentic tool use largely measures *task success* — does the
agent complete the task correctly — often within a single domain (e.g.,
coding benchmarks). Comparatively little work asks the calibration
question directly: does the agent *know* when it's guessing, and does that
self-knowledge transfer across domains? This is the gap we target.

**Contribution.** We introduce a small, reusable benchmark — 60 paired
tasks (ambiguous / fully-specified) across three domains: coding
instructions, everyday task planning, and customer-support-style requests —
each with a gold clarifying question and a defined "reasonable assumption."
We evaluate a current agentic model (Gemini Flash Lite) end-to-end, measure
Expected Calibration Error (ECE) and AUROC (does confidence predict whether
asking would have helped), and release the dataset and harness for others
to run additional models through — the intended and natural next step for
this line of work.

---

## 2. Method

### 2.1 Dataset construction

60 pairs (120 prompts total), 20 per domain:

- **Coding instructions** — short dev-agent tasks (e.g., "add retry logic
  to the API call") paired with a fully-specified version.
- **Everyday task planning** — scheduling, bookings, reminders, errands.
- **Customer-support-style requests** — refunds, order changes, account
  actions, framed as requests to a support agent with tool access.

For each ambiguous item we hand-defined:
- the **gold clarifying question** — the single best question to ask;
- the **reasonable assumption** — the most defensible default, where one
  exists;
- an **assumption-is-safe** flag — whether *any* reasonable default could
  satisfy the user (e.g., "add milk to my grocery list" — quantity is
  guessable) versus tasks where guessing is unsafe regardless of which
  specific assumption is chosen (e.g., "cancel my order" — which order is
  not guessable, and cancelling the wrong one is a real cost).

This flag operationalizes "would asking have helped": it is `True` (asking
would *not* materially change the outcome) for low-stakes/guessable slots,
and `False` (asking *would* help) for genuinely unrecoverable ambiguity.
41 of 60 pairs (68%) are flagged unsafe-to-assume — most everyday agentic
requests, once you actually enumerate them, turn out to hinge on
information a model cannot guess (which order, which date, which account).

### 2.2 Model evaluated

**Gemini Flash Lite** (`gemini-flash-lite-latest`, Google), run July–August
2026 via the Generative Language API. This is a first pass on a single
model; the harness and dataset are released specifically so the comparison
across models — the more interesting question — can be completed as a
follow-up (see Limitations).

### 2.3 Elicitation protocol

The model receives a fixed system prompt instructing it to decide, per
task, whether to ask a clarifying question or proceed on an assumption, and
to self-report confidence (0–100) that it has correctly understood what the
user needs — elicited in the same turn as the action, not after the fact,
to avoid post-hoc rationalization. Full prompt in `harness.py`.

### 2.4 Grading

Each of the 120 responses was graded against the gold labels using a fixed
rule:

- **Clear tasks** (60/60): correct if the response is a reasonable,
  non-hallucinated attempt — all 60 were substantive, on-topic attempts on
  inspection, so accuracy on this leg is a sanity check rather than a
  finding (100%, as expected).
- **Ambiguous, model asked** (48/60 — see Results): graded correct, since
  asking on a genuinely ambiguous task cannot itself be the wrong move.
- **Ambiguous, model assumed** (12/60): graded correct only if the stated
  assumption matched the gold reasonable assumption *and* the task was
  flagged assumption-is-safe. On the 3 cases where the model assumed
  despite an unsafe-to-assume task, it was graded incorrect regardless of
  how plausible the specific guess was. On the 9 cases where assuming was
  defensible in principle, each was read individually against the gold
  assumption (see `gemini_graded.json` for full transcripts); 6 matched the
  gold assumption's substance, 3 did not — notably, two of those three
  missed the *specific* axis of ambiguity entirely (e.g., assuming a
  frontend framework when the actual ambiguity was about persistence
  mechanism; assuming a different test framework/language than the one
  implied) rather than landing on a merely-suboptimal-but-related default.

### 2.5 Metrics

- **ECE** (10-bin, ambiguous tasks only): mean absolute gap between binned
  confidence and empirical accuracy, weighted by bin size.
- **AUROC**: does (100 − confidence) rank-separate unsafe-to-assume tasks
  from safe-to-assume ones — i.e., does the model's own uncertainty predict
  when asking was actually necessary, independent of what it chose to do.

---

## 3. Results

### 3.1 Overall calibration

| Model | ECE (ambiguous) | AUROC | Ask rate | Assume rate | Accuracy (ambiguous) | Accuracy (clear) | n |
|---|---|---|---|---|---|---|---|
| Gemini Flash Lite | **0.633** | **0.622** | 80% | 20% | 90% | 100% | 60 |

The high task accuracy (90% on ambiguous tasks) initially looks
reassuring, but is largely a byproduct of a high ask rate (80%) on a
dataset where asking is very often the correct move (68% of pairs are
unsafe-to-assume). The calibration numbers tell a different story.

### 3.2 Reliability diagram (ambiguous tasks)

| Confidence bin | n | Mean stated confidence | Empirical accuracy |
|---|---|---|---|
| 0–10 | 6 | 0.0% | **100%** |
| 10–20 | 24 | 20.0% | **100%** |
| 20–30 | 2 | 30.0% | 100% |
| 30–40 | 11 | 40.0% | 100% |
| 80–90 | 7 | 90.0% | **71.4%** |
| 90–100 | 10 | 95.0% | **60.0%** |

(No responses fell in the 40–80 range — the model's confidence was
strongly bimodal: low when it asked, high when it assumed.)

This is the central finding: confidence and accuracy move in **opposite
directions**. Every single low-confidence response (0–40, n=43) was
graded correct. Every high-confidence response (80–100, n=17) had a real
chance of being wrong — accuracy drops to 60% in the top bin. This is not
subtle miscalibration around a diagonal; it is a near-total inversion,
because low stated confidence is what the model reports right before
asking (which this dataset is constructed such that asking is usually
right), and high stated confidence is what it reports right before
assuming (which is where the actual failures concentrate).

### 3.3 By domain

| Domain | ECE | AUROC | Ask rate | Accuracy | n |
|---|---|---|---|---|---|
| Coding | 0.718 | **0.845** | 70% | 85% | 20 |
| Planning | 0.655 | 0.583 | 85% | 95% | 20 |
| Support | 0.528 | **0.353** | 85% | 90% | 20 |

AUROC swings from 0.845 (coding — confidence is a genuinely useful,
if noisy, signal for whether a question was needed) down to 0.353 in
support — *worse than a coin flip*, meaning in that domain the model's
confidence, if anything, points the wrong way about when it should have
asked.

---

## 4. Discussion

**Where calibration breaks down.** Not randomly — it breaks down
specifically and consistently in the "assume" branch. The model's stated
confidence functions less like a genuine estimate of task understanding
and more like a marker of which action it already decided to take: ask →
report low confidence; assume → report high confidence, almost
irrespective of whether the assumption was actually well-founded. Three of
the nine judgment-call cases show this plainly — the model reported 90–95%
confidence while asserting an assumption that missed the actual axis of
ambiguity in the task (e.g., defaulting to a different test framework
entirely, or addressing an unrelated design detail instead of the
persistence question actually being asked). High stated confidence in
these cases reads as confidence in *having produced an answer*, not
confidence in *having understood the request*.

**Domain matters a lot, and not in an obvious way.** Coding — often
treated as the domain where models are most capable — has the *best*
calibration signal (AUROC 0.845) but also the *worst* ECE (0.718),
because coding tasks pulled the most high-confidence wrong assumptions
(the framework/language mismatches above). Support, meanwhile, has the
worst AUROC (0.353): confidence in that domain carries close to no
information about whether a clarifying question was actually needed. This
is a domain a deployment might reasonably expect to be "easier" to reason
about (order lookups, refunds) — the numbers suggest the opposite for
calibration specifically, even though raw accuracy in support was fine
(90%).

**Does this generalize across models?** Open question — this is a
single-model result. The released harness is built specifically so the
same 60 pairs can be run through additional models with a few lines of
code (see Release, below), which is the natural and necessary next step
before drawing conclusions about newer/larger models being better or worse
calibrated in general.

---

## 5. Limitations

- **Single model.** This run covers one model (Gemini Flash Lite). The
  original design called for 3–4 models; time and free-tier API
  constraints limited this pass to one clean, complete run. The dataset,
  harness, and grading protocol are released precisely so this is a fast
  follow-up rather than a redo.
- 60 task pairs is small; per-domain cells (n=20 ambiguous each) give wide
  confidence intervals on ECE/AUROC — the coding-vs-support AUROC gap
  (0.845 vs 0.353) is suggestive, not conclusive, at this sample size.
- Single-turn only: no multi-turn negotiation where a model could ask a
  follow-up after partial information; real deployments often allow this.
- Grading of the 9 "safe-to-assume" judgment-call cases was done by one
  reviewer reading transcripts directly rather than a separate automated
  judge model, since the automated grading pipeline (browser-based LLM
  judge) hit infrastructure issues during this run; the mechanical portion
  of the rule (48 automatic-correct, 3 automatic-incorrect, based on the
  assumption-is-safe flag and action taken) covers 51 of 60 rows and is
  fully reproducible from the released data.
- "Reasonable assumption" and "assumption-is-safe" labels were
  hand-authored by one person; they encode a particular, contestable view
  of what counts as safe to guess.

---

## 6. Release

Dataset (`tasks.json`), elicitation harness (`harness.py`), grading script
(`judge.py`), and metrics (`metrics.py`) are released as a reusable
mini-benchmark, along with this run's full graded output
(`gemini_graded.json`, `report.json`). To evaluate an additional model:
implement one function matching the signature in `harness.py`'s
`PROVIDERS` dict, run the harness, grade with `judge.py` (or the same
manual-read protocol used here), and merge into `metrics.py`.

[Repo / release link — fill in once published.]