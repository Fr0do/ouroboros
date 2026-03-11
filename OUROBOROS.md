# OUROBOROS

> The serpent eats its own tail: each project feeds the next, and the meta-process improves itself.

This is not a project plan. It is a set of beliefs about how research should be conducted when the researcher and the tools are in continuous dialogue.

---

## 1. The loop closes

Every artifact produced — code, paper, infrastructure, tooling — must eventually improve the process that created it. A training pipeline that doesn't inform the next training pipeline was a dead end, not research. A governance protocol that never revises itself is bureaucracy.

## 2. Autonomy with accountability

Agents — human or otherwise — operate with maximum freedom and minimum supervision. But every action is logged, every decision is traceable, every commit tells a story. Freedom without a trail is chaos.

## 3. Minimalism

One source of truth per fact. One file per concern. Delete over deprecate. If something exists in two places, one of them is wrong and both are suspect. Complexity is debt with compounding interest.

## 4. Atomic updates

Every change is self-contained and non-breaking. A commit either works or it doesn't exist. A feature is either complete or it's behind an issue. No half-states, no "will fix later" comments left to rot.

## 5. Reproducibility

Any result must be recoverable from three things: the config, the seed, and the commit hash. If a result cannot be reproduced, it is an anecdote, not a finding.

## 6. Cross-pollination

Projects are not silos. An insight from spectral optimization should inform black-box search. A benchmark methodology should transfer across domains. The shared workspace exists so ideas can bleed between directories.

## 7. Minimal overhead

Every tool must justify its existence by saving more time than it costs. Telegram for control, GitHub for memory, RTK for efficiency. If a process requires a meeting, the process is wrong.

## 8. Issues before code

The impulse to write code before thinking is a form of procrastination. An issue is a commitment to a direction. A commit without an issue is a change without a reason.

## 9. Plan in the large, implement in the small

Architecture deserves the strongest reasoning. Implementation deserves the fastest hands. These are different skills and often different models. Never use a sledgehammer to type.

## 10. Ship or kill

A project that hasn't shipped in three months needs either a deadline or a funeral. Research that never leaves the cluster is a hobby. Papers that never leave the overleaf are drafts. Be honest about which is which.

---

*For project registry and infrastructure, see [PROJECTS.md](PROJECTS.md).*
*For version history, see [CHANGELOG.md](CHANGELOG.md).*
*For development conventions, see [CLAUDE.md](CLAUDE.md).*
