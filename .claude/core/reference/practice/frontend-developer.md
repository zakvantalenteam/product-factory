# Practice pack: frontend-developer

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## IAAP WAS: building and checking accessible UI
- Element first: `<button type="button">` acts, `<a href>` navigates, `<input>` with `<label for>` collects; a `div` with a role also needs `tabindex="0"`, Enter and Space handlers and state attributes, so use it only when no element fits.
- Accessible name order: `aria-labelledby`, then `aria-label`, then the label or content, then `title`; the visible label text must be inside the name (2.5.3) so voice users can say it.
- Icon-only button: `aria-label` on the button, `aria-hidden="true"` on the icon; decorative image `alt=""`; an image that is a link's only content gets the destination as its alt.
- Field help and errors linked with `aria-describedby`, `aria-invalid="true"` on the failed field, text says what is wrong and how to fix it; after a failed submit, focus moves to the first invalid field or an error summary.
- Groups: radio and checkbox sets in `<fieldset>` with `<legend>`; data tables with `<th scope>` and a caption, never a grid of `div`s for data.
- Modal dialog: native `<dialog>` with `showModal()` (inert background, Esc built in) or `role="dialog"` with `aria-modal="true"` and `aria-labelledby`; focus to the first field or the title on open, Tab stays inside, Esc closes, focus back on the trigger.
- Route change in a single page app: update `document.title` and move focus to the new `h1` or `main` (`tabindex="-1"`), or screen reader users hear nothing.
- Live regions: the container (`role="status"` polite; `role="alert"` only for errors that need action now) is in the DOM before the update; announce a short summary ("8 results", "Answer ready"), never the whole LLM answer, never per streamed token.
- Composite widgets (tabs, listbox, menu, grid, tree) follow the ARIA Authoring Practices keyboard model: one Tab stop, arrows inside (roving `tabindex` or `aria-activedescendant`), Home and End.
- Search box with suggestions: `role="combobox"` with `aria-expanded`, `aria-controls` and `aria-activedescendant`; DOM focus stays in the input while arrows move the active option.
- Focus ring: `:focus-visible` with `outline` (for example 2 px solid, 2 px offset), 3:1 against its surroundings; never `box-shadow`, which breaks the no-shadow default and is removed in forced-colors mode.
- WCAG 2.2 additions to check on every screen: focus not hidden under sticky bars (2.4.11, fix with `scroll-padding`), a click alternative to every drag (2.5.7), target size (2.5.8), help in the same place on every page (3.2.6), no re-entry of data given earlier in the same process (3.3.7), sign-in with no memorising or transcribing, paste allowed (3.3.8).
- Test in this order and log each: automated scan (axe or Lighthouse, which find only part of the issues), keyboard-only pass, screen reader pass (NVDA with Chrome or Firefox, VoiceOver with Safari), 200% text and 400% zoom, Windows forced colours, reduced motion.
- Remediation order: blockers first (a task cannot be finished by keyboard or screen reader), then the main journey, then the rest; fix the shared component once, not each screen.
- EU proof: the European Accessibility Act is shown in practice against EN 301 549: EN 301 549 V4.1.1 (Sep 2026) moves the web clause to WCAG 2.2 AA; until it is cited in the EU Official Journal the cited V3.2.1 means WCAG 2.1 AA; building to WCAG 2.2 AA covers both.

