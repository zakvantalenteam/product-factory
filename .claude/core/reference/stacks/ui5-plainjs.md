# Stack pack: SAP UI5, plain JS widgets, approuter

Read once, at the start, by the agents that design, write or review UI5 or plain JS front ends. The repo's own rules,
the UI standard (`.claude/core/reference/standards/ui.md`) and the approved prototype win over this pack.

## Versions
- The bootstrap URL in the `index.html` files sets the UI5 version (an unversioned URL means "latest", so pin when
  the repo does); `manifest.json` `minUI5Version` is the floor. Use only APIs that exist in the version the page
  loads; an API added after 1.71 is checked in the API reference (ui5.sap.com/#/api, with the version) or marked
  "not confirmed" when you have no web tool.
- Never add a new deprecated API: `jQuery.sap.*`, sync XHR (`sync: true`, `jQuery.sap.sjax`), global names
  (`sap.m.Button` without `sap.ui.define`), `sap.ui.getCore().byId` across views.

## UI5 structure
- AMD modules with `sap.ui.define([...], function (...) { "use strict"; ... })`; async component and view loading
  (`"async": true` in the manifest routing and root view).
- XML views with data binding; controllers hold event handlers and call services; formatters in their own module,
  pure and tested.
- Models: `JSONModel` for view state, one per concern; `setSizeLimit` when a list may pass 100 rows; OData models
  with `$select` and server paging (growing lists with `growingThreshold`).
- Texts through the i18n `ResourceModel` (`{i18n>key}`); no text in code; `properties` files complete in English.
- Never touch a control's DOM directly (`$()`, `getDomRef` edits); use the control API or a custom control with a
  renderer. Destroy dialogs and fragments you create (`dependents` or `destroy` on close).
- Busy state on the control or the view (`setBusy`), error state with a `MessageStrip` or `MessageBox` and the
  translated text; a failed call is an error, never an empty list.

## Plain JS widgets (cards, AI widgets)
- Untrusted text (user input, LLM output, data from n8n or the backend) never goes into `innerHTML`,
  `insertAdjacentHTML`, `outerHTML`, `document.write` or a UI5 `FormattedText` without sanitising; use
  `textContent`, `createElement`, or an escaping helper the repo already has. Markdown from an LLM is rendered by the
  repo's sanitising renderer only. Links from data: allow `http:` and `https:` only.
- Build a list in a `DocumentFragment` or one escaped string, insert once; never read layout (`offsetHeight`,
  `getBoundingClientRect`) between writes in a loop.
- Event delegation on the container instead of one listener per row; remove listeners and clear timers when the
  widget is destroyed; `AbortController` or a request counter so a slow old response never overwrites a newer one.
- Debounce input (250-300 ms); throttle scroll and resize; `requestAnimationFrame` for animation; respect
  `prefers-reduced-motion`.
- Modules or one IIFE per file, `"use strict"`, `const`/`let`, `===`; no globals beyond the one namespace the repo
  uses; no prototype changes on built-ins.
- Colours, sizes and spaces from the theme (CSS variables or UI5 theming parameters), never fixed values.

## Accessibility (WCAG 2.2 AA)
- UI5 controls carry roles; set `ariaLabelledBy` or a `Label` `labelFor` for every input; icons that act get a
  tooltip and an accessible name.
- Plain JS: real `<button>` and `<a>` elements, `aria-live="polite"` for async results, focus moved into a dialog
  and back on close, focus ring for keyboard only (`:focus-visible`), targets at least 24x24 px, contrast 4.5:1.

## Speed
- Core Web Vitals: LCP under 2.5 s, INP under 200 ms, CLS under 0.1; reserve space for async content.
- Preload the component (`Component-preload.js` in the build); lazy-load views and libraries not on the first
  screen (`sap.ui.require` on demand); one backend call per screen state, never per row.

## Tests
- Where tests live: UI5 in `webapp/test/unit/<the same path>` (QUnit) and `webapp/test/integration/` (OPA5
  journeys); plain JS widgets served from `src/main/resources/static/**` in `src/test/js/<the same path>`. Never next to
  the code in a folder that ships (`webapp/` outside `test/`, `src/main/**`) and never in the repo root.

## Approuter
- Routes in `xs-app.json`: the most specific first, `authenticationType` set per route, CSRF protection on for
  modifying calls, no route that exposes a backend path the UI does not need; never put a secret or host in it.
