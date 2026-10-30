# Base product specification

Everything a fresh base project must contain so that `base-builder` can rebuild it from scratch and
`scripts/check_base.py` can verify it against `base-manifest.json`. Every line with an id is a checkable
requirement. Source: `D:\skillos\repo\SkillsOS` (read-only reference), shell at commit `91040a0`
(2026-07-24, "set proper ui changes"), generic modules from branch `dev` (HEAD `df053fa`, 2026-10-28).

## B0 How to read this spec

- B0.1 Placeholders (replace everywhere, including file names, labels, comments and README):
  `{{basePackage}}` Java root package (was `com.talenteam.skillsos`); `{{basePackagePath}}` the same as a
  path (`com/talenteam/<x>`); `{{productName}}` display name (was `SkillsOS`); `{{productSlug}}` lowercase
  slug used for context path, WAR name, `API_BASE`, approuter route, destination, xsappname, cookie name
  (was `skillsos`); `{{ProductClass}}` PascalCase prefix for Java class names (was `SkillsOs`);
  `{{cssPrefix}}` CSS variable prefix (was `sos`); `{{productTagline}}` sidebar subtitle (was `by TalenTeam`).
- B0.2 No file of the new product may contain the strings `skillsos`, `SkillsOS`, `SkillsOs`, `SkillOS`,
  `LearningAdmin`, `Lightcast`, `jobprofile`, `job profile`, `--sos-` (case-insensitive check, excluding
  `node_modules`, lock files and this spec).
- B0.3 Secrets: config files carry key names with placeholder values `<set-me>` only. No value is copied from
  the source `application*.properties`, `manifest.yml`, `xs-security.json` or `*Constants*` files.
- B0.4 Source tags: `91040a0:<path>` = take the file at the shell commit and rename; `dev:<path>` = take from
  `dev` and clean as stated; `new` = not in the source, build from the requirement here.
- B0.5 Manifest encoding: `file` = path relative to the product root; `endpoint` = `METHOD /path` relative to
  the backend context path; `table` = table name, `must_contain` = column names; `config` =
  `<file>:<key>`; `route` = frontend URL, `must_contain` = route file; `label` = `<locale file>:<dotted key>`.
- B0.6 Platform facts the rebuild must keep: Spring Boot 3.5.15 WAR, Java 17, EclipseLink 4.0.5 (not
  Hibernate), PostgreSQL 42.7.5 driver (database is PostgreSQL, flat tables in the default schema),
  TTCommon 2.0.0 jars supply authentication, `UserSessionBean`, `ConfigService`, jobs scheduler, locales,
  custom labels, users and their tables. SAP BTP Cloud Foundry with approuter + XSUAA.

## B1 Shell - Backend

Module `Backend/`, artifact `{{ProductClass}}-Backend`, packaging `war`.

- B1.1 `pom.xml` (root): aggregator `packaging pom`, groupId `com.talenteam`, artifactId `{{ProductClass}}`,
  modules `Backend` and `Frontend`, description without product-specific wording.
- B1.2 `Backend/pom.xml`: parent `spring-boot-starter-parent` 3.5.15; properties `java.version` 17,
  `ttcommon.version` 2.0.0, `mapstruct.version` 1.6.3, `start-class` `{{basePackage}}.{{ProductClass}}Application`.
- B1.3 Dependencies (exact set): TTCommon-Core, -LMS, -Jam, -SFTP, -Authentication, -Sharepoint, -Shared
  (all `${ttcommon.version}`; TTCommon-Core excludes `org.bouncycastle:bcprov-jdk15on` as on dev);
  spring-boot-starter-web, -validation, -cache; caffeine; spring-boot-starter-jdbc excluding HikariCP;
  tomcat-jdbc; org.eclipse.persistence.jpa 4.0.5; postgresql 42.7.5; modelmapper 3.2.1; mapstruct; flyway-core
  + flyway-database-postgresql (B1.25); spring-boot-starter-test (test).
- B1.4 Profiles: `local` (active by default) adds spring-boot-devtools, spring-boot-starter-tomcat,
  `com.sap.cloud:neo-java-web-api` 5.18.5; `production` marks starter-logging, starter-tomcat and
  neo-java-web-api as `provided`.
- B1.5 Build plugins: maven-compiler-plugin with mapstruct-processor annotation path and
  `-Amapstruct.defaultComponentModel=spring`; spring-boot-maven-plugin `mainClass` the application class;
  maven-war-plugin `warName` `{{productSlug}}`, `outputDirectory` `${project.basedir}/releases`,
  `packagingExcludes` `WEB-INF/lib/slf4j-api-*.jar`.
- B1.6 `{{basePackagePath}}/{{ProductClass}}Application.java`: extends `SpringBootServletInitializer`;
  `@SpringBootApplication @EnableCaching @EnableScheduling @EnableAsync`;
  `@ServletComponentScan`, `@EntityScan`, `@EnableJpaRepositories` all on `com.talenteam`;
  `configure()` calls `setRegisterErrorPageFilter(false)`; beans `LocaleResolver` (SessionLocaleResolver,
  default `Locale.ENGLISH`), `DatabaseAwareMessageSource messageSource()` (TTCommon; cacheSeconds 60,
  basename `classpath:messages`, UTF-8), `ModelMapper`. `main()` as at 91040a0 (sets system property
  `disableLoadMessages=true`).
- B1.7 `common/config/{{ProductClass}}ComponentScan.java` (dev): `@ComponentScan(basePackages="com.talenteam",
  lazyInit=false)` excluding regex `{{basePackage}}\..*` (already scanned by the app class) and the class
  `com.talenteam.common.helper.ConfigurationHelper`, so only the product's `@Primary` subclass (B1.17) exists.
- B1.8 `common/api/ApiResponse.java`: generic `<T>`, `@JsonInclude(NON_NULL)`, fields `success`, `message`,
  `data`, `error` (ErrorResponse); factories `ok(T)`, `ok(String,T)`, `fail(String)`, `fail(String,ErrorResponse)`.
- B1.9 `common/api/ErrorResponse.java`: `@JsonInclude(NON_NULL)`, fields `code`, `detail`, `requestId` (dev),
  `fieldErrors: List<FieldErrorDetail{field,message}>`.
- B1.10 `common/api/HealthController.java`: `GET /api/public/health` (no auth) returns
  `{status:"UP", service:"{{productName}}", timestamp: ISO-8601}`. Nothing else in this controller.
- B1.11 `common/config/CorsConfig.java`: `CorsFilter` bean, credentials allowed, origins from
  `{{productSlug}}.cors.allowed-origins` (default `http://localhost:3000,http://localhost:5173`), all headers,
  methods GET POST PUT PATCH DELETE OPTIONS, path `/**`.
- B1.12 `common/exception/BusinessException.java` (dev shape): `code` (default `BUSINESS_ERROR`), `status`
  (default 400), `fieldErrors`; constructors `(msg)`, `(code,msg)`, `(code,msg,status)`, `(code,msg,fieldErrors)`,
  `(code,msg,status,fieldErrors)`.
- B1.13 `common/exception/ResourceNotFoundException.java`: `code` default `RESOURCE_NOT_FOUND`.
- B1.14 `common/exception/GlobalExceptionHandler.java`: `@Order(HIGHEST_PRECEDENCE)`,
  `@RestControllerAdvice(basePackages = "{{basePackage}}")`. Mapping: ResourceNotFound 404; Business ->
  its status + code + fieldErrors; MethodArgumentNotValid and ConstraintViolation 400 `VALIDATION_ERROR` with
  fieldErrors; OptimisticLockException / ObjectOptimisticLockingFailureException 409 `CONCURRENT_UPDATE`;
  DataIntegrityViolation: optimistic lock -> 409, unique violation -> 409 `DUPLICATE`, else 409
  `VALIDATION_ERROR`; EntityExistsException -> unique violation; anything else 500 `INTERNAL_ERROR` with the
  fixed message "An unexpected error occurred", `requestId` from MDC and NO exception text (fixes the 91040a0
  leak of `ex.getMessage()`).
- B1.15 Error body format: for request paths under `/api/v1/` the handler writes RFC 9457 problem details
  (`application/problem+json`: `type`, `title`, `status`, `detail`, `instance`, `code`, `traceId` = request id,
  `errors[]{field,code,message}`); for all other paths it writes `ApiResponse.fail(message, ErrorResponse)`.
- B1.16 `common/security/AuthConfig.java`: empty `@Configuration` (TTCommon wires security).
  `common/security/AdminGuard.java` (dev): `isAdmin()` = `adminAccess || superAdminAccess` from
  `UserSessionBean`; `requireAdmin(msg)` throws BusinessException `FORBIDDEN` 403.
