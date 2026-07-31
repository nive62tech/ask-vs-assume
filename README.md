# Ask-vs-Assume — one-day execution plan

## Files
- `tasks.json` — 60 paired tasks (120 prompts), 3 domains, with gold clarifying
  question / reasonable assumption / assumption-is-safe flag for each.
- `harness.py` — runs any provider (Anthropic/OpenAI/Google, HTTP-based, no SDK
  lock-in) over all tasks, captures action (ASK/ASSUME), response, confidence.
- `judge.py` — LLM-judge grading of harness output against the gold labels.
- `metrics.py` — computes ECE (10-bin) and AUROC, overall + per domain, from
  one or more graded result files.
- `outputs/live_runner.html` — a browser artifact that runs the **Claude** leg
  live with zero API key (uses Claude's built-in artifact→API bridge). Open it
  as an artifact inside Claude (not as a local file — the API bridge only
  works there), hit "Run study," and it streams results + calibration plot
  in real time. Uses a 30-pair subset (10/domain) to keep runtime reasonable;
  swap in the full 60 by pasting `tasks.json` into the `TASKS` constant if
  you want the full set.
- `ARTICLE.md` — ~3 page article skeleton, every results table cell tagged
  with the exact `report.json` field it pulls from.

## Environment: Windows / VS Code / PowerShell

This project is being run in **VS Code's integrated PowerShell terminal on
Windows**. Note this everywhere commands are given — `export` (bash syntax)
does NOT work here. Use:

```powershell
$env:ANTHROPIC_API_KEY="sk-ant-..."
$env:OPENAI_API_KEY="sk-..."
$env:GOOGLE_API_KEY="..."
```

These only last the current terminal session. To persist across sessions:
`setx ANTHROPIC_API_KEY "sk-ant-..."` (then restart the terminal).

Verify a key is set: `echo $env:ANTHROPIC_API_KEY`

Venv activation on Windows PowerShell: `venv\Scripts\Activate.ps1` (not
`source venv/bin/activate`, that's bash).

## Today's sequence

**1. Get API keys (15 min)** — OpenAI and Google keys if you want the
   full 3-model comparison. Claude doesn't need one for the artifact leg.

**2. Run Claude via the artifact (10–15 min, no setup)**
   Open `live_runner.html` inside Claude (chat UI), click "Run study." Watch
   ECE/AUROC populate live. Download the JSON when done, save it into this
   repo as `results_claude_graded.json` (the artifact already grades with
   the judge internally, so this file can go straight into `metrics.py`).

**3. Smoke-test each provider locally before the full run**
   ```powershell
   pip install httpx numpy
   python harness.py --provider openai --model gpt-4o --out results_gpt4o_smoke.json --limit 5
   ```
   Check `results_gpt4o_smoke.json` — confirm `action` and `confidence`
   parsed correctly (not `null`) before spending the full budget.

**4. Run the full harness per model**
   ```powershell
   python harness.py --provider openai --model gpt-4o --out results_gpt4o.json
   python harness.py --provider google --model gemini-1.5-pro --out results_gemini.json
   ```

**5. Grade each with the judge**
   ```powershell
   python judge.py --results results_gpt4o.json --judge_provider anthropic --judge_model claude-sonnet-4-6 --out results_gpt4o_graded.json
   python judge.py --results results_gemini.json --judge_provider anthropic --judge_model claude-sonnet-4-6 --out results_gemini_graded.json
   ```
   (Judging needs an Anthropic key too, or point `--judge_provider` at
   whichever model you trust as judge — just don't use a model to judge
   itself.)

**6. Merge and compute final metrics**
   ```powershell
   python metrics.py --results results_claude_graded.json results_gpt4o_graded.json results_gemini_graded.json --out report.json
   ```

**7. Log every number into `RESULTS_LOG.md`** as soon as you get it (see
   that file) — don't wait until the end, `report.json` gets overwritten
   each time you re-run metrics.py with a different file set.

**8. Fill in `ARTICLE.md`** from `RESULTS_LOG.md` / `report.json` — every
   table is pre-labeled with the field name to pull.

**9. Release** — push `tasks.json` + the three scripts to the repo with
   this README so others can run their own models through it.

## Progress log

Track what's actually been done, in this repo, as you go:

- [ ] API keys obtained: Anthropic ☐ &nbsp; OpenAI ☐ &nbsp; Google ☐
- [ ] Claude leg run (via `live_runner.html`) → `results_claude_graded.json` saved
- [ ] GPT smoke test passed → full run → graded
- [ ] Gemini smoke test passed → full run → graded
- [ ] `report.json` generated from all graded files
- [ ] `RESULTS_LOG.md` filled in
- [ ] `ARTICLE.md` filled in

## If you're short on time
Cut to 2 models (Claude via the artifact + one other), and/or cut the task
set to the 30-pair subset already embedded in `live_runner.html` for both
legs — the pipeline and metrics are unaffected by n, just widen your
confidence intervals when discussing results.