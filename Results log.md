# Results Log

Fill this in as soon as each run finishes — don't wait for everything to be
done. `report.json` gets overwritten each time `metrics.py` is re-run, so
this file is the durable copy of numbers as you get them. Copy straight
into `ARTICLE.md` tables when writing.

Last updated: _(date/time)_

---

## Run metadata

| Model | Provider | Exact model string | Date run | n pairs run | Notes |
|---|---|---|---|---|---|
| Claude | anthropic | claude-sonnet-4-6 | | | via live_runner.html, n=30 subset unless full 60 used |
| GPT | openai | | | | |
| Gemini | google | | | | |

---

## Overall calibration (ambiguous tasks)

| Model | ECE | AUROC | Ask rate | Assume rate | Accuracy (ambiguous) | Accuracy (clear) | n graded |
|---|---|---|---|---|---|---|---|
| Claude | | | | | | | |
| GPT | | | | | | | |
| Gemini | | | | | | | |

*(field names in report.json: overall_ece_ambiguous, auroc_confidence_predicts_should_ask, ask_rate, assume_rate, accuracy_ambiguous, accuracy_clear, n_ambiguous_graded)*

---

## By domain

### Coding

| Model | ECE | AUROC | Ask rate | Accuracy | n |
|---|---|---|---|---|---|
| Claude | | | | | |
| GPT | | | | | |
| Gemini | | | | | |

### Planning

| Model | ECE | AUROC | Ask rate | Accuracy | n |
|---|---|---|---|---|---|
| Claude | | | | | |
| GPT | | | | | |
| Gemini | | | | | |

### Support

| Model | ECE | AUROC | Ask rate | Accuracy | n |
|---|---|---|---|---|---|
| Claude | | | | | |
| GPT | | | | | |
| Gemini | | | | | |

*(field names: by_domain.<domain>.ece / .auroc / .ask_rate / .accuracy / .n)*

---

## Reliability diagram raw data (optional, for plotting)

Paste `overall_calibration_table` per model here if you want to build a
proper reliability diagram later (bin range / n / mean confidence /
empirical accuracy per bin).

### Claude
```
(paste array here)
```

### GPT
```
(paste array here)
```

### Gemini
```
(paste array here)
```

---

## Observations while running (qualitative notes)

Jot anything odd here as you see it — e.g. a model refusing to commit to a
confidence number, unparseable outputs, a domain where one model always
assumes vs always asks. These are useful for the Discussion section and
easy to forget by the time you write it up.

-
-
-