## C_FIORD: SAPUI5 and Fiori apps
- (SAP) Fiori elements (list report, object page, worklist) need an OData service with annotations and bring paging, variants and accessibility for free; our Spring Boot APIs are plain REST, so freestyle UI5 with `JSONModel` is the default unless the story brings an OData service.
- (SAP) Manifest first: data sources, models, routing, i18n and library dependencies live in `manifest.json` (`sap.app`, `sap.ui5`); `Component.js` stays thin (parent `init`, router `initialize`).
- (SAP) Routing: attach `patternMatched` in `onInit`, read the key from the route arguments and `bindElement` there; a bookmark or browser back rebuilds the screen from the URL alone.
- (SAP) Binding mode on purpose: `JSONModel` defaults to two-way, the OData V2 model to one-way; a view must never write into shared data by accident.
- (SAP) Formatting and parsing through model types (`sap.ui.model.type.Date`, `Float`, `Integer`, `Currency` with format options) for locale and validation; expression binding only for one-line conditions, the rest in a formatter.
- (SAP) Validation: types with constraints plus `"handleValidation": true` in the manifest; messages go to the message manager and a message popover, field value states, not a hand-made red label.
- (SAP) Stable IDs on every control in XML views (key-user adaptation, OPA5 and wdi5 selectors need them); fragments loaded with the view ID as prefix (`Fragment.load({ id: oView.getId(), ... })`, or `this.loadFragment` where the version has it).
- (SAP) Lists: `growing` with `growingThreshold` for server paging; sort and filter on the binding (`getBinding("items").filter(...)`), never by looping over rows.
- (SAP) Content density: `sapUiSizeCompact` on the root for mouse devices, cozy on touch (`Device.support.touch`); compact matches our spacing default.
- (SAP) Custom CSS takes colours from theming CSS variables (for example `var(--sapBrandColor)`, `var(--sapTextColor)`), so tenant and high-contrast themes keep working.
- (SAP) Accessibility: `sap.ui.core.InvisibleText` as a hidden label for `ariaLabelledBy`; `sap.ui.core.InvisibleMessage` for announcements (check it exists in the loaded version); `landmarkInfo` on `sap.m.Page` or `sap.f.DynamicPage` so readers can jump between regions.
- (SAP) Launchpad and Work Zone: navigate between apps by intent (semantic object and action from `sap.app.crossNavigation`), never by a hard-coded URL.
- (SAP) Start-up (LCP): `data-sap-ui-async="true"` in the bootstrap, the built `Component-preload.js`, `"lazy": true` on manifest libraries the first screen does not use.
- (SAP) Tests: QUnit for formatters and models, OPA5 with stubbed backend responses for in-app journeys (`waitFor` arrangements, actions, assertions), wdi5 for end to end in the launchpad.

## Traps
- `aria-label` on a plain `div` or `span` is not reliably announced; fix: a native element or a role that takes a name.
- `aria-hidden="true"` on a focusable element or its parent leaves focus on something silent; fix: `inert`, or do not hide it.
- Positive `tabindex` scrambles the order; fix: order the DOM, use only `0` and `-1`.
- Placeholder as the label vanishes on typing and often fails contrast; fix: a visible label.
- A live region added together with its first message is often not read; fix: render the empty region at load, then change its text.
- A `<button>` inside a `<form>` submits by default; fix: `type="button"` on every non-submit button.
- Contrast checked on the base token only; fix: also hover, selected, tinted fill and error states (our 13px text is never large text).
- `loading="lazy"` on the hero image delays LCP; fix: lazy-load below the fold only, give the hero `fetchpriority="high"`.
- A page-load Lighthouse run has no interactions, so it shows no INP; fix: Total Blocking Time as the lab hint, field data (`web-vitals` library) for INP.
- Content inserted above what the user reads (banner, late image, async result) shifts the layout; fix: reserve its height or insert below (shifts within 500 ms of a user input do not count).
- (SAP) A fragment created twice without the view ID prefix throws a duplicate ID error; fix: load once, add it to `dependents`, reopen it.

## Numbers
- Contrast: text 4.5:1; large text 3:1 only from 24 px regular or about 18.7 px bold; component borders, icons and focus rings 3:1 (1.4.11).
- Target size: at least 24x24 CSS px, or spaced so a 24 px circle on each target touches no other (2.5.8); 44x44 px is the AAA level.
- Reflow at 320 CSS px wide with no side scroll (400% zoom of 1280 px), data tables excepted; text resizes to 200% with nothing lost.
- Text spacing (1.4.12): line height 1.5, paragraph spacing 2, letter spacing 0.12, word spacing 0.16 times the font size, nothing cut off.
- Time: warn before a session timeout and give at least 20 s to extend with one action (2.2.1); auto-moving content over 5 s needs a pause (2.2.2); at most 3 flashes per second (2.3.1).
- LCP: good at 2.5 s or less, poor over 4 s, at the 75th percentile of page loads; moved by server response time, render-blocking CSS and JS, the hero resource priority and client rendering before first content.
- INP: good at 200 ms or less, poor over 500 ms; it is input delay plus handler time plus the next paint; moved by main-thread tasks over 50 ms, so split work, yield, debounce and render less per interaction.
- CLS: good at 0.1 or less, poor over 0.25; moved by images without size, late fonts, injected banners and async results without reserved space; animate `transform` and `opacity`, not layout properties.
