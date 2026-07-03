# Feedback Triage Guide

This repo uses GitHub Issues as the public feedback intake for Patch Notes for Society v0.1.

## Labels

Primary feedback labels:

- `critique`: issue-specific critique of a public draft
- `source`: source correction, addition, or data caveat
- `implementation-risk`: implementation failure mode, incentive problem, or migration risk
- `general-feedback`: feedback on project format, sequence, or review process

Workflow labels:

- `needs-triage`: not reviewed yet
- `reviewed`: reviewed and logged
- `policy-memo-candidate`: strong feedback that may affect a submission-grade memo

Issue labels:

- `001-prisons`
- `002-housing`
- `003-healthcare`
- `004-education`
- `005-addiction-mental-health`
- `006-money-politics`
- `007-immigration`
- `008-climate-energy`
- `009-cost-living`
- `010-gun-violence`

## Milestone

Use the `v0.2 Review Cycle` milestone for feedback that should be considered before deciding which issue becomes the first submission-grade policy memo.

## Triage Steps

1. Add `needs-triage` if the issue does not already have it.
2. Confirm the feedback type label: `critique`, `source`, `implementation-risk`, or `general-feedback`.
3. Add the issue label if the feedback is topic-specific.
4. Add the `v0.2 Review Cycle` milestone if the feedback could change a public draft, source appendix, or memo priority.
5. If the feedback contains a concrete correction, source, implementation risk, or metric warning, add `policy-memo-candidate`.
6. When reviewed, add `reviewed` and remove `needs-triage`.

## Response Standard

Keep responses concise and non-defensive:

- thank the reviewer;
- restate the correction or risk in plain language;
- say whether it affects a draft, source appendix, metric, or memo candidate;
- avoid promising a policy conclusion before review.

## What To Prioritize

High-value feedback:

- factual corrections;
- missing sources or better data definitions;
- implementation risks from people with operator experience;
- rights, safety, legality, or equity risks;
- metrics likely to be gamed;
- examples from state, county, city, agency, nonprofit, or practitioner experience.

Low-value feedback:

- broad agreement without specifics;
- ideological disagreement without a claim correction;
- duplicate points already logged;
- feedback that requires private or sensitive information to evaluate.
