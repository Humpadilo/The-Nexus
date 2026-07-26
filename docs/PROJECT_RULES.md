# Project Rules

This is the constitution of The Nexus. When a shortcut conflicts with one of these rules, the rule wins unless Matt explicitly changes it and records that change in [DECISIONS.md](DECISIONS.md).

## Reliability over cleverness

Prefer boring, observable, testable behavior over a clever abstraction that is difficult to operate or debug.

## AI never changes production automatically

AI may observe, explain, and recommend. Production changes require explicit human approval and a recorded, reviewable action.

## Every change must be reversible

Design changes so they can be rolled back, disabled, or replaced. Keep generated artifacts separate from active configuration until approved.

## Every recommendation must explain why

Recommendations need evidence, expected effect, uncertainty, and relevant risks. A conclusion without reasoning is not an actionable project artifact.

## Observe → Recommend → Approve → Apply

This is the default safety boundary. A future implementation step must not bypass the preceding steps without an explicit decision record.

## Prefer local control

The system must remain useful without Codex, ChatGPT, or a cloud AI provider. External services are optional extensions, not runtime foundations.

## Minimize maintenance burden

Every feature must justify its operational cost. Avoid introducing infrastructure, dependencies, or background jobs that do not materially help the household.

## Avoid feature creep

Unrelated ideas go to [PARKING_LOT.md](PARKING_LOT.md). They do not enter the current sprint by enthusiasm alone.

## Dum-Dum Protocol

When a proposed action could create a surprising or hard-to-reverse consequence, stop and state the risk in plain language before proceeding. Do not rely on the user noticing the danger after the fact.

## Hold the Fuck Up Protocol

If evidence is incomplete, permissions are unclear, or the system behavior is uncertain, pause the action and verify the assumption. A partial answer is safer than confident damage.

## The 30 Minute Rule

If a task has not produced meaningful progress after roughly 30 minutes, stop, summarize the blocker, and choose a smaller experiment or ask for direction.

## The 80% Rule

Prefer a small, working, well-understood result over a large incomplete system. Ship the reliable 80% and record the remaining 20% explicitly.

## Parking Lot rule

Ideas are not lost because they are deferred. Record them with enough context to revisit, then protect the current sprint from them.

## Every sprint must produce a working result

Each sprint should end with a usable improvement, a verified artifact, or a clearly documented decision—not only scaffolding.

## No hidden automation behavior

Background activity, scheduling, collection, and state changes must be visible in documentation and logs. The system must not surprise its operator.

## Security before convenience

Use the narrowest permissions and data access that satisfy the feature. Do not read secrets or broad configuration merely because it is convenient.

## Simplicity before novelty

New technologies and AI capabilities must solve a demonstrated problem. Familiar tools with clear failure modes are preferred.
