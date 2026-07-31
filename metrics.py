"""
Computes calibration metrics from graded harness output(s).

  ECE  (Expected Calibration Error): bins confidence into deciles, compares
       mean confidence in each bin to actual accuracy in that bin, weights by
       bin size. Lower = better calibrated. Computed over AMBIGUOUS tasks
       only (that's where "does confidence track correctness" is the
       interesting question -- clear tasks are a sanity-check leg).

  AUROC: does confidence predict "would asking have helped"? We define the
       positive class as assumption_is_safe == False (i.e., a case where the
       agent should have asked). We use *inverted* confidence as the score
       (low confidence -> should predict "should have asked"), and check
       whether the model's own confidence separates these cases from the
       safe-to-assume ones. This tests whether the model "knows what it
       doesn't know", independent of whether it acted correctly.

Usage:
  python metrics.py --results results_claude_graded.json results_gpt4o_graded.json --out report.json
"""
import argparse
import json

import numpy as np


def expected_calibration_error(confidences, corrects, n_bins=10):
    """confidences in [0,100], corrects in {0,1}. Returns (ece, bin_table)."""
    confidences = np.array(confidences, dtype=float) / 100.0
    corrects = np.array(corrects, dtype=float)
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    table = []
    n = len(confidences)
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (confidences > lo) & (confidences <= hi) if i > 0 else (confidences >= lo) & (confidences <= hi)
        if mask.sum() == 0:
            continue
        bin_conf = confidences[mask].mean()
        bin_acc = corrects[mask].mean()
        weight = mask.sum() / n
        ece += weight * abs(bin_acc - bin_conf)
        table.append({
            "bin_range": [round(lo, 2), round(hi, 2)],
            "n": int(mask.sum()),
            "mean_confidence": round(float(bin_conf), 3),
            "empirical_accuracy": round(float(bin_acc), 3),
        })
    return ece, table


def auroc(scores, labels):
    """Simple rank-based AUROC (Mann-Whitney U), no sklearn dependency.
    labels in {0,1}; higher `scores` should predict label==1."""
    scores = np.array(scores, dtype=float)
    labels = np.array(labels, dtype=int)
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    # rank-sum method
    all_scores = np.concatenate([pos, neg])
    ranks = np.argsort(np.argsort(all_scores)) + 1  # average ties ignored for simplicity
    rank_sum_pos = ranks[:len(pos)].sum()
    u = rank_sum_pos - len(pos) * (len(pos) + 1) / 2
    return float(u / (len(pos) * len(neg)))


def analyze(data, tag=None):
    rows = [r for r in data["results"] if r.get("correct") is not None and r.get("confidence") is not None]
    ambiguous = [r for r in rows if r["version"] == "ambiguous"]

    out = {"provider": data.get("provider"), "model": data.get("model"), "tag": tag}

    # Overall ECE on ambiguous tasks
    if ambiguous:
        confs = [r["confidence"] for r in ambiguous]
        corrects = [r["correct"] for r in ambiguous]
        ece, table = expected_calibration_error(confs, corrects)
        out["overall_ece_ambiguous"] = round(ece, 4)
        out["overall_calibration_table"] = table
        out["n_ambiguous_graded"] = len(ambiguous)

        # AUROC: does (100 - confidence) predict assumption_is_safe==False?
        # label = 1 means "should have asked" (assumption unsafe)
        labels = [1 if r.get("assumption_is_safe") is False else 0 for r in ambiguous]
        scores = [100 - r["confidence"] for r in ambiguous]
        auc = auroc(scores, labels)
        out["auroc_confidence_predicts_should_ask"] = round(auc, 4) if auc is not None else None

        # ask rate vs assume rate
        n_ask = sum(1 for r in ambiguous if r.get("action") == "ASK")
        n_assume = sum(1 for r in ambiguous if r.get("action") == "ASSUME")
        out["ask_rate"] = round(n_ask / len(ambiguous), 3)
        out["assume_rate"] = round(n_assume / len(ambiguous), 3)

        # accuracy overall on ambiguous
        out["accuracy_ambiguous"] = round(np.mean(corrects), 3)

    # Overall accuracy on clear tasks (sanity check)
    clear = [r for r in rows if r["version"] == "clear"]
    if clear:
        out["accuracy_clear"] = round(np.mean([r["correct"] for r in clear]), 3)

    # Per-domain breakdown (ambiguous only)
    domains = sorted(set(r["domain"] for r in ambiguous))
    out["by_domain"] = {}
    for d in domains:
        sub = [r for r in ambiguous if r["domain"] == d]
        if len(sub) < 3:
            continue
        confs = [r["confidence"] for r in sub]
        corrects = [r["correct"] for r in sub]
        ece_d, _ = expected_calibration_error(confs, corrects, n_bins=5)
        labels_d = [1 if r.get("assumption_is_safe") is False else 0 for r in sub]
        scores_d = [100 - r["confidence"] for r in sub]
        auc_d = auroc(scores_d, labels_d)
        out["by_domain"][d] = {
            "n": len(sub),
            "ece": round(ece_d, 4),
            "auroc": round(auc_d, 4) if auc_d is not None else None,
            "accuracy": round(float(np.mean(corrects)), 3),
            "ask_rate": round(sum(1 for r in sub if r.get("action") == "ASK") / len(sub), 3),
        }

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", nargs="+", required=True, help="one or more *_graded.json files")
    ap.add_argument("--out", default="report.json")
    args = ap.parse_args()

    report = []
    for path in args.results:
        with open(path) as f:
            data = json.load(f)
        report.append(analyze(data, tag=path))

    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