- B1.17 `configuration/service/{{ProductClass}}ConfigurationHelper.java`: `@Component @Primary` extends TTCommon
  `ConfigurationHelper`; `getEncryptedKeys()` and `getIntegrationKeys(group)` backed by a group -> keys map:
  `SUCCESSFACTORS`, `AZURE_OPEN_AI_KEYS`, `INTEGRATIONS_STATUS_KEYS`, `GENERAL` (`CONTENT_LANGUAGE`), `THEME`
  is NOT here (B7 uses its own table). Unknown group returns an empty list.
- B1.18 `configuration/service/{{ProductClass}}Configuration.java`: `@Component` extends TTCommon
  `BaseConfiguration`; typed getters only for keys the base uses.
- B1.19 `configuration/Constants.java`: config key names used by the base (B5.2 list), no values other than
  the key names themselves.
- B1.20 `configuration/dto/response/TestConnectionResponse.java`: `successMessageKey`, `errorMessageKey`,
  `errorDetailMessage`; message keys `Label.TestConnection.SuccessMsg`, `Label.Error.TestConnection.FailedMsg`.
- B1.21 Session: `session/controller/SessionController.java` `GET /api/session/me` (no envelope) returns
  `{userId, fullName, locale, companyId, adminAccess, superAdminAccess}` from `UserSessionBean`
  (constructor injection).
- B1.22 i18n: `i18n/controller/LocaleController.java` under `/api/i18n`: `GET /locales` ->
  `ApiResponse<List<{localeId, localeDesc}>>` (TTCommon `LocaleConfigService.getAllActiveLocales`);
  `GET /preferences` -> `ApiResponse<{uiLanguage, contentLanguage}>`; `PUT /preferences` body
  `{uiLanguage, contentLanguage}` -> same, message "Locale preferences saved"; `GET /labels?locale=` ->
  `ApiResponse<Map<String,String>>` of non-empty TTCommon custom labels.
- B1.23 `i18n/service/LocalePreferencesService.java`: uiLanguage resolved from persisted user DEFAULT_LOCALE
  (UserDetailsService), then session, then `en`; contentLanguage from config key `CONTENT_LANGUAGE` (default
  `en`); update validates both via `LocaleConfigService.isValidLocale` (400 `INVALID_LOCALE`), 400
  `INVALID_REQUEST` on empty body, 404 `USER_NOT_FOUND`, saves user default locale + session locale, stores
  `CONTENT_LANGUAGE` via `ConfigService.storeConfiguration`, 500 `CONFIG_STORE_FAILED` on CryptoException.
  DTOs `i18n/dto/request/UpdateLocalePreferencesRequest`, `i18n/dto/response/LocaleOptionResponse`,
  `LocalePreferencesResponse`.
- B1.24 `common/web/RequestIdFilter.java` (dev): `OncePerRequestFilter`, highest precedence, reads
  `X-Request-Id` (kept if 1-64 chars of `[A-Za-z0-9_-]`, else new UUID), puts MDC `requestId`, echoes header.
- B1.25 Schema mechanism: Flyway, location `classpath:db/migration`, scripts `V<NNN>__<snake_name>.sql`,
  `baseline-on-migrate=true`; EclipseLink DDL generation off. TTCommon platform tables are NOT created by the
  base migrations; `Backend/src/main/resources/db/README.md` states they are provisioned from the TTCommon DDL
  (list: CONFIGURATION, CONFIGURATION_AUDIT, LOCALE_CONFIG, LOCALE_MAPPING, CUSTOM_LABELS, DATA_LOCALIZATION,
  MENU, LXP_USER_ROLE_ACCESS(+_AUDIT), LXP_USER_DETAILS, LXP_USER_PROFILE_PHOTO, USER_ATTRIBUTE, JOB_SCHEDULER,
  JOB_SCHEDULER_AUDIT, JOB_RESULT, JOB_API_REQUEST_COUNT, CLUSTER_STATUS, SESSION_INFO, SESSION_TOKEN,
  SPRING_SESSION, SPRING_SESSION_ATTRIBUTES, EMAIL*, EVENT_MESSAGE*, INCOMING_EVENT_MESSAGE, JAM_*,
  TT_FILE_UPLOAD_TEMP, SYS_AUDIT_REPORT_CRITERIA).
- B1.26 `src/main/webapp/WEB-INF/web.xml`: web-app 3.0, `display-name` `{{productName}}`, resource-ref
  `jdbc/DefaultDB` (javax.sql.DataSource) and `connectivityConfiguration`
  (`com.sap.core.connectivity.api.configuration.ConnectivityConfiguration`), listener
  `RequestContextListener`, security-role `TTCONTENTBASE`.
- B1.27 `application.properties` keys (names only, values per environment): `spring.session.store-type`,
  `spring.profiles.active` (default `local`), `server.servlet.context-path` (`/{{productSlug}}`),
  `app.security.SecurityRole.USER|ADMIN|SUPER_ADMIN`, `talenteam.auth.cookie.name`
  (`_tt_{{productSlug}}_jwt_`), `{{productSlug}}.cors.allowed-origins`,
  `spring.servlet.multipart.max-file-size|max-request-size`, `spring.main.allow-bean-definition-overriding`,
  `spring.main.allow-circular-references`, `app.cache.expires.licenseDataCacheInMinutes|getUserRolesCacheInMinutes|
  getActiveLocaleInMinutes|getActiveLocaleConfigInMinutes|getMenuAccessMapCacheInMinutes|sessionInfoCacheInMinutes|
  findBySuccessFactorsIDCacheInMinutes`, `app.cache.sf.expires.successfactorsTokenCacheInMinutes`,
  `jam.access.enabled` (false), `logging.level.com.talenteam.authentication`, `logging.level.{{basePackage}}`,
  `logging.pattern.level` (`%5p [%X{requestId:-}]`), `spring.flyway.*`. Drop `app.cache.lightcast.*`.
- B1.28 `application-local.properties` and `application-test.properties`: keys `companyID`,
  `allowedNodeRoles`, `spring.session.store-type`, `spring.devtools.restart.enabled`,
  `spring.datasource.url|username|password|driverClassName`, `server.servlet.context-path`,
  `talenteam.auth.cookie.name`, `talenteam.dev.loggedInUser.id|defaultLocale|defaultFullName|preferedTimeZone|
  defaultLocaleCountry|companyID|adminAccess|isManager|superAdminAccess|isPlayListAdmin`,
  `{{productSlug}}.cors.allowed-origins`, logging keys; test adds `com.talenteam.scheduling.disabled`. Values
  `<set-me>`; both files listed in `.gitignore` guidance as secret-bearing.
- B1.29 `messages.properties` exists (basename of B1.6) with the two test-connection keys of B1.20.
- B1.30 Tests (JUnit 5, no Spring context, `MockMvcBuilders.standaloneSetup`): `ApiResponseTest`
  (ok, ok+message, fail), `HealthControllerTest` (200 UP), `GlobalExceptionHandlerTest` +
  `GlobalExceptionHandlerStubController` (`/stub/missing` 404 envelope, `/stub/business` status from exception,
  500 has no exception text, `/api/v1/stub/*` returns problem details), `RequestIdFilterTest` (sanitize rules).
- B1.31 Package layout per feature: `controller`, `service`, `repository`, `domain`, `dto/request`,
  `dto/response`, `mapper`, `exception`, `job` (only the folders that have classes; no empty
  `package-info.java` stubs).

## B2 Shell - Frontend

Module `Frontend/` (Maven wrapper pom + npm app).

- B2.1 `Frontend/pom.xml`: artifactId `{{ProductClass}}-Frontend`, packaging pom, frontend-maven-plugin 1.15.1:
  install-node-and-npm (node v24.18.0, npm 11.16.0), `npm ci`, `npm run build` in `generate-resources`.
- B2.2 `package.json` name `{{productSlug}}-frontend`, scripts `dev`, `generate-routes` (`tsr generate`),
  `build` (`tsr generate && tsc -b && vite build`), `lint`, `format`, `format:check`, `preview`, `test`
  (`vitest run`), `test:watch`. Dependencies as at 91040a0 (MUI 6 + emotion, radix label/radio-group/
  separator/slot, TanStack query 5 + router 1, react 19, react-hook-form 7 + @hookform/resolvers, zod 3,
  i18next + react-i18next, lucide-react, cva, clsx, tailwind-merge); dev deps as at 91040a0 plus vitest.
- B2.3 Tooling files: `vite.config.ts` (plugins tanstackRouter {target react, autoCodeSplitting}, react,
  tailwindcss; alias `@` -> `./src`; dev server port 5173 proxying `/{{productSlug}}` to
  `http://localhost:8080` with 10-minute timeouts; vitest `environment node`, include `src/**/*.test.ts`),
  `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`, `eslint.config.js`, `.prettierrc`,
  `.prettierignore`, `.gitignore`, `index.html` (title `{{productName}}`, Inter from Google Fonts, `#root`,
  `/src/main.tsx`), `public/favicon.svg` (neutral, not the SkillsOS mark).
- B2.4 `src/main.tsx`: calls `applyCssVars()` then renders `RouterProvider` in StrictMode; throws if `#root`
  is missing.
