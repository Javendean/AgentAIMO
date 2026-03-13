---
name: schema-miner
description: >
  Activated when extracting reusable problem-solving patterns from solved problems.
  Requires data from Phases 1-3.
---

# Schema Miner Skill

## What is a schema
A reusable pattern: trigger conditions, required ingredients,
transformation steps, verification criteria.

## Anti-Overfitting Rules
- Never mine from fewer than 10 solutions
- Always validate on held-out problems (minimum 5)
- If schema only helps training problems, discard it
