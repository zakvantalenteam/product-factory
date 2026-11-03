# Practice pack: ux-designer

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## NN/g UX: research method and interaction design
- "Where do users get stuck?" -> qualitative usability test with think-aloud, 5 users per user group per round, then fix and test again.
- "How well does it perform, did it improve?" -> quantitative benchmark (task success, time on task, a 7-point ease rating per task), about 40 users per group.
- "How do users group and name our content?" -> open card sort; "can they find X in our structure?" -> tree test, before any visual design.
- "What do users need, in what context?" -> field visit or contextual interview; ask about the last real time ("Show me how you did it last week"), never "Would you use this?".
- "Which version works better live?" -> A/B test or analytics; they show what happens, only a usability test shows why.
- No users available -> heuristic evaluation by 3-5 evaluators working alone, merged afterwards; it finds other issues than users do, so it adds to testing, never replaces it.
- When what people say (surveys, interviews) and what they do (tests, analytics) disagree, trust what they do.
- Task scenarios: a real goal with the data needed and no UI words ("Find the safety course due this month", not "Open Courses and filter"); pilot one session first.
- Facilitating: stay neutral, never help or explain; answer a question with a question ("What would you expect?"); note hesitation, wrong clicks and backtracking.
- Rate every finding 0-4 (0 none, 1 cosmetic, 2 minor, 3 major, 4 catastrophe) from frequency, impact and persistence; 3 and 4 are fixed before build.
- Response limits: under 0.1 s feels instant, 1 s keeps the flow, 10 s keeps attention; 2-10 s gets a looping indicator, over 10 s a progress indicator with the current step and a Cancel; AI answers show work within 1 s, stream or show stages, and offer Stop.
- Heuristic pass as questions, part 1: does every action show a result (status)? are the labels the users' words from research, not our table names (match)? can every step be cancelled or undone (control)? does the same thing look and work the same everywhere, including the platform (consistency)?
- Heuristic pass, part 2: is the slip made impossible by constraints and defaults (prevention)? are options shown, not remembered (recognition)? do frequent users get bulk actions, shortcuts and saved filters (efficiency)? does every element earn its place (minimal)? do errors say what and how to fix (recovery)? is help at the point of need (help)?
- Forms: one column, label above the field, only the fields the goal needs; mark the rarer of required or optional; validate a field when the user leaves it, not per keystroke; keep what they typed after an error.
- Controls by job: few exclusive options all visible -> radio buttons; many -> select or combobox with type-ahead; on/off that applies at once -> switch; on/off applied on Save -> checkbox.
- Modal dialog only when the user must decide before going on; otherwise inline or a side panel; never a modal on a modal.
- Confirm only irreversible actions and name object and count ("Delete 3 plans?" with button "Delete plans"); reversible actions get Undo instead, because frequent confirmations are clicked through unread.
- Progressive disclosure stays at two levels at most; a third level loses users.
- Links and buttons name the destination or result; no lone "Learn more", "Click here" or "Details" (weak information scent).
- Hierarchy within our limits (weights 400-500, no shadows): size, spacing and tinted fills; group by proximity (larger gap between groups than inside one), one alignment grid.
- Tables: numbers right-aligned with equal decimals, text left-aligned, header visible on scroll, sort state shown on the column.
- Empty state says why it is empty and offers the next action; an error message sits next to the problem, says what happened in the user's words and how to fix it, never blames, never only a code.
- Tooltips carry extra info only, never something needed to finish (touch has no hover); icon without text only for universally known icons (search, close, menu).
- (SAP) Floorplan by job: list report for finding and acting on many items with filters, worklist for a to-do list with little filtering, object page for one item in sections, overview page for a role's cards across sources.
- (SAP) Messages by weight: field value state for one field, message strip for page-level info, message toast for a short success, message popover for many messages, message box only when the user must decide.

