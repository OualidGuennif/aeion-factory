---
type: Policy
title: "UI and UX"
description: "Monochrome interfaces aligned with Æion Spec: tokens in one file with light and dark sets, AA contrast, sidebar section switching, bounded pagination, and zero decorative clutter."
status: stable
generated:
  by: aeion-template/4.0.3
  at: 2026-11-17T00:00:00Z
sources:
  - id: tokens
    resource: ../../demo/app/theme.css
    title: "Monochrome light and dark colour tokens"
  - id: theme
    resource: ../../demo/app/theme.js
    title: "Theme toggle with localStorage persistence"
---

# UI and UX

Interfaces stay sober, fast to scan, and free of decorative clutter.

## Tokens

- Every colour, radius, font, and shadow lives in [`demo/app/theme.css`](../../demo/app/theme.css), with both light and dark sets (`html[data-theme="light"]`, `html[data-theme="dark"]`, and system `prefers-color-scheme: dark`).
- The palette follows Æion Spec's monochrome approach: an alabaster canvas (`#f8f8f7` light / `#0b0b0d` dark), crisp white or charcoal panels (`#ffffff` / `#121215`), solid black/white primary actions (`#0d0d10` / `#f4f4f6`), and midnight blue (`#172554` / `#93b4ef`) for links and focus rings. Semantic green, amber, and red appear only when a status requires attention.
- Body text meets WCAG AA (4.5:1) and stays at `>= 14px`. Amounts, counts, and timers use monospace or tabular figures.

## Layout and behaviour

- **One section on screen at a time**: both `/` and `/lab` use a left sidebar that switches between focused sections (`Catalog`, `Builds`, `Budget & mode`, `Environments & logs` on `/`; `Run a task`, `Run history`, `Models`, `Memory`, `Architecture` on `/lab`).
- **Bounded lists with pagers**: long lists never dump 100 items on one scrollable page. The feature catalog shows 10 items per page (`#catalog-pager`), and build queues, build history, lab runs, and checkpoints show 5 items per page with `← Prev`, numbered pages, `Page X / Y`, and `Next →`.
- **Responsive**: checked at 375 px and 1440 px in both light and dark modes.
- **Strict CSP**: no inline `style=` attributes or inline scripts (`style-src 'self'`).

## Truthfulness

- Unknown or missing values read `"unknown"` or `"unavailable"`, never `"fine"` or zero.
- Simulation and offline modes state plainly that no paid model call, pull request, or `main` merge occurs.
