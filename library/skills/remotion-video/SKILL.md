---
name: remotion-video
description: Plan and implement programmatic videos with React and Remotion.
---

# Remotion Video

Use when the deliverable is a repeatable or data-driven video rendered with
Remotion.

## Workflow

1. Confirm message, audience, duration, dimensions, frame rate, format, and
   source asset rights.
2. Write a frame-based beat sheet before code.
3. Define typed composition props and deterministic asset paths.
4. Split scenes into small React components with explicit frame ranges.
5. Drive motion from `useCurrentFrame`, `interpolate`, and spring functions;
   avoid browser-time APIs and nondeterministic state.
6. Reserve safe areas, keep text readable, and provide captions when speech
   carries meaning.
7. Preview representative frames, then render a short sample before the full
   output.

Return the composition structure, timing table, asset list, code plan, render
command, and verification checklist. Never imply that copyrighted media is
licensed unless evidence is provided.
