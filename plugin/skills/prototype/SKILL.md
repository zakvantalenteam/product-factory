---
name: prototype
description: Build a clickable single-file HTML prototype with 2-4 lettered design variants before any real UI code, so the developer can pick one. Use for any new screen, widget, card, dialog or redesign (Design stage of the sdlc flow, or SP in product mode for a new screen), and when asked for a "proto", mockup or options.
---
# Prototype first

Repo notes first: the `## Live check and verify notes` section of AGENTS.md, when the repo has one (theme, component library and the UI gate); it wins over the defaults below.

1. Restate the target in one line: which surface (page, widget, dialog, admin screen, embedded frame) and where it sits.
2. Study the real thing first: the current template and CSS, the theme variables named in AGENTS.md or `.claude/rules/`, real labels and real data shapes. Use real-looking data, never lorem ipsum.
3. One self-contained HTML file, `<work>/<id>/prototype.html` (product mode: `P-prototype.html`) (inline CSS and JS, no CDN, works offline) with a variant switcher A / B / C (/ D) at real size, a narrow-width toggle (~360 px) and a short-frame toggle where it matters.
4. UI defaults (unless AGENTS.md says otherwise; details in `${CLAUDE_PLUGIN_ROOT}/reference/standards/ui.md`): no shadows, compact spacing, 13px text, weights 400-500, tinted (not saturated) fills from the primary colour, white text on primary buttons, keyboard-only focus ring, WCAG AA contrast.
5. Give each variant a one-line caption of what differs. Open it for the developer in the browser pane, or publish it as a private artifact if they want a link.
6. Stop and ask "Which one?". Build only the chosen variant, porting the prototype's CSS and markup faithfully, and record the choice in `design.md` and the D5 approval with `live_status.py ok`.
