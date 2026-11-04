# Practice pack: ui-qa-expert

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## CTAL-TA: techniques applied to screens
- Input fields: equivalence partitions plus boundaries (empty, 1 char, max, max + 1, spaces only, Unicode); one invalid value per test so errors do not mask each other; check the message, the field focus and that nothing was saved.
- UI states as a state transition table: loading, empty, error, no permission, one row, many rows, saving, saved; test each valid transition and the invalid ones a fast user can cause (double click, click during loading, back after save).
- Filters and search as a decision table: each filter alone, two together, none matching, blank; expected total and page 1 after each change. Many independent options: pairwise.
- Experience-based: error guessing from `lessons.md` and the classics (long text, an apostrophe, `<b>`, paste, double click, back, reload mid-action, two tabs); exploratory sessions use the plan's charter and a time box.
- Checklist-based: the UQ items are the checklist; every changed screen part gets a result each, with evidence. See UQ1-UQ18 for the items, not repeated here.
- Pass only with evidence from this run: page text, a count, a console or network line, a screenshot for layout and colour.
- Defect report: UQ id, steps, expected, actual, evidence, MUST or SHOULD, owner; severity apart from priority.

## CT-UT: usability findings
- Nielsen's 10 heuristics, each with what a finding looks like:
- Visibility of status: a save with no sign, a spinner that never clears, no "21-40 of 312".
- Match with the real world: internal ids or codes as labels, jargon instead of the user's words.
- User control and freedom: no cancel or undo, a dialog with no close, back loses the filter.
- Consistency and standards: two names for one thing, a pager in different places on two lists.
- Error prevention: delete with no confirmation, free text where a picker fits, no limit hint.
- Recognition over recall: a user must remember a value from another screen; options hidden in a menu.
- Flexibility and efficiency: no keyboard path, no filter on a 300-row list.
- Minimal design: three buttons that do the same, text nobody needs.
- Error recovery: "Error 500" with no next step, typed input lost after a failure.
- Help and documentation: an empty state with no why and no next step.
- Severity 0 = not a problem; 1 = cosmetic; 2 = minor, fix when time; 3 = major, fix before release; 4 = catastrophe, blocks the task or loses data. Rate by frequency, impact and whether users can work around it; 3-4 are MUST, 1-2 SHOULD.
- Name the heuristic in each finding, and the task the user was doing.
- Usability sample: one real task, steps and time; hesitation or a wrong first click is a finding even when the function works.

## IAAP WAS: WCAG 2.2 AA in practice
- Keyboard: Tab in reading order, Enter and Space act, Escape closes, no trap; test one pass with no mouse (UQ13).
- Focus: order follows the layout, visible focus at all times, moves into an opened dialog or detail and back on close; focus never lands on a hidden element.
- Names and roles: every control has an accessible name in `read_page`; icon buttons, the pager and inputs included; a label, not only a placeholder.
- Contrast: text 4.5:1, large text (24 px or 18.66 px bold) and control borders, icons, focus ring 3:1; check on a pale and a dark tenant colour.
- Reflow: no horizontal page scroll at 320 CSS px (a wide table scrolls inside its own box).
- Text resize: 200% text or zoom keeps all content and controls usable.
- Target size: pointer targets at least 24 x 24 CSS px, or enough spacing.
- Status messages: saved, failed, loading done are announced or shown as text, never colour alone.
- Do not rely on colour, hover only or a drag-only action; a drag has a click alternative.

## NN/g UX: lists, detail, text and language
- Long lists: server paging with a total; pager directly under or above the table with "21-40 of 312" and next and previous; a filter or sort change goes to page 1; a page past the end gives the last page, never an error.
- Master-detail: the detail opens next to or over the clicked row, or scrolls into view; test from the last row of a long page; closing returns focus and scroll to the row.
- Truncation: cut-off text has a tooltip on hover and keyboard focus or an expand; a long word with no spaces (200 chars) must not overflow.
- i18n: German runs about 35% longer than English, Finnish has long compounds; test with the longest label in buttons, tabs, chips, column headers and menus: wrap or truncate with a tooltip.
- (SAP) Fiori: a growing list shows a count in the toolbar title and loads more by "More"; flexible column layout or an object page keeps the detail in view; `sap.m` controls keep their built-in keyboard support; test in the launchpad shell when the app runs there.
- (SAP) Launchpad shell: back navigation, the shell header and the app title stay correct after opening a detail.

## Browser habits
- Own tab with `tabs_create`; pass its `tabId` on every call; close it and reset the viewport at the end.
- Chain steps in one `browser_batch`; read with `get_page_text`, `read_page`, `find` first; a screenshot only to judge layout or colour.
- 200% zoom: `resize_window` to half the desktop width (640 x 400 for 1280 x 800) and reload; this is how WCAG 1.4.4 and 1.4.10 are checked.
- Phone widths 360 and 375 px; reset with the desktop preset.
- Tenant colour: set the theme's CSS variable on `document.documentElement` through `javascript_tool` (one pale, one dark), judge contrast and focus ring, then reload to undo; never save a shared tenant's setting.
- Force an error or a long label in the page only to check a state, undone by a reload.

## Traps
- A list seen with 5 rows is PASS for nothing; fix: BLOCKED for UQ3-UQ6 until 3+ pages exist.
- Passing the layout at one width; fix: 360, 375, half-width and desktop.
- Judging contrast by eye; fix: compute the ratio from the two colours when close.
- Checking the page at the top only; fix: open the detail from the last row.

## Numbers
- Contrast 4.5:1 text, 3:1 large text and borders; reflow 320 CSS px; text 200%; target 24 px.
- Viewports: 360, 375, 640 x 400 for 200%; German about +35% text length.
- Severity 0-4; 3-4 = MUST.