## IAAP CPACC: disability, universal design and law
- Social model: disability is the mismatch between a person and the design, so remove the barrier in the main product; no separate "accessible version", no need to declare a disability to get a working path.
- Blind users: screen reader with keyboard or touch gestures; they need text alternatives, headings and landmarks to skim, labelled fields, a logical order, status said in words.
- Low vision: zoom to 400%, magnifiers show only part of the screen, so keep labels next to fields and messages next to the action; high-contrast modes must keep every state visible.
- Colour vision deficiency, mostly red-green: status pairs need an icon or text, and charts need labels or patterns, not colour keys alone.
- Deaf and hard of hearing: captions for video, transcripts for audio; for some sign-language users written text is a second language, so plain words matter.
- Motor and dexterity: keyboard only, switch access, voice control ("click Save plan" must match the visible label), eye tracking; avoid drag-only actions, small or crowded targets and time pressure.
- Cognitive, learning and neurological: plain short text, one task per screen, consistent placement, no time limits, no memory test at sign-in, errors prevented and easy to fix.
- Seizure and vestibular: no flashing, no large motion (parallax, zoom transitions) without a reduced-motion path.
- Temporary and situational limits (broken arm, sunlight, noise, one hand on a phone) hit the same barriers, so the fix helps them too (curb-cut effect).
- Universal design review list: equitable use, flexibility in use, simple and intuitive, perceptible information, tolerance for error, low physical effort, size and space for approach and use.
- Research includes disabled users: for a new screen or new navigation, recruit at least one screen reader or keyboard-only user per round.
- EU law: European Accessibility Act (Directive (EU) 2019/882); Web Accessibility Directive (EU) 2016/2102 for public-sector sites and apps, with an accessibility statement; both are met in practice through EN 301 549 (clause 9 web = WCAG 2.2 AA in V4.1.1 of Sep 2026, 2.1 AA in the still-cited V3.2.1; 11 software, 12 documentation and support).
- Elsewhere: US Section 508 for federal buying (WCAG 2.0 AA), the ADA through the courts; worldwide the UN CRPD, Article 9.
- Procurement proof: an Accessibility Conformance Report on the VPAT template (EU edition for EN 301 549) per release, listing every known gap with a fix date; help pages and support channels must be accessible too.

## Traps
- "Would you use this?" or "Do you like it?" predicts behaviour badly; fix: watch them do a task, ask about past behaviour.
- One round of 15 users instead of three rounds of 5; fix: test, fix, test again.
- Five users mixed across roles (admin, manager, learner); fix: 5 per group, or 3-4 per group when there are two or more groups.
- Percentages from a 5-user test ("80% failed"); fix: report counts and problems, numbers only from a quantitative study.
- Using "7 plus or minus 2" to cap menu items: menus are recognised, not recalled; fix: group and label from the card sort.
- Disabled primary button with no reason; fix: say next to it what is missing, or keep it enabled and explain on press.
- Row actions shown on hover only are lost on touch and to keyboard users; fix: always visible, or shown on focus too.
- An accessibility overlay or toolbar widget does not make a product conform; fix: the product itself.
- Auto-advancing carousel: missed content and a WCAG failure without pause; fix: no auto-advance.

## Numbers
- 5 users per round find about 85% of the problems a design has for that group.
- About 40 users per group for a quantitative study; 15 for a card sort; 39 for eye-tracking heatmaps.
- 3-5 heuristic evaluators; one evaluator alone finds about 35% of the problems.
- System Usability Scale: 68 is the average score; below it, the design is worse than most.
- Design limits from WCAG 2.2 AA: text contrast 4.5:1, large text and UI parts 3:1, targets 24x24 CSS px, reflow at 320 CSS px, text to 200%, at most 3 flashes per second.
- About 1.3 billion people, 1 in 6, live with a significant disability (WHO); colour vision deficiency affects about 1 in 12 men and 1 in 200 women.
- European Accessibility Act applies to products and services placed on the market from 28 June 2025.