- B2.5 `src/lib/router.tsx`: `createRouter({routeTree, defaultPreload:'intent', scrollRestoration:true})`
  with the `Register` module declaration. `src/routeTree.gen.ts` is generated by `tsr generate`, never written
  by hand.
- B2.6 `src/routes/__root.tsx`: `RootErrorBoundary` > `QueryClientProvider` > `LocaleBootstrap` >
  `ThemeBootstrap` (B7) > MUI `ThemeProvider` + `CssBaseline` > `Outlet`; `errorComponent` shows the
  `shell.*` error screen.
- B2.7 `src/routes/index.tsx` redirects `/` to `/dashboard`. `src/routes/_public/route.tsx` plain Outlet.
- B2.8 `src/routes/_authenticated/route.tsx` (dev): `beforeLoad` ensures `CURRENT_USER_QUERY_KEY` via
  `fetchCurrentUser` (staleTime 5 min) and redirects to `/login` on error or missing userId; component wraps
  `SessionBootstrap` > `AppShell` > `Outlet`.
- B2.9 `src/routes/_public/login.tsx`: card with product name, `{{productTagline}}`, "Sign in" heading, one
  button that navigates to `/dashboard` (approuter/XSUAA performs the real sign-in). No email/password fields,
  no "dev bypass" text.
- B2.10 `src/routes/_authenticated/dashboard.tsx`: heading + subtitle, cards Projects (total), Open tasks,
  Integrations enabled, each with icon, value, hint, link; values from real APIs (B8 list `totalElements`,
  B5 status); loading and error states. No hard-coded numbers.
- B2.11 Routes `jobs.tsx` (B4) and `settings.tsx` (renders `SettingsPage`, tab from search param
  `tab=general|integrations|theme`).
- B2.12 `src/lib/api/http.ts` (dev version, renamed): `API_BASE='/{{productSlug}}'`, timeouts 30 s default /
  5 min long, `ApiError{status, message, fieldErrors, code}`, session-expired statuses 401 and 440 notify a
  single listener once, `apiFetch` (credentials include, timeout via AbortController), `parseResponseJson`
  (envelope unwrap when `success`; `envelope:false` for raw), `parseResponseText`, `apiJson`, `apiGetJson`,
  `parseErrorBody` reading `error.message|detail`, `message`, `error.code`, `error.fieldErrors`, and also RFC
  9457 bodies (`detail`, `code`, `errors[]`, `traceId`); 5xx messages append "Quote this id: <requestId>.";
  `shouldRetryQuery` retries once only for non-ApiError or status >= 500.
- B2.13 `src/lib/api/session-api.ts`: `CurrentUser{userId, fullName, locale, companyId, adminAccess,
  superAdminAccess}`, `fetchCurrentUser()` (GET `/api/session/me`), `userInitials()`, `LOGOUT_PATH='/logout'`,
  `signOut()` -> `window.location.replace('/logout')`.
- B2.14 `src/lib/api/locale-api.ts`: `fetchActiveLocales`, `fetchLocalePreferences`,
  `fetchStoreLocalePreferences` (PUT), `fetchCustomLabels(locale)`.
- B2.15 `src/lib/query-client.ts`: staleTime 30 s, `retry: shouldRetryQuery`, refetchOnWindowFocus false.
- B2.16 `src/lib/session/SessionBootstrap.tsx`: registers the session-expired listener; query
  `['current-user']` (retry false, staleTime 5 min); shows "Loading..." then children with `SessionContext`;
  session-expired screen (`session.expiredTitle`, `session.expiredMessage`, button `session.signInAgain` ->
  reload) on 401/440 or missing userId; exports `useCurrentUser()` (throws outside provider) and
  `CURRENT_USER_QUERY_KEY`.
- B2.17 `src/lib/i18n/index.ts`: i18next + initReactI18next with bundled `en`, `en-GB`, `de`, `es`, `fr`,
  `lng`/`fallbackLng` `en`, `escapeValue:false`, `returnNull:false`; `applyUiLanguage(locale)` changes language
  then merges server custom labels (dotted keys expanded to nested objects) with `addResourceBundle(deep,
  overwrite)`, ignoring label fetch errors.
- B2.18 `src/lib/i18n/LocaleBootstrap.tsx`: query `['locale-preferences']` (retry false), applies
  `uiLanguage` (default `en`) before rendering children; "Loading..." meanwhile; wraps in `I18nextProvider`.
- B2.19 Locales `src/locales/en.json`, `en-GB.json`, `de.json`, `es.json`, `fr.json` hold the same key set
  (all base keys of B2-B8, translated); `src/locales/locales.test.ts` fails when a key is missing in any file.
  Top-level namespaces: `app`, `nav`, `shell`, `session`, `common`, `settings`, `integrations`, `jobs`,
  `history`, `theme`, `projects`, `tasks`, `dashboard`.
- B2.20 Theme: `src/theme/tokens.ts` exports `tokens` (colors background, surface, border, borderStrong,
  textPrimary, textSecondary, textMuted, accent, accentHover, accentSoft, accentBorder, badgeBg, badgeText,
  danger, sidebarBg, sidebarActiveBg, sidebarActiveText, sidebarHoverBg, iconMuted, topNavBorder; radius sm 6 /
  md 8 / lg 12; spacing sidebarWidth 272, sidebarCollapsedWidth 72, topNavHeight 56; shadows card,
  optionSelected; typography fontFamily Inter stack), `tokensToCssVars(t)` producing `--{{cssPrefix}}-*`
  variables (one per token, px for sizes), `applyCssVars(target, t)`.
- B2.21 `src/theme/mui-theme.ts` exports `createAppMuiTheme(t: Tokens)` (palette primary from accent /
  accentHover / accentBorder, background, text, divider, error; typography h4 700 1.75rem, h6 600 1rem;
  shape radius md; overrides CssBaseline body, Accordion, AccordionSummary, AccordionDetails, Tabs indicator,
  Tab (no uppercase, 500, selected accent 600), Badge) and `muiTheme = createAppMuiTheme(tokens)`.
- B2.22 `src/index.css`: `@import 'tailwindcss'`; `@theme` maps Tailwind tokens (`--color-background`,
  `--color-surface`, `--color-border`, `--color-border-strong`, `--color-foreground`,
  `--color-muted-foreground`, `--color-subtle-foreground`, `--color-primary`, `-hover`, `-soft`, `-border`,
  `--color-badge`, `--color-badge-foreground`, `--color-danger`, `--color-sidebar`, `-active`, `-active-fg`,
  `-hover`, `--color-icon-muted`, `--radius-sm|md|lg`, `--font-sans`, `--shadow-card`) to the
  `--{{cssPrefix}}-*` variables; full-height `html, body, #root`; body font/background/colour from variables.
- B2.23 `src/components/ui/`: `badge.tsx`, `button.tsx`, `input.tsx`, `label.tsx`, `radio-group.tsx`,
  `select.tsx`, `textarea.tsx` (cva + `cn` from `src/lib/utils.ts`, radix where the 91040a0 file uses it).
- B2.24 Layout `src/components/layout/`: `AppShell.tsx` (SidebarProvider; Sidebar + column of TopNav and
  scrolling `main`), `sidebar-context.tsx` (`collapsed`, `toggle`, `setCollapsed`, `useSidebar` throws outside
  provider), `Sidebar.tsx`, `TopNav.tsx`, `AppFooter.tsx` (`app.footer.brand` = "{{productName}} · {{productTagline}}").
- B2.25 Sidebar: brand block (tenant logo from B7 or letter tile, product name, `nav.brandSubtitle`), width
  from CSS vars, collapsed shows icons with title tooltips, active item by current path, user avatar +
  name + `nav.roleAdministrator` when admin. Sections and items (only these): Overview: Dashboard `/dashboard`;
  Workspace: Projects `/projects`; Admin (admin only): Background Jobs `/jobs`, Settings `/settings`. No stub
  items.
- B2.26 TopNav: sidebar toggle with tooltip "Expand sidebar"/"Collapse sidebar" (labels via i18n), user menu
  (`session.userMenu`) with `session.signOut`. No fake notification count; no notifications icon.
- B2.27 Common components `src/components/`: `RootErrorBoundary.tsx` (class boundary, `shell.errorTitle`,
  `shell.errorMessage`, `shell.reload`), `common/AppToast.tsx` (severity success|warning|error|info; errors and
  warnings stay longer), `common/TestConnectionResultDialog.tsx` (+ `formatTestConnectionMessage`),
  `common/RouterLinks.tsx`.
- B2.28 Settings `src/components/settings/SettingsPage.tsx`: breadcrumb `{{productName}} > Admin > Settings`,
  title, subtitle, search box filtering groups (`settings.noMatch`), tabs General | Integrations | Theme only.
  `GeneralConfigurationPanel.tsx`: UI language + content language selects from active locales, Reset and Save,
  success/error toasts, invalidates `['locale-preferences']` and re-applies the UI language. Non-admin sees
  General only.
