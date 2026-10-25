---
name: debug
description: Investigates a reproducible bug, failed check or unexpected runtime behavior before changing code; traces evidence to the failing boundary and verifies the regression.
---

# Debug a failure

1. Capture the failing input, exact command/error and expected behavior. Reproduce it; if it
   cannot be reproduced, gather bounded evidence instead of inventing a cause.
2. Read the relevant spec, callers, configuration and recent diff. Follow the actual execution
   path to the first failing boundary. Distinguish observations, confirmed causes and hypotheses.
3. Form one falsifiable hypothesis. Use the smallest diagnostic or experiment that can reject
   it. Never print secrets or complete request/environment dumps as instrumentation.
4. Add a regression test when behavior changes: demonstrate the failure, apply the smallest
   root-cause fix, and verify success plus relevant negative paths. Keep assertions meaningful.
5. Run the owning checks, update the affected Knowledge/spec and report remaining uncertainty.
   Stop accumulating fixes when the hypothesis fails; return to evidence.

Adapted from the investigation sequence in obra/Superpowers `systematic-debugging` (MIT).
Attribution: `CREDITS.md`. Factory's existing authority, test and sign-off rules still apply.
