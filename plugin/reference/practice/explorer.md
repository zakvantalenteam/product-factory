# Practice pack: explorer

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## OCP Java SE 17: reading Java fast and right
- Endpoint path = the class `@RequestMapping` prefix + the method mapping: grep both parts; a `{id}` path never matches a grep for a literal URL.
- An interface call: grep `implements <Interface>`; with several, `@Primary`, `@Qualifier`, `@Profile` or `@ConditionalOnProperty` decide which bean runs.
- Behaviour outside the method body: `@Transactional`, `@Async`, `@Cacheable`, `@PreAuthorize`, `@Retryable` and `@Validated` act through the proxy; note when the call comes from the same class (then they do not apply).
- Meta-annotations carry behaviour: `@RestController` includes `@ResponseBody`, a custom `@AdminOnly` may hold `@PreAuthorize`; open the annotation.
- Entry points with no caller: `@Scheduled`, `@EventListener`, `@TransactionalEventListener`, `ApplicationRunner`, `CommandLineRunner`, `@PostConstruct`, message listeners, `main`.
- Events: for `publishEvent(new X(...))` grep the listeners that take `X` (`@EventListener` methods and `ApplicationListener<X>`).
- Method references hide callers: grep `Class::method` and `::method` as well as `.method(`.
- Overloads share a name: match the argument count and types before you call something a caller.
- Inherited and default methods: a call may land in a superclass, an override or an interface `default` method; list overrides with `extends <Class>`.
- Package-private classes and methods are used only inside their package: search that folder first.
- A `sealed` type's `permits` clause lists every subtype in one line.
- Records: the accessor is `name()`, not `getName()`; validation lives in the compact constructor.
- Enums: constants may carry their own method bodies; `valueOf(text)` turns request strings into constants, so grep the constant name in quotes too.
- `var` hides the type: read the right-hand side or the called method's return type.
- Streams read like SQL: `filter` is WHERE, `map` is SELECT, `groupingBy` is GROUP BY, `sorted` is ORDER BY; the terminal call decides what comes out.
- `Optional` chains: `orElseThrow` and `orElseGet` mark the missing-value path; follow it for the error case.
- Checked exceptions in a signature (`throws IOException`) mark I/O; a broad `catch (Exception e)` marks where errors are hidden.
- Stack trace names: `Outer$Inner` is a nested class, `lambda$save$0` a lambda inside `save`, `$$SpringCGLIB$$` a Spring proxy around the real class.
- Exceptions to HTTP: `@ControllerAdvice` and `@ExceptionHandler` decide the status a client sees; grep there.
- JPA: the side with `mappedBy` does not own the foreign key, the `@JoinColumn` side does; JPQL uses entity and field names, native SQL uses table and column names.
- Spring Data derived queries: the method name is the query (`findByTenantIdAndStatusIn` filters on two fields); renaming a field breaks it at startup.
- Config keys: `@Value("${a.b-c:default}")` and `@ConfigurationProperties` bind `a.b-c`, `a.bC` and the env var `A_BC`; grep every form, name the key, never the value.
- Generics: in `<T extends Base>` every call on `T` is a call on `Base`.
- Tests document behaviour: `<Class>Test` and `<Class>IT` show inputs and expected outputs; `@WebMvcTest(XController.class)` shows the endpoint's contract.
- TypeScript and JS: a URL built as `/api/${id}` does not match a full-path grep: grep the fixed part.
- (SAP) A UI5 call to `/api/...` goes through the approuter: the first matching `source` regex in `xs-app.json`, its destination and path rewrite, then the backend mapping.
- (SAP) UI5: the `sap.ui.define` dependency array is the import list; `manifest.json` holds routes and data sources; XML view handlers (`press=".onSave"`) point into the controller.

## Traps
- Grep finds no definition for generated code: Lombok methods (`@Getter`, `@RequiredArgsConstructor`), MapStruct `*MapperImpl`, OpenAPI-generated interfaces; read the annotated source, never the generated output.
- Names used as strings are invisible to the call graph: JPQL field names, derived query names, `@JsonProperty`, i18n keys, config keys, reflection; list them as callers.
- Two classes with the same simple name in different packages: check the import before you cite one.
- A `static` import hides the class: grep the method name alone.
- A bean replaced in a profile or test configuration: the code you read may not be the bean that runs.
- Callers outside the repo (n8n workflows, other apps, SuccessFactors callbacks) never show in Grep: name them as not confirmed.
- Comments and old docs drift: cite the code line, not the comment.
- Never quote personal data from seed files, fixtures or logs: name the file and the field.