- B2.29 Frontend tests (vitest): `src/lib/api/http.test.ts`, `src/lib/api/session-api.test.ts`,
  `src/locales/locales.test.ts`, plus those named in B4-B8.
- B2.30 Frontend feature folder convention: `src/features/<feature>/{api, components, hooks, lib, types,
  schemas, config}` + `queryKeys.ts` (object of `as const` arrays rooted at one key).

## B3 Deploy, approuter, docs

- B3.1 `approuter/package.json`: name `approuter`, dependency `@sap/approuter` ^11.0.0, start script
  `node node_modules/@sap/approuter/approuter.js`.
- B3.2 `approuter/xs-app.json`: `authenticationMethod: route`, `welcomeFile: index.html`, `logout`
  `{logoutEndpoint:"/logout", logoutPage:"/"}`, routes in this order: `^/{{productSlug}}/webservices/webhook/(.*)$`
  -> `/webservices/webhook/$1` (auth none, csrf off, no-cache); `^/{{productSlug}}/api/public/(.*)$` ->
  `/api/public/$1` (auth none); `^/{{productSlug}}/(.*)$` -> `$1` (xsuaa, csrf off, no-cache); `^/(.*)$` ->
  `localDir: resources` (xsuaa). Destination name `{{productSlug}}` in all backend routes.
- B3.3 `approuter/resources/.gitkeep` only; the frontend build output is copied there by the build
  (`Frontend` build step or CI), never committed.
- B3.4 `approuter/xs-security.json`: `xsappname` `{{productSlug}}`, `tenant-mode` placeholder, one scope with
  `grant-as-authority-to-apps ["$XSAPPNAME(application,xsuaa-{{productSlug}})"]`, `oauth2-configuration`
  `token-validity` 3600 and `redirect-uris` `https://<approuter-host>/login/callback`.
- B3.5 `manifest.yml` app 1 (backend): `name`, `hostname`, `memory`, `buildpack` (Java), `path` to
  `Backend/releases/{{productSlug}}.war`; env `IAS_XSUAA_XCHANGE_ENABLED`, `spring_profiles_active: cloud`,
  `companyID`, `SEND_XFRAMEOPTIONS`, `databaseType`, `JBP_CONFIG_JAVA_OPTS`, `allowedNodeRoles`,
  `disableSchemaValidation`, `logoutEnabled`; services `<postgres-service>`, `<destination-service>`,
  `<xsuaa-service>` (placeholders, never the dev names).
- B3.6 `manifest.yml` app 2 (approuter): `nodejs_buildpack`, `path: approuter`, `memory`, one `route`;
  services xsuaa + postgres; env `TENANT_HOST_PATTERN`, `COMPRESSION` (`enabled true, minSize 256,
  compressResponseMixedTypeContent true`), `destinations` JSON `[{name:"{{productSlug}}", url:"<backend-url>",
  forwardAuthToken:true}]`, `REQUEST_TRACE`, `SEND_XFRAMEOPTIONS`, `INCOMING_CONNECTION_TIMEOUT`,
  `CF_NODEJS_LOGGING_LEVEL`.
- B3.7 Root `.gitignore`: `target/`, `releases/`, `node_modules/`, `dist/`, `approuter/resources/*` except
  `.gitkeep`, `.classpath`, `.project`, `.settings/`, `.temp-*.txt`, `createDDL.jdbc`, `*.log`, `.tanstack/`.
- B3.8 `README.md`: module table (Backend Java 17 / Boot 3.5 WAR; Frontend React 19 / Vite 7 / TanStack
  Router), prerequisites (JDK 17, Maven 3.9, Node 18+, TTCommon 2.0.0 in `~/.m2`), build commands
  (`mvn -pl Backend clean package -DskipTests`, full reactor), auth model table (local mock user via
  `talenteam.dev.loggedInUser.*`; cloud XSUAA JWT; JWT cookie), local run (backend with `-DcompanyID=local`
  because TTCommon reads it as a system property; `npm run dev` on 5173), BTP deploy steps, endpoint table of
  B1/B4-B8. Relative paths only (no `D:\...`), no other product names.

## B4 Background jobs

Scheduling, registry tables and run history are TTCommon (`com.talenteam.common.job`), exposed under
`/webservices/*`. The base adds job classes, an admin page and generic jobs. Source: `dev:Frontend/src/features/job/**`.

- B4.1 Backend job contract: each job is `@Component @Scope("prototype")` extending TTCommon `BaseJob`;
  `execute()` does the work inside try/catch, on failure calls `markJobExceutionStatus(JobExecutionStatus.FAILED)`
  (TTCommon spelling) and `JobContextHolder.getJobContext().addError(...)`, records progress with `addInfo(...)`;
  `getJobName()` returns the fully-qualified class name; `getFileNames()` and `getLogFile()` return null.
- B4.2 TTCommon endpoints the page uses (not re-implemented): `GET /webservices/getJob?jobName=` ->
  `JobSchedulerDTO`; `GET /webservices/getJobResults?jobName=` -> `JobResultDTO[]`; `POST
  /webservices/updateHourlyJobFrequency` (form: enabled, jobName, jobSchedulingType and JobSchedulingType,
  jobFrequency `H:m:s`, jobFrequencyDayOfWeek 0-6, jobFrequencyDayOfMonth 1-31, jobType RECURRING|ADHOC) ->
  JobSchedulerDTO; `POST /webservices/createAdhocJob` (form jobName) -> text, run starts within ~75 s; `POST
  /webservices/updateEnableOrDisableJob` (form jobName, isEnable) -> text. Tables JOB_SCHEDULER, JOB_RESULT,
  JOB_SCHEDULER_AUDIT, CLUSTER_STATUS (node role from `allowedNodeRoles`).
- B4.3 `{{basePackagePath}}/job/SampleHeartbeatJob.java`: generic sample (replaces 91040a0
  `JobFamiliesSyncJob` sample): logs start/finish and `addInfo("Heartbeat completed")`.
- B4.4 `{{basePackagePath}}/audit/job/AuditPartitionMaintenanceJob.java`: creates the next 3 monthly
  partitions of the audit tables (B6.4) and drops partitions older than `AUDIT_RETENTION_MONTHS` (config,
  default 84); idempotent; reports counts with `addInfo`.
- B4.5 User sync (decision: generic platform plumbing, included): `{{basePackagePath}}/user/job/
  AbstractUsersSyncJob.java`, `UsersSyncDailyJob.java`, `UsersSyncFullFetchJob.java`. Behaviour: first call
  `IntegrationConfigService.requireSuccessFactorsReadyForSync()` (409 rules of B5.9); page SF users with
  `SuccessFactorsClientService.getUserDetails(top=200, skip, filter)` until a page is short; per user: find by
  user id, inactivate when SF status is not `t`, map with `UserDetailsService.setUserDetailsVO(api, db,
  inactivate, lastUpdatedUser)`, fetch photo (`getUserPhotoByUserID`, errors logged and skipped), `validate`,
  then `saveAll` users and photos per page; a failed page marks the job FAILED and skips post-processing; after
  all pages (if no failure) `inactivateMissingRecords()` and `JamSuccessFactorsMappingService.cleanUpRecords()`;
  `addInfo` total fetched. Daily: filter `&$filter=lastModifiedDateTime ge datetime'<now-26h>'`, no
  inactivation. Full: no filter; inactivates records not updated for 15 days only if this run updated more than
  0 records in the last 2 hours (else logs an error). `lastUpdatedUser` constants per job.
- B4.6 Strip from user sync: `GlobalAssignmentsRepository` and the LMS custom-column push
  (`GLOBAL_USERS_CUST_COLUMN_UPDATE`, `LearningClientService`, `LearningOAuthClient`, `LMSUserVO`,
  `LMSCustomColumnVO`), and `updateJobProfileId` (job-code -> job-profile mapping, `isJobProfileApiEnabled`).
- B4.7 FE `src/features/job/types/job.ts`: `JobSchedulingType` HOURLY|DAILY|WEEKLY|MONTHLY|MINUTE|RUN_NOW,
  `JobType` RECURRING|ADHOC, `JobExecutionStatus` INITIALIZING|EXECUTING|SUCCESS|FAILED|WARNING, `JobSection`
  inbound|outbound|maintenance, `JobSchedulerDTO` (enabled, jobName, jobSchedulingType, jobFrequency,
  jobFrequencyDayOfWeek, jobFrequencyDayOfMonth, nextExecution, lastExecution, lastExecutionStatus,
  editPermission, viewPermission, allowUpload, jobType), `JobResultDTO` (uuID, jobUUID, jobName, startTimeStr,
  endTimeStr, status, message, fileName, logFileName), `UpdateJobFrequencyPayload`, `JobRegistryEntry{key,
  titleKey, descriptionKey, section, jobName}`.
