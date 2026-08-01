# AGENTS.md

# The Nexus

## Mission

The Nexus is an AI-assisted Home Assistant intelligence platform.

Its purpose is not merely to automate a home.

Its purpose is to understand the home, observe the home, recommend improvements, and safely assist the user in evolving the home's behavior over time.

The system must remain modular, maintainable, observable, and safe.

---

# Core Philosophy

Observation before automation.

Evidence before assumptions.

Recommendations before implementation.

Reliability before complexity.

Local control whenever practical.

The system should help the user understand the house rather than hiding behavior.

---

# Constitutional Offices

## The Archivist

Responsible for collecting information.

Produces reports.

Maintains historical observations.

Never modifies Home Assistant.

Read-only.

---

## The Curator

Produces intelligence packages.

Creates comprehensive snapshots of the smart home.

Packages information for AI analysis.

Read-only.

---

## The Raven

Investigates problems.

Produces diagnoses.

Never repairs.

---

## The Engineer

Designs proposed repairs.

Produces implementation plans.

Never applies changes automatically.

---

## The Watcher

Continuously observes system state.

Detects changes.

Schedules observations.

---

## Future Offices

Oracle

Speaker

Steward

Additional offices may be introduced without restructuring the architecture.

---

# Design Principles

Prefer modular services.

Avoid giant files.

Keep responsibilities separated.

Each office owns one responsibility.

Prefer extension over modification.

Do not duplicate logic.

Favor readability over cleverness.

---

# Home Assistant Rules

Never perform destructive actions without explicit approval.

Never modify entities during observation.

Prefer official Home Assistant APIs.

Use registries instead of hardcoded entity names whenever possible.

Automatically discover integrations whenever practical.

Gracefully handle unavailable integrations.

---

# Reports

Reports should be designed for both humans and AI.

Whenever practical include:

summary

metadata

relationships

timestamps

errors

capabilities

Every report should remain useful even if future integrations are added.

---

# AI Philosophy

The primary consumer of Curator reports is ChatGPT.

Reports should prioritize understanding over compactness.

When uncertain whether information may be useful in the future, include it.

Automatically redact secrets, passwords, API keys, and tokens.

---

# Maintenance Mode

The Curator infrastructure is operational. Future development is driven by findings from Curator intelligence reports rather than assumptions.

Do not expand functionality, redesign architecture, or add speculative capabilities without a verified Curator finding, an observed production need, or an explicit user request.

Treat Curator reports as the primary evidence source for prioritization, diagnosis, and future changes. Preserve the read-only collection path and avoid changing Home Assistant while gathering evidence.

---

# Engineering Philosophy

The Producer defines:

goals

constraints

desired behavior

Codex determines implementation.

Engineering improvements are encouraged provided they remain within the architectural boundaries.

---

# Success

The long-term vision is an intelligent home that continuously improves through observation, historical analysis, and human approval.

The house should become increasingly understandable over time rather than increasingly complicated.
