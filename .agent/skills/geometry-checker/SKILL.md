---
name: geometry-checker
description: >
  Activated for geometry problem verification via AlphaGeometryRE DDAR.
  OFFLINE USE ONLY for full DDAR runs.
---

# Geometry Checker Skill

## AlphaGeometryRE
- This is AlphaGeometry v1 (not v2). No beam search.
- DDAR engine is deterministic, runs on CPU
- Use for: verifying synthetic plane geometry claims

## Limitations
- Cannot handle auxiliary point constructions without LM
- Cannot handle 3D, non-Euclidean, or analytic geometry
