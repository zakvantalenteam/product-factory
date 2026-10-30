# UI standards

Read by `ux-designer` (options, variants, ui-spec, ui-review); `frontend-developer` reads "Defaults" only.
Theme variable names, the shell, base components and label files come from the repo (`AGENTS.md`,
`.claude/rules/`), never from this file.

## Defaults
- No shadows. Compact spacing on a 4/8/12/16 px scale. 13px base text. Weights 400-500.
- Colour only from the theme variables (the tenant primary colour and the tints derived from it). Tinted
  fills, 1px tinted borders, no saturated fills, no fixed hex or rgb.
- Focus ring for keyboard only (`:focus-visible`); never `outline: none` without a replacement ring.
- WCAG AA: 4.5:1 for text, 3:1 for large text and controls, also for text on the tenant colour, light and dark.
- Real buttons and links; tab order follows reading order; Escape closes a dialog and focus returns to its opener.
- Works at 360-375 px, at 200% zoom, with long labels in other languages.
- Avoid the generic AI look: heavy gradients, glass blur, shadows, emoji, saturated fills, oversized rounded
  cards, an icon on every line.

## Understand the screen first
1. The screen's job in up to 3 sentences: who uses it, the one main task, the decision they make, what they
   must see first. Take it from the brief and spec; confirmed answers there are fixed.
2. Study the real thing before judging it: today's markup, styles and theme variables, today's labels, the real
   data shape (empty lists, missing fields, long titles), the nearest existing screen of the same kind, and the
   repo's UI rules. When a reference design is named, port its real markup and styles faithfully; no reskin.
   Design only for fields that exist; a new field is a contract change (D3).
3. You cannot open a browser: ask the lead for screenshots (1440 and 375 px; light and dark tenant colour when
   colour matters; inside the host frame when the repo embeds the screen).

## Critique today's screen
One line per point: where it is (`path:line` or selector), why it matters to the user. Group by:
hierarchy (one primary action, most important fact first, scannable in 5 seconds); density (no wasted height);
states (empty, loading, error with retry, slow or failing outside system, no permission, long text, many rows);
keyboard (see Defaults); contrast; narrow width.

## Token plan, variants, improvements
- Token plan: table `variable | used for`; every colour, size and space the variants use, from theme variables only.
- Variants: 2-4 lettered A-D, recommended first. Per variant: the idea in one line, layout, what it is best at,
  its trade-off, the states shown, a real-looking data sample (made-up people).
- Improvements: at most 3 per screen, each with the reason (what the user gains) and the cost. Good kinds:
  skeleton rows instead of a spinner, inline progress on a card action, progressive disclosure, a transition of
  150 ms or less (off for `prefers-reduced-motion`), container queries for narrow frames.

## UX text
Short plain labels, verbs on buttons, sentence case. An error says what happened and what to do; an empty state
says why and the next step. Every new label is an i18n key with English text (locales come in the release pass).
Rules about product names and wording in user-facing text come from the repo's hard rules.

## Prototype rules (options and variants)
One self-contained offline HTML, no CDN. Tabs to switch option or variant. Real size, real-looking data with
made-up people. The repo's shell (sidebar, top bar) and theme tokens as CSS variables. Soft light look:
off-white background, white rounded cards, pastel tints of the primary colour, Defaults above. Show empty,
loading and error of the main screen, and 360 px for at least one variant. Plain words a user would see.

## Layouts
- `P-options.md` (options): per option the idea in one sentence, who it suits, the main journey in 3-6 steps,
  strengths, weaknesses, effect on scope and effort (smaller / same / bigger than the spec, and why), risks;
  then your recommendation. Prototype: the 3-5 key screens of the main journey per option, clickable.
- `P-options.md` (variants): per screen the variants, your pick and why, what each costs to build.
  Both: `## Added by the prototype` lists everything invented that the spec does not say (a filter, a shortcut,
  a default) so the spec-analyst can add it or drop it.
- Journeys (`03-journeys.md`, or `## Journeys and screens` in `ui.md`): per role the 3-6 journeys that matter as
  numbered steps (screen, action, result) with frequency and where the user may get stuck; a screen inventory
  table (screen, job, who, data shown, actions, states, entry points); where each screen sits in the navigation.
- UI spec, product mode (`05-ui.md`): only the approved option or variant. Per screen: layout regions; base
  components reused (named from the base spec) and new ones with why; fields with their API source (operation id
  and field); actions with the operation they call; every state with its exact text; validation messages mapped
  from problem-details codes; what each role sees (`05-security.md`); behaviour at 360 px; keyboard order and
  screen-reader labels; tokens; every label, empty state, error and confirmation as an i18n key with English text.
  Anything in the prototype with no story or no operation goes to `questions.md`.
- UI spec, task mode (`ui.md`): `## What the screen must do`; `## Today's screen` (table `area | problem |
  where | why it matters`); `## Variants` (`### Token plan`, then `### A <name>` ...); `## Improvements` (at
  most 3, `improvement - reason - cost`, then the new label keys with English text). The variants are the
  brief for the lead's `prototype` skill.

## Review (`ui-review`, writes `review-ui.md`)
Read the UI files of the diff (`git diff -- <file>`). Check: colours from theme variables only; keyboard-only
focus ring; AA contrast; compact spacing, 13px text, weights 400-500, no shadows; labels through keys; loading,
empty and error states; keyboard and aria; the screen matches the approved prototype variant (D5); the repo's
UI hard rules and checklist ids (`.claude/review/checklist.md`).
Findings table: `# | path:line | problem | failure scenario | fix | MUST/SHOULD | Confidence: NN`. MUST when a
repo hard rule or a checklist MUST breaks. Score honestly, write nothing under 50 (0 false positive or
pre-existing, 25 might be real, 50 real but minor, 75 checked twice or named in a rule, 100 certain). Not a
finding: lines the diff did not change, issues that existed before, what a linter catches, taste, a speculative
risk with no concrete path. Needs the running app = a "Live checks for Verify" line. No verdict; the
`code-reviewer` check pass re-verifies and merges.
