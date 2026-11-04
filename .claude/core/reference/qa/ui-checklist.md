# UI test checklist (MUST)

Read by `ui-qa-expert` (every UI change), `e2e-qa-expert` (the screens on its journeys), `qa-lead` (plan and
sign-off) and the Tech Lead (a quick fix's live check). Every item is a MUST: a FAIL fails Test and the change goes
back to Build with the item id, the steps, what was expected and what showed. Each changed screen part gets every
item a result: PASS, FAIL, N/A (with the reason) or BLOCKED (what is needed to run it). NOT RUN is never PASS.
Evidence is what the browser showed: text and counts read with `get_page_text` / `read_page`, a console or network
line, or a screenshot for layout and colour.

## Before the first check
- **UQ0** The served asset is the changed code (the project's asset check in AGENTS.md, or fetch the asset URL and
  find the new code), the app answers on `app.url`, and you are signed in as the role the row needs (the dev user or
  the role switch AGENTS.md names; never real credentials).

## States
- **UQ1** Each changed screen part shows every state, each one checked: loading (a busy sign, no layout jump), empty
  (says why and what to do next), error (a readable message with retry or close; the busy sign is cleared), no
  permission (a message, not a broken or blank page), one row, many rows. An empty list never stands for a failed
  read: force the error (stop the call with a bad filter or an offline request) and look.
- **UQ2** Long and odd text: a 200-character name with no spaces, a long URL, Unicode and emoji, an apostrophe and
  `<b>` in a title. Nothing overflows its box; cut-off text has a way to read it in full (a tooltip on hover and on
  keyboard focus, or an expand); markup shows as text.

## Lists and paging (any list that can grow past one screen)
- **UQ3** Server paging with a total: the request asks for one page (`page`/`size`, `top`/`skip` or a cursor) and the
  response carries the total; the page never loads all rows to page them in the browser. Checked in
  `read_network_requests`.
- **UQ4** A visible pager: the page shows where you are and how much there is ("21-40 of 312", or page 2 of 16) and the
  next and previous controls, placed where the user sees them without hunting (directly under or above the table, not
  below a long empty area or off to one side); it is a real control with an accessible name.
- **UQ5** Paging at scale, with at least three pages of data: first, next, last, the last page partly full, a page
  size change, and a page past the end (a hand-edited URL or a stale page after rows were deleted) gives the last page
  or an empty state, never an error.
- **UQ6** A filter, search or sort change goes back to page 1 and updates the total; the filter runs on the server over
  all rows, not only over the rows on screen.

## Master and detail
- **UQ7** Opening a row's detail (panel, drawer, dialog, expanded row) puts it where the user is looking: next to or
  over the clicked row, or the page scrolls it into view, and focus moves into it. Checked from the last row of a long
  page: the user never has to scroll back up to find the detail.
- **UQ8** Closing the detail returns focus and the scroll position to the row it came from; the list keeps its page,
  filter and sort.

## Layout
- **UQ9** Phone widths 360 px and 375 px (`resize_window`): no horizontal page scroll (a wide table scrolls inside its
  own box), no overlapping or cut-off controls, the main action reachable.
- **UQ10** 200% zoom: a viewport at half the desktop width (640 x 400 for 1280 x 800) and a reload; nothing overlaps,
  nothing is cut off, every control is reachable (WCAG 2.2 1.4.4 and 1.4.10).
- **UQ11** Long German and Finnish labels (switch the language, or put the longest translation into the label in the
  page for the check): buttons, column headers, tabs, chips and menus wrap or truncate with a tooltip; nothing spills
  out of its box or pushes a control off screen.
- **UQ12** Light and dark tenant colours: one pale and one dark primary colour (the tenant theme setting on a dev
  tenant, or the theme's CSS variable set in the page for the check, never a shared tenant's saved setting). Text and
  icons on the colour keep contrast 4.5:1 (3:1 for large text and control borders); the focus ring stays visible.

## Keyboard and screen reader
- **UQ13** Keyboard only: every action is reachable with Tab in reading order, focus is always visible, Enter and Space
  act, Escape closes a dialog or panel, focus never gets stuck and never lands on something hidden.
- **UQ14** Names: icon-only buttons, the pager, inputs and the detail panel have accessible names in `read_page`; a
  status change (saved, failed, loading done) is announced or shown as text, not only by colour.

## Actions and data
- **UQ15** Each action shows progress and its outcome, a double click sends one request, a failure keeps what the user
  typed and allows retry, and a delete or other destructive action asks first.
- **UQ16** After a save the list and the detail show the new value without a full reload, and a reload shows the
  stored value.
- **UQ17** Every role in the access matrix sees what it should: allowed actions work, a role without access sees the
  no-permission state; a hidden button is never the only protection (the API check for that endpoint is `qa-engineer`'s).

## Console and network
- **UQ18** On load and after each action: no new console errors or unhandled rejections (`read_console_messages`,
  errors only), no failed calls other than the ones the test causes on purpose, no request per row, and no request that
  asks for an unbounded page size (`read_network_requests`).

## Data volumes to test with
Empty, one row, exactly one page, one page plus one, three or more pages, and the largest volume the product will
really hold when the plan names it. Data comes from the dev data the developer points to or the app's own screens on a
local or dev tenant; never insert into a shared database, and ask (a question for the developer) when the volume is
missing. A list checked only with a handful of rows is BLOCKED for UQ3-UQ6, not PASS.
