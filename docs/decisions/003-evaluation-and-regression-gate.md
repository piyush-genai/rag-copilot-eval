# Decision 003 — Evaluation Pipeline and Regression Gate

**Date:** 2026-04-17  
**Status:** Accepted  
**Component:** `evaluation/ragas_pipeline.py`, `evaluation/deepeval_tests.py`, `evaluation/regression_gate.py`

---

## Context

RAG systems degrade silently. A new runbook upload can introduce terminology conflicts, naming collisions with existing documents, or incorrect information that the model reproduces. Without automated quality measurement, degradation is only discovered when an engineer receives a wrong answer during a live incident.

---

## Decision

**Two-layer evaluation: RAGAS for quality metrics + DeepEval for hallucination detection. Regression gate Lambda blocks deployment if any metric drops >5% from baseline.**

### RAGAS Metrics

| Metric | What It Measures | Low Score Means |
|---|---|---|
| `context_precision` | Of retrieved chunks, what fraction were relevant? | Noisy retrieval — wrong chunks are being returned |
| `context_recall` | Did retrieved chunks contain the needed information? | Right chunk was never retrieved — not in top-k |
| `faithfulness` | Is every claim in the answer supported by context? | Hallucination — model added facts not in retrieved chunks |
| `answer_relevancy` | Does the answer address the question asked? | Model answered a related but different question |

### DeepEval HallucinationMetric

Stricter than RAGAS faithfulness. Checks whether the answer contradicts the context or contains statements that cannot be derived from it. Near-zero tolerance threshold (>0.1 flags the answer) for procedural runbook queries where commands must be exact.

### Regression Gate

Lambda triggered by S3 `ObjectCreated` on the runbooks bucket. Runs RAGAS on the QA pairs most relevant to the new runbook. Compares against `evaluation/data/baseline_metrics.json`. If any metric drops >5%: publishes SNS alert, writes `BLOCKED` to SSM Parameter `/rag-copilot/deployment-status`. CI/CD pipeline checks this parameter before deploying.

---

## Why Both RAGAS and DeepEval

RAGAS faithfulness measures whether claims are supported by context. DeepEval HallucinationMetric measures whether claims contradict or cannot be derived from context. These are complementary — a claim can be "not contradicted" (passes DeepEval) but also "not explicitly supported" (fails RAGAS faithfulness). For runbooks where commands must be reproduced exactly, both checks are necessary.

---

## Why SNS + SSM Over a Database Flag

**SNS:** During a 3am incident, a text message or Slack webhook via SNS subscription is more reliable than checking a dashboard. Alert delivery is the primary concern.

**SSM Parameter:** Integrates natively with AWS CodePipeline as a built-in step — `ssm:GetParameter` requires no custom integration code. A database flag would require writing and maintaining a custom deployment gate for every CI/CD tool used.

---

## Why 5% Threshold

Tight enough to catch meaningful regressions before they affect users. Loose enough to avoid false positives from natural variance in LLM evaluation (RAGAS uses an LLM internally — scores have inherent variance of ~2-3%). A 5% drop on `context_precision` from 0.91 to 0.86 is a real signal. A 1% drop is likely noise.

---

## Alternatives Considered

| Approach | Reason Rejected |
|---|---|
| Manual evaluation only | Does not scale to 200+ runbooks. Misses regressions between manual review cycles. |
| RAGAS only | Does not catch command-level hallucinations where the model paraphrases a command. DeepEval's stricter check is necessary for procedural accuracy. |
| Cron-based evaluation | Runs on a schedule, not on new content. A bad runbook uploaded at 9am could affect queries until the next scheduled run at midnight. Event-driven is the correct trigger. |
| Block all deployments on any metric change | Too sensitive. Natural LLM evaluation variance would block deployments constantly. The 5% threshold filters noise. |

---

## Consequences

- Every new runbook upload triggers an automated quality check before it affects production retrieval
- The golden test set (`evaluation/data/golden_set.json`) must be sourced from real P1 incident queries — synthetic questions do not catch the precision drops that matter most
- Baseline metrics must be updated intentionally when a genuine improvement is made — the gate compares against the saved baseline, not the previous run
- The gate adds ~2-5 minutes to the ingestion pipeline per new runbook — acceptable for a background process