- B4.8 FE `api/jobApi.ts`: `getJob`, `getJobResults`, `updateJobFrequency`, `createAdhocJob`,
  `updateEnableOrDisableJob` (form-urlencoded posts via a `postForm` helper; `envelope:false`).
- B4.9 FE `config/jobRegistry.ts`: FQCN constants and entries for SampleHeartbeatJob (maintenance),
  AuditPartitionMaintenanceJob (maintenance), UsersSyncDailyJob and UsersSyncFullFetchJob (inbound), using
  `{{basePackage}}` names.
- B4.10 FE `queryKeys.ts` `jobKeys {all:['jobs'], detail(jobName), results(jobName)}`; `lib/jobPolling.ts`
  (poll every 5 s while INITIALIZING/EXECUTING, stop after 10 min); hooks `useJob` (polls while running),
  `useJobResults(jobName,{poll})`, `useCreateAdhocJob`, `useUpdateJobFrequency` (both invalidate detail +
  results), `useEnableDisableJob`.
- B4.11 FE `lib/jobDisplay.ts`: `formatScheduleLabel` ("Every hour", "Every N hours", "Daily at HH:mm UTC",
  "Weekly on <Day> at HH:mm UTC", "Monthly on day N at HH:mm UTC", "Every minute", "Run once", fallback
  "Not scheduled" - all via i18n keys `jobs.schedule.*`), `statusBadgeLabel`, `toJobFrequency` (HOURLY `N:0:0`
  min 1; `HH:mm` -> `H:m:0`), `fromJobFrequency`, `computeJobStats` (runs7d, successful, failed over 7 days).
  Unit test `lib/jobDisplay.test.ts`.
- B4.12 FE `schemas/scheduleSchema.ts` (zod): enabled, jobSchedulingType HOURLY|DAILY|WEEKLY|MONTHLY,
  jobFrequency required when enabled, day of month integer 1-31 for MONTHLY, day of week required for WEEKLY.
- B4.13 FE components: `BackgroundJobsPage.tsx` (breadcrumb, title `jobs.title`, subtitle, ConnectionBanner,
  one JobSection per registry section, schedule/results dialogs, toasts "<title> scheduled to run shortly"),
  `JobSection.tsx`, `JobRow.tsx` (title, description, schedule label, status badge, last run, enable switch,
  buttons Schedule / Results / Run now, busy states), `ScheduleJobDialog.tsx` ("Schedule <title> job",
  enable checkbox, type select, time or hours input, day of week / day of month, Cancel / Save, zod
  validation), `JobResultsDialog.tsx` (table Start time, End time, Status, Comment, File, Log file; Refresh,
  Close; polls while open after Run now), `JobStatsCards.tsx` (Runs (7d), Successful, Failed),
  `ConnectionBanner.tsx` (SuccessFactors connection state from B5 status + link to Settings > Integrations).
  All text through `jobs.*` keys (the source hard-codes English).
- B4.14 Access: `/jobs` route and sidebar item only for admins (`adminAccess || superAdminAccess`); non-admin
  sees the no-permission state.

## B5 Integrations settings

Stored in the TTCommon CONFIGURATION table through `ConfigService` (tenant-scoped, encrypted keys from
`getEncryptedKeys()`, change history in TTCommon CONFIGURATION_AUDIT). Source: `dev:Backend/.../integration/**`,
`dev:Frontend/src/features/integrations/**`. Labour Market Insights (LMI) and LMS-only parts are stripped.

- B5.1 Backend files: `integration/config/IntegrationConfigService.java`, `IntegrationConfigValidator.java`,
  `IntegrationStatusController.java`, `dto/IntegrationStatusResponse.java`;
  `integration/successfactors/controller/SuccessFactorsConnectionController.java`;
  `integration/openai/controller/AzureOpenAiConnectionController.java`;
  `configuration/service/TestConnectivityService.java`, `AzureOpenAiConfiguration.java`;
  optional `integration/openai/service/AzureOpenAiChatClient.java` with a generic
  `complete(List<ChatMessage> messages, int maxTokens)` (no `GenerationMessages`).
- B5.2 Config keys (names only). Group `SUCCESSFACTORS`: SUCCESSFACTORS_INTEGRATION_STATUS,
  SUCCESSFACTORS_LAST_TEST_STATUS, BIZX_API_USER_ID, BIZX_COMPANY_ID, BIZX_BASE_URL, BIZX_API_URL,
  BIZX_IDP_CLIENT_ID, BIZX_IDP_PRIVATE_KEY, LMS_BASE_URL, LMS_ADMIN_ID, LMS_TENANT_ID, LMS_OAUTH_SECRET,
  LMS_DUPLICATE_FIELDS, BIZX_USER_API_DATA_MODEL_FIELDS, SF_CONTENT_LOCALE. Group `AZURE_OPEN_AI_KEYS`:
  AZURE_OPEN_AI_STATUS, AZURE_OPEN_AI_ENDPOINT_URL, AZURE_OPEN_AI_API_KEY, AZURE_OPEN_AI_API_COMPLETIONS_VERSION,
  AZURE_OPEN_AI_COMPLETIONS_MODEL, AZURE_OPEN_AI_COMPLETIONS_URL, AZURE_OPEN_AI_API_CHAT_VERSION,
  AZURE_OPEN_AI_CHAT_MODEL, AZURE_OPEN_AI_CHAT_URL, AZURE_OPEN_AI_LAST_TEST_STATUS, OPENAI_INTEGRATION_STATUS,
  AI_SERVICE_PROVIDER. Group `INTEGRATIONS_STATUS_KEYS`: SUCCESSFACTORS_INTEGRATION_STATUS, AZURE_OPEN_AI_STATUS,
  OPENAI_INTEGRATION_STATUS. Encrypted: BIZX_IDP_CLIENT_ID, BIZX_IDP_PRIVATE_KEY, LMS_OAUTH_SECRET,
  AZURE_OPEN_AI_API_KEY.
