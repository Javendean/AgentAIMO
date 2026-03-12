---
description: Force agent to use GitNexus for structural awareness
activation: always
---

# GitNexus Integration Rules

## Before modifying existing code
1. Query GitNexus impact tool: what depends on the file/function being changed?
2. If blast radius > 2 files: list all affected files and request human approval
3. After completing changes to all affected files, verify no broken imports

## Before creating new modules
1. Query GitNexus query tool: what existing modules handle this functionality?
2. Ensure the new module does not duplicate existing functionality
3. After creating the module, run npx gitnexus analyze to update the graph

## When implementing cross-module features
1. Query GitNexus context tool for the target function/class
2. Understand its callers, callees, and data flow before modifying
3. Update all downstream consumers if interfaces change

## After completing each Phase
1. Run npx gitnexus analyze to re-index
2. Verify the knowledge graph reflects the new architecture