- B5.3 Endpoints (ApiResponse envelope): `GET /api/integrations/status` -> `{successfactors:boolean,
  azureOpenai:boolean}` (any signed-in user, no secrets); `GET /api/integrations/successfactors/config` and
  `GET /api/integrations/azure-openai/config` -> `Map<String,String>` of the group + `<SECRET>_PRESENT`
  "true|false" + `secretsPresent` + `lst_upd_tstmp` (latest row update, ISO); `PUT` on the same paths with a
  key/value map -> saved group, messages "SuccessFactors configuration saved" / "Azure OpenAI configuration
  saved"; `POST /api/integrations/successfactors/connection/test?configId=SUCCESSFACTORS` and `POST
  /api/integrations/azure-openai/connection/test?configId=AZURE_OPEN_AI_KEYS` -> `TestConnectionResponse`
  (no envelope).
- B5.4 Secrets are never returned: GET returns `""` for every encrypted key plus its `_PRESENT` flag
  (deliberate change from dev, where `exposeSecrets` returned stored values). PUT stores a secret only when a
  non-blank value differs from the stored one; blank keeps the stored secret.
- B5.5 Permission: every config GET/PUT and test calls `requireCanManageConfiguration()` = `AdminGuard.isAdmin()`
  or TTCommon `PermissionChecker.hasPermission` for menu `navConfiguration` (ADMIN or USER type); else 403
  `FORBIDDEN` "Only administrators can manage integration configuration".
- B5.6 Save SF: validate (Company ID, API User ID, LMS Admin ID, LMS Tenant ID required; BizX Base URL, BizX
  API URL, LMS Base URL valid http(s) URLs; secrets required only when none stored; data-model and duplicate
  fields max 255; secrets max 10000; errors -> 400 `VALIDATION_ERROR` with field errors); copy plain keys
  trimmed; default SUCCESSFACTORS_INTEGRATION_STATUS `ENABLED` and SF_CONTENT_LOCALE `en_US` when absent.
- B5.7 Save Azure: enabled from AZURE_OPEN_AI_STATUS; when enabled require endpoint URL, completions version +
  model + URL, chat version + model + URL, API key unless stored; set AZURE_OPEN_AI_STATUS and
  OPENAI_INTEGRATION_STATUS to ENABLED|DISABLED and AI_SERVICE_PROVIDER to `AZURE_OPEN_AI` or blank.
- B5.8 Test connection: SF calls `SuccessFactorsClientService.testConnection()` ("SUCCESS" = ok); Azure
  requires enabled + key + chat URL + chat API version, rejects portal-shaped keys with a clear message, POSTs a
  tiny chat completion (`max_completion_tokens` 60, temperature 0, header `api-key`) to
  `<chatUrl>?api-version=<v>`; 401/403 -> "Azure OpenAI rejected the API key..."; result stored in
  `<X>_LAST_TEST_STATUS` = SUCCESS|FAILED in its own transaction; unsupported configId -> error key +
  "Unsupported connection test."; error detail never contains the key.
- B5.9 `requireSuccessFactorsReadyForSync()`: 409 `SUCCESSFACTORS_UNTESTED` unless
  SUCCESSFACTORS_LAST_TEST_STATUS is SUCCESS; 409 `SUCCESSFACTORS_NOT_CONFIGURED` when BIZX_COMPANY_ID blank.
- B5.10 Status rules (backend and `lib/integrationEnabled.ts` identical): enabled values ENABLED|TRUE|1|YES|Y,
  disabled DISABLED|FALSE|0|NO|N|OFF (case-insensitive); SF without a flag = enabled when company id and API
  URL are set; Azure falls back to OPENAI_INTEGRATION_STATUS, then endpoint URL + (chat or completions model).
- B5.11 FE files: `api/integrationsConfigApi.ts` (status, SF get/store/test, Azure get/store/test),
  `types.ts` (`IntegrationCategory` 'HR Systems'|'AI Services'; `IntegrationId` 'successfactors'|'azure-openai';
  `INTEGRATIONS` with name, category, descriptionKey, learnMoreKey, keywords, logo accent/initials;
  `INTEGRATION_CATEGORIES` All, HR Systems, AI Services, Disabled), `lib/integrationConfig.ts`
  (`readIntegrationConfig`, secret key lists, `SECRETS_PRESENT_KEY`), `lib/integrationEnabled.ts`, `queryKeys.ts`
  (`integrationsKeys.all|status|azure|successfactors`), components `IntegrationsCatalogue.tsx`,
  `SuccessFactorsConfigDialog.tsx`, `SuccessFactorsLogo.tsx`, `AzureOpenAiConfigDialog.tsx`, `AzureOpenAiLogo.tsx`;
  tests `lib/integrationConfig.test.ts`, `lib/integrationEnabled.test.ts`.
- B5.12 Catalogue UI: search (`integrations.searchPlaceholder`), category chips, cards with logo, name,
  description, status chip Enabled/Disabled/Loading, buttons Settings and Learn more (dialog with category);
  `integrations.noMatch`.
- B5.13 SF dialog: sections BizX (Company ID, API User ID, Base URL, API URL, IDP Client ID secret, IDP Private
  Key secret), LMS (Base URL, Admin ID, Tenant ID, OAuth Secret secret, duplicate fields), User API (data-model
  fields); secret fields show `integrations.secretPlaceholder` when stored; Save / Saving / Cancel; Test
  connection (disabled while dirty) opens TestConnectionResultDialog; field errors from the 400 shown inline.
- B5.14 Azure dialog: Enable switch, Endpoint URL, Authentication (API key secret), Completions (API version,
  model, URL), Chat (API version, model, URL), Save, Test connection as B5.13.

## B6 Audit history (on for every table)

New generic design generalising `dev:Backend/.../companyprofile/**` (CompanyProfileAudit: table
`companyprofile_audit` id identity, version, changed_at, changed_by, field_path, field_label, section, old_value,
new_value; diff of a static field list on save; history paged by distinct version, max 50 per page; view-only;
FE `CompanyProfileHistoryDialog.tsx` with "Load older versions"). The base replaces per-entity audit tables
with one listener-driven change log.

- B6.1 `{{basePackagePath}}/common/domain/AuditableEntity.java`: `@MappedSuperclass`, columns `id` UUID
  (assigned in `@PrePersist` when null), `tenant_id` varchar(100) not null, `created_at` timestamptz not null,
  `created_by` varchar(100) not null, `updated_at` timestamptz not null, `updated_by` varchar(100) not null,
  `version` bigint `@Version` not null, `deleted_at` timestamptz null, `deleted_by` varchar(100) null.
- B6.2 `common/domain/AuditableEntityListener.java` (`@EntityListeners` on AuditableEntity): sets tenant (from
  `UserSessionBean.getCompanyID()`), created/updated by (`getLoggedInUserID()`, or the job name inside a job)
  and timestamps (injected `Clock`); tenant can never change after insert.
- B6.3 Annotations in `audit/annotation/`: `@AuditedEntity(type="PROJECT", labelPrefix="projects.fields")`
  required on every AuditableEntity subclass; `@AuditedEntity(enabled=false, reason="...")` is the only
  opt-out and `reason` must be non-blank; `@NotAudited` (field skipped); `@AuditMasked` (old/new stored as
  `***` - for secrets and personal data); `@AuditLabel("key")` optional per-field label key (default
  `<labelPrefix>.<fieldName>`).
- B6.4 Migration `V002__audit_tables.sql`: `aud_change_log` (id uuid, tenant_id, entity_type varchar(60),
  entity_id uuid, entity_version bigint, action varchar(10) CHECK in CREATE|UPDATE|DELETE|RESTORE, changed_by
  varchar(100), changed_at timestamptz, request_id varchar(64) null, PK (id, changed_at)) and
  `aud_change_field` (id uuid, change_id uuid, changed_at timestamptz, tenant_id, field varchar(100),
  label_key varchar(150), old_value text, new_value text, PK (id, changed_at)), both `PARTITION BY RANGE
  (changed_at)` monthly with a DEFAULT partition and the first 3 months created; indexes
  `ix_aud_change_log_tenant_entity (tenant_id, entity_type, entity_id, changed_at DESC)` and
  `ix_aud_change_field_change (change_id)`. No FK to business tables (history survives deletes).
- B6.5 Entities `audit/domain/AuditChangeLog.java`, `AuditChangeField.java` (do NOT extend AuditableEntity),
  repositories `audit/repository/AuditChangeLogRepository.java`, `AuditChangeFieldRepository.java`.
- B6.6 Capture: `audit/listener/AuditSessionCustomizer.java` (EclipseLink `SessionCustomizer`, registered via
  `spring.jpa.properties.eclipselink.session.customizer` in `application.properties`, or the TTCommon JPA
  property map if TTCommon builds the EntityManagerFactory) adds `AuditDescriptorEventListener` to every descriptor whose class extends
  AuditableEntity and is audited. postInsert -> CREATE with every non-null audited field; postUpdate -> one
  row per changed audited field from the EclipseLink `ObjectChangeSet` (old and new value); an update that sets
  `deleted_at` -> DELETE, that clears it -> RESTORE; postDelete -> DELETE. Changes to `version`, `updated_*`,
  `created_*` alone are not recorded.
- B6.7 Write: captured changes go to a transaction-bound `audit/service/AuditBuffer` and are persisted by
  `AuditWriter` in `TransactionSynchronization.beforeCommit` in the same transaction (rollback = no audit).
  Services never write audit rows by hand.
- B6.8 Value format: strings as is; enums `name()`; dates ISO-8601 UTC; booleans `true|false`; numbers plain;
  associations by id; collections joined with ", "; values over 4000 chars cut with "...".
- B6.9 Read API: `audit/service/AuditHistoryService.history(entityType, entityId, page, size)` (size 1-100,
  default 20, newest first) used by each resource's controller after that resource's own read check (same 404
  for other tenants). Response `HistoryPage {items: HistoryEntry[], page {number, size, totalElements,
  totalPages}}`; `HistoryEntry {changeId, action, entityVersion, changedAt, changedBy, requestId, fields:
  [{field, labelKey, oldValue, newValue}]}`. Endpoint shape `GET /api/v1/<resource>/{id}/history`.
- B6.10 Config key `AUDIT_RETENTION_MONTHS` (default 84) used by B4.4.
- B6.11 Tests: `AuditDescriptorEventListenerTest` (create/update/soft delete/restore/masked/not-audited),
  `AuditHistoryServiceTest` (paging bounds), `AuditedEntityCoverageTest` (every AuditableEntity subclass has
  `@AuditedEntity`; opt-outs have a reason).
- B6.12 FE `src/features/history/`: `api/historyApi.ts` (`fetchHistory(resourcePath, page, size)`),
  `hooks/useHistory.ts` (`useInfiniteQuery`, page size 20), `types.ts`, `queryKeys.ts`
  (`historyKeys.list(resourcePath)`), `components/HistoryPanel.tsx`.
- B6.13 `HistoryPanel` props `{resourcePath, labelPrefix, enabled}`: timeline newest first; each entry shows
  action chip (`history.action.create|update|delete|restore`), who, when (relative + absolute tooltip), table
  field label | old | new (`history.empty.value` for blanks, masked shown as `history.masked`); "Load older"
  (`history.loadOlder` / `history.loadingOlder`); empty (`history.empty`), loading, error with retry,
  no-permission states. Any entity screen gets history by adding one panel.

## B7 Theme manager (new)

Per-tenant branding set by an admin and applied through the CSS tokens of B2.20.

- B7.1 Migration `V003__theme.sql`: table `thm_tenant_themes` (AuditableEntity columns + `primary_color`
  varchar(7) not null CHECK `^#[0-9A-Fa-f]{6}$`, `body_font` varchar(40) not null, `heading_font` varchar(40)
  not null, `logo_data` bytea null, `logo_mime_type` varchar(40) null, `logo_file_name` varchar(120) null,
  `logo_sha256` char(64) null); unique `uq_thm_tenant_themes_tenant (tenant_id) WHERE deleted_at IS NULL`.
- B7.2 Backend `{{basePackagePath}}/theme/{controller/ThemeController, service/ThemeService,
  repository/TenantThemeRepository, domain/TenantTheme, dto/request/UpdateThemeRequest,
  dto/response/ThemeResponse, mapper/ThemeMapper}`; `@AuditedEntity(type="THEME", labelPrefix="theme.fields")`;
  `logo_data` is `@NotAudited`, `logo_sha256` and `logo_file_name` are audited.
- B7.3 Endpoints (problem details, no envelope): `GET /api/v1/theme` (any signed-in user) -> `ThemeResponse
  {id, primaryColor, bodyFont, headingFont, hasLogo, logoUrl, version, updatedAt, updatedBy, isDefault}`
  (defaults when no row: primary `#2563EB`, fonts Inter); `PUT /api/v1/theme` (ADMIN, `If-Match: <version>`)
  body `{primaryColor, bodyFont, headingFont}` -> 200 ThemeResponse; `PUT /api/v1/theme/logo` (ADMIN,
  multipart `file`, PNG/JPEG/WebP only, max 256 KB, max 1024x1024 px) -> ThemeResponse; `GET
  /api/v1/theme/logo` -> image bytes with `ETag` = sha256 and `Cache-Control: private, max-age=3600`, 404 when
  none; `DELETE /api/v1/theme/logo` (ADMIN) -> 204; `DELETE /api/v1/theme` (ADMIN) resets to defaults (soft
  delete) -> 204; `GET /api/v1/theme/history` (ADMIN) -> HistoryPage.
- B7.4 Validation: colour hex; fonts from the allowlist Inter, Roboto, Open Sans, Lato, Source Sans 3, Noto
  Sans, System UI (400 `THEME_FONT_NOT_ALLOWED`); white text on the primary must reach WCAG AA 4.5:1 or the API
  returns `contrastText` dark - never rejects; SVG rejected (415 `THEME_LOGO_TYPE`); size 413 `THEME_LOGO_TOO_LARGE`;
  stale version 409 `CONCURRENT_UPDATE`.
- B7.5 FE `src/lib/theme/ThemeBootstrap.tsx`: query `['theme']`; builds tokens with `deriveTokens(base,
  theme)` from `src/theme/deriveTokens.ts` (accent = primary; accentHover = 12 % darker; accentSoft = 8 % mix
  on white; accentBorder = 45 % mix; badgeBg = accentSoft; badgeText = accent; sidebarActiveBg = accentSoft;
  sidebarActiveText = accent; fontFamily from bodyFont); calls `applyCssVars` and provides
  `createAppMuiTheme(tokens)`; injects the Google Fonts link for non-default fonts; renders with defaults while
  loading or on error (never blocks the app). Unit test `src/theme/deriveTokens.test.ts`.
- B7.6 FE `src/features/theme/{api/themeApi.ts, hooks/useTheme.ts, hooks/useUpdateTheme.ts, queryKeys.ts,
  types.ts, schemas/themeSchema.ts, components/ThemeSettingsPanel.tsx, components/ThemePreview.tsx,
  components/LogoUpload.tsx}`.
- B7.7 Theme tab (Settings > Theme, admin only): primary colour picker + hex input, body and heading font
  selects, logo upload with preview / replace / remove, live preview (sidebar item active, primary button,
  badge, tab, heading) updating before save, contrast warning, Save (disabled until dirty), Reset to default
  (confirm dialog), HistoryPanel for the theme; success/error toasts; 409 opens "changed by someone else -
  reload" dialog. Sidebar brand shows the logo when present.
- B7.8 Only token-driven colours: no component uses a fixed hex except `tokens.ts` defaults.

## B8 Demo Projects + Tasks (new)

End-to-end example of the full stack conventions; removable as one module.

- B8.1 Migration `V004__projects_tasks.sql`: `prj_projects` (AuditableEntity columns + `code` varchar(20) not
  null, `name` varchar(120) not null, `description` varchar(4000) null, `status` varchar(20) not null CHECK in
  DRAFT|ACTIVE|ON_HOLD|COMPLETED|ARCHIVED, `owner_user_id` varchar(100) not null, `start_date` date null,
  `due_date` date null, CHECK `due_date >= start_date`); unique `uq_prj_projects_tenant_code (tenant_id, code)
  WHERE deleted_at IS NULL`; indexes `ix_prj_projects_tenant_status (tenant_id, status, updated_at DESC)`,
  `ix_prj_projects_tenant_name (tenant_id, lower(name))`.
- B8.2 `prj_tasks` (AuditableEntity columns + `project_id` uuid not null `fk_prj_tasks_project` ON DELETE
  RESTRICT, `title` varchar(200) not null, `description` varchar(4000) null, `status` varchar(20) CHECK in
  TODO|IN_PROGRESS|BLOCKED|DONE|CANCELLED, `priority` varchar(10) CHECK in LOW|MEDIUM|HIGH|CRITICAL default
  MEDIUM, `assignee_user_id` varchar(100) null, `due_date` date null, `sort_order` int not null default 0);
  indexes `ix_prj_tasks_project (tenant_id, project_id, status, sort_order)`, `ix_prj_tasks_assignee
  (tenant_id, assignee_user_id, status)`.
- B8.3 Backend `{{basePackagePath}}/projects/{controller/ProjectController, controller/TaskController,
  service/ProjectService, service/TaskService, service/ProjectStatusFlow, service/TaskStatusFlow,
  repository/ProjectRepository, repository/TaskRepository, domain/Project, domain/Task, domain/ProjectStatus,
  domain/TaskStatus, domain/TaskPriority, dto/request/*, dto/response/*, mapper/ProjectMapper (MapStruct),
  mapper/TaskMapper}`; entities `@AuditedEntity(type="PROJECT")` / `("TASK")`.
- B8.4 Project flow: DRAFT->ACTIVE, DRAFT->ARCHIVED, ACTIVE->ON_HOLD, ON_HOLD->ACTIVE, ACTIVE->COMPLETED,
  COMPLETED->ARCHIVED. COMPLETED needs every live task DONE or CANCELLED (422 `PROJECT_HAS_OPEN_TASKS`). Other
  moves 422 `INVALID_STATUS_TRANSITION`. New projects start DRAFT.
- B8.5 Task flow: TODO->IN_PROGRESS, IN_PROGRESS->BLOCKED, BLOCKED->IN_PROGRESS, IN_PROGRESS->DONE,
  DONE->IN_PROGRESS, TODO|IN_PROGRESS|BLOCKED->CANCELLED, CANCELLED->TODO. Tasks of a COMPLETED or ARCHIVED
  project are read-only (422 `PROJECT_READ_ONLY`). New tasks start TODO.
- B8.6 Delete: project soft delete allowed in DRAFT, COMPLETED, ARCHIVED (else 422
  `PROJECT_DELETE_NOT_ALLOWED`) and soft-deletes its tasks in the same transaction (each audited DELETE); task
  soft delete allowed unless project read-only. Deleted rows are invisible to every read.
- B8.7 Access: read = any signed-in user of the tenant; create/update/delete/transition project = ADMIN or
  the project owner; create/update/delete task = ADMIN or project owner; transition task = those plus the
  assignee. Other tenant's ids -> 404. Checked in services, not only in the UI.
- B8.8 Endpoints (`/api/v1`, plain resources, problem-details errors, `If-Match` on PUT/DELETE/transition,
  409 on stale version): `GET /projects?q&status&ownerUserId&page&size&sort` (size max 100, sort
  name|code|dueDate|updatedAt) -> `{items: ProjectSummary[], page}`; `POST /projects` -> 201 + Location,
  Project; `GET /projects/{projectId}`; `PUT /projects/{projectId}`; `DELETE /projects/{projectId}` -> 204;
  `POST /projects/{projectId}/transition {targetStatus}` -> Project; `GET /projects/{projectId}/history`;
  `GET /projects/{projectId}/tasks?status&assigneeUserId&page&size&sort`; `POST /projects/{projectId}/tasks`
  -> 201; `GET|PUT|DELETE /projects/{projectId}/tasks/{taskId}`; `POST
  /projects/{projectId}/tasks/{taskId}/transition`; `GET /projects/{projectId}/tasks/{taskId}/history`.
  Action style decision: `POST /<resource>/{id}/transition`.
- B8.9 Schemas: `Project {id, code, name, description, status, ownerUserId, startDate, dueDate, taskCounts
  {total, open, done}, allowedTransitions[], version, createdAt, createdBy, updatedAt, updatedBy}`;
  `ProjectSummary` (no description); `CreateProjectRequest {code, name, description?, ownerUserId?, startDate?,
  dueDate?}` (owner defaults to caller; code `^[A-Z0-9-]{2,20}$`, 409 `PROJECT_CODE_TAKEN`);
  `UpdateProjectRequest` same minus code; `Task {id, projectId, title, description, status, priority,
  assigneeUserId, dueDate, sortOrder, allowedTransitions[], version, audit fields}`; `CreateTaskRequest`,
  `UpdateTaskRequest`, `TransitionRequest {targetStatus}`.
- B8.10 OpenAPI 3.1 contract `Backend/src/main/resources/openapi/openapi.yaml` (`info.version` 1.0.0) covering
  every `/api/v1` operation of B6-B8 with `operationId` (`listProjects`, `createProject`, `getProject`,
  `updateProject`, `deleteProject`, `transitionProject`, `getProjectHistory`, `listTasks`, `createTask`,
  `getTask`, `updateTask`, `deleteTask`, `transitionTask`, `getTaskHistory`, `getTheme`, `updateTheme`,
  `uploadThemeLogo`, `getThemeLogo`, `deleteThemeLogo`, `resetTheme`, `getThemeHistory`), tags, schemas in
  `components`, examples, `x-roles`, `Problem` schema; lint clean (`npx @redocly/cli lint`). FE types
  generated to `Frontend/src/lib/api/schema.gen.ts` (openapi-typescript, script `generate-api`).
- B8.11 Tests: `ProjectStatusFlowTest`, `TaskStatusFlowTest`, `ProjectServiceTest` (owner/admin access,
  tenant 404, delete rules, open-task rule), `TaskServiceTest`, `ProjectControllerContractTest` (paths, codes,
  problem details vs the OpenAPI file); FE `src/features/projects/lib/statusFlow.test.ts`.
- B8.12 FE `src/features/projects/{api/projectsApi.ts, api/tasksApi.ts, hooks/*, types.ts (from
  schema.gen.ts), queryKeys.ts (projectKeys, taskKeys), schemas/projectSchema.ts, schemas/taskSchema.ts,
  lib/statusFlow.ts, components/ProjectsListPage.tsx, ProjectDetailPage.tsx, ProjectFormDialog.tsx,
  TaskList.tsx, TaskFormDialog.tsx, StatusChip.tsx, TransitionMenu.tsx, ConfirmDeleteDialog.tsx,
  ConflictDialog.tsx}`.
- B8.13 Routes `src/routes/_authenticated/projects.tsx` (`/projects`, search params q, status, page, sort) and
  `src/routes/_authenticated/projects_.$projectId.tsx` (`/projects/$projectId`, search param `tab`).
- B8.14 List page: title, "New project" (permitted users), search, status filter chips, sortable paged table
  (code, name, status chip, owner, due date, open tasks, updated), row click to detail; empty (with create
  call to action), loading skeleton, error with retry, no-permission states.
- B8.15 Detail page: header (code, name, status chip, owner, dates), TransitionMenu listing only
  `allowedTransitions`, Edit (dialog, react-hook-form + zod, server field errors inline), Delete (confirm with
  task count, disabled with reason when not allowed); tabs Overview | Tasks | History (HistoryPanel
  `projects/{id}`); Tasks tab: status filter, New task, rows with priority, assignee, due date, inline
  transition, edit, delete, per-task history drawer; 409 -> ConflictDialog (reload); 404 -> not-found state.
- B8.16 Labels `projects.*`, `tasks.*` (titles, fields, statuses, priorities, actions, errors per code,
  empty states) in all five locale files.

## B9 Conventions

- B9.1 Backend package per feature: `{{basePackagePath}}/<feature>/{controller, service, repository, domain,
  dto/request, dto/response, mapper, exception, job}`; shared code in `common/{api, config, domain, exception,
  security, web}`; TTCommon wiring in `configuration/`.
- B9.2 Constructor injection for new classes (dev style); controllers thin, rules in services; MapStruct
  mappers (`componentModel spring`) for new modules; DTOs never expose entities.
- B9.3 Shell endpoints (`/api/session`, `/api/i18n`, `/api/integrations`) keep the ApiResponse envelope
  (`success`, `message`, `data`, `error{code, detail, requestId, fieldErrors}`); new modules use `/api/v1`,
  plain resources and problem details (B1.15). TTCommon `/webservices/*` are used as they are.
- B9.4 Error codes are UPPER_SNAKE (`VALIDATION_ERROR`, `RESOURCE_NOT_FOUND`, `FORBIDDEN`, `CONCURRENT_UPDATE`,
  `DUPLICATE`, `INTERNAL_ERROR`, feature codes like `PROJECT_CODE_TAKEN`); 500 never carries internals.
- B9.5 Admin check = `adminAccess || superAdminAccess` (AdminGuard); menu-based permission through TTCommon
  `PermissionChecker` where the source used it.
- B9.6 Tables: plural snake_case with module prefix (`prj_`, `thm_`, `aud_`), `ix_`/`uq_`/`fk_` names, no
  quoted identifiers, every business table extends AuditableEntity and is audited (B6).
- B9.7 Frontend features in `src/features/<feature>/{api, components, hooks, lib, types, schemas, config}` +
  `queryKeys.ts`; shared code in `src/lib`, `src/components/{ui, layout, common, settings}`; data access only
  through TanStack Query hooks calling `src/lib/api/http.ts`; forms react-hook-form + zod.
- B9.8 i18n keys: nested camelCase by area (`nav.items.dashboard`, `settings.generalConfiguration.saveSuccess`,
  `integrations.sf.companyId`); interpolation `{{name}}`; no hard-coded user text in components; server custom
  labels override bundled text at runtime.
- B9.9 Styling: Tailwind utilities on `--{{cssPrefix}}-*` tokens and MUI theme from the same tokens; no fixed
  colours in components; focus ring for keyboard only (`:focus-visible`).
- B9.10 Tests: backend JUnit 5 + Mockito without Spring context (MockMvc standalone); frontend vitest for
  `lib/` logic; scratch tests are not committed.
- B9.11 Logs carry `requestId` (MDC); no secrets or personal data in logs or URLs.

## B10 Do not copy

- B10.1 `Backend/target/**` (classes, m2e-wtp MANIFEST.MF, pom copies) - build output committed by mistake.
- B10.2 `Backend/.classpath`, `.project` (root and Backend), `Backend/.settings/**` - Eclipse metadata.
- B10.3 `Backend/.temp-SkillsOS-BE-classpath-arg-*.txt`, `Backend/.temp-skillos-be-classpath-arg-*.txt`.
- B10.4 `test.txt` (root).
- B10.5 `Backend/createDDL.jdbc` - generated by EclipseLink from TTCommon entities.
- B10.6 Empty `package-info.java` stubs: `integration/lightcast/**`, `integration/openai/**` (stub set),
  `integration/successfactors/{domain,dto,exception,mapper,repository,service}`, `jobprofile/**`,
  `common/{exception,mapper}/package-info.java`, `common/package-info.java`, `i18n/package-info.java`,
  `session/package-info.java`, `integration/package-info.java`.
- B10.7 `jobprofile/job/JobFamiliesSyncJob.java` and every job-profile, job-template, job-family, skill,
  approval, translation, company-profile, confidence, generation, publish, LMI/Lightcast, LMS client and
  role-progression class, DTO, SQL script (`db/01`-`db/19`), FE feature (`job-profiles`, `job-templates`,
  `skills-library`, `my-approvals`, `translations`, `company-profile`, `settings` cards for approvals,
  confidence, score weights, skill library, labour market) and their labels.
- B10.8 Frontend `routeTree.gen.ts` (regenerate), `package-lock.json` (regenerate after renaming),
  `approuter/resources/*` build output.
- B10.9 91040a0 placeholders: dashboard fake numbers (128 / 6 / 1,042 / 18), TopNav `UNREAD_COUNT = 2` and
  hard-coded `#7C3AED` badge, Sidebar `stub: true` items and `nav.modeBadge`, Settings operating-mode,
  access-approvals, job-profile and skills-library groups, login form "Dev bypass" text and disabled fields,
  `phase2Placeholder`/`TODO(Phase 2)` texts.
- B10.10 dev defects: `HealthController` `GET /api/public/job-profile-sync` debug endpoint and its job
  injection; `IntegrationConfigService.exposeSecrets` returning stored secret values; 91040a0
  `GlobalExceptionHandler` returning `ex.getMessage()` in 500s; `CacheConfig` entries for lightcast,
  skilldecoder, sapai, jam.
- B10.11 Environment values: dev `manifest.yml` service names and hostnames, any `companyID`, destination URLs
  with real regions, xs-security xsappname/redirect URIs, every value in `application*.properties`, README
  absolute paths (`D:\SkillOS\...`) and "LearningAdmin" references.
- B10.12 Repository AI setup (`.claude`, `.cursor`, `AGENTS.md`, `CLAUDE.md`), `Jenkinsfile`, `dev-jenkinsfile`,
  `JobDSL.groovy`, `postman/` from dev (product tooling, not base).
