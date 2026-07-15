# Creational patterns — lesson content.
# Each pattern: slug, name, category, intent, sections [(h2, prose_html, code)],
# optional "DEMO" marker, wild, avoid, exercise, optional demo.

PATTERNS = [

# ---------------------------------------------------------------- factory method
{
"slug": "factory-method", "name": "Factory Method", "category": "creational",
"intent": "Let callers ask for an object by intent, not by concrete class \u2014 so the decision of <em>which</em> class to instantiate lives in exactly one place.",
"sections": [
("The problem", r"""
<p>Your reporting service exports data in several formats. The knowledge of
<em>which class handles which format</em> has leaked into three different call
sites &mdash; the API handler, the CLI, and the nightly job:</p>""",
r"""
def export_report(rows: list[dict], fmt: str) -> str:
    if fmt == "json":
        exporter = JsonExporter(indent=2)
    elif fmt == "csv":
        exporter = CsvExporter(delimiter=",")
    elif fmt == "xml":
        exporter = XmlExporter(root_tag="report")
    else:
        raise ValueError(f"unknown format: {fmt}")
    return exporter.export(rows)

# ...and the same if/elif chain lives in cli.py and nightly_job.py
"""),
(None, r"""
<p>Adding a Parquet exporter now means hunting down every copy of that chain
&mdash; the classic <em>shotgun surgery</em> smell. Worse, the calling code is
coupled to every concrete exporter and its constructor arguments, so it has to
change whenever any of them does.</p>""", None),
("The pattern", r"""
<p>Factory Method says: put object creation behind a method whose <em>return
type is an abstraction</em>, and let something else &mdash; a subclass, a
registry, a config value &mdash; decide the concrete class. Callers program
against the interface and never say a concrete name again.</p>
<p>The textbook GoF form uses subclassing: a creator class does its work
against the product interface and defers one creation step to subclasses.
Notice how <code>run()</code> never knows which exporter exists:</p>""",
r"""
from typing import Protocol
from abc import ABC, abstractmethod

class Exporter(Protocol):
    def export(self, rows: list[dict]) -> str: ...

class ReportJob(ABC):
    def run(self, rows: list[dict]) -> str:
        exporter = self.create_exporter()   # <- the factory method
        payload = exporter.export(rows)
        self.archive(payload)
        return payload

    @abstractmethod
    def create_exporter(self) -> Exporter: ...

    def archive(self, payload: str) -> None: ...

class JsonReportJob(ReportJob):
    def create_exporter(self) -> Exporter:
        return JsonExporter(indent=2)

class CsvReportJob(ReportJob):
    def create_exporter(self) -> Exporter:
        return CsvExporter(delimiter=",")
"""),
("The Pythonic twist", r"""
<p>In Python, classes are objects you can put in a dict &mdash; so the
subclass-per-product ceremony usually collapses into a <strong>registry</strong>.
This is the form you'll actually ship: one lookup table, one honest error
message, and open/closed extension by adding a line (or a decorator):</p>""",
r"""
EXPORTERS: dict[str, type] = {}

def register(fmt: str):
    def deco(cls):
        EXPORTERS[fmt] = cls
        return cls
    return deco

@register("json")
class JsonExporter:
    def export(self, rows: list[dict]) -> str:
        import json
        return json.dumps(rows, indent=2)

@register("csv")
class CsvExporter:
    def export(self, rows: list[dict]) -> str:
        if not rows:
            return ""
        header = ",".join(rows[0])
        lines = [",".join(str(v) for v in r.values()) for r in rows]
        return "\n".join([header, *lines])

def create_exporter(fmt: str) -> "Exporter":
    try:
        return EXPORTERS[fmt]()
    except KeyError:
        raise ValueError(f"unknown format {fmt!r}, "
                         f"expected one of {sorted(EXPORTERS)}") from None
"""),
"DEMO",
("Alternative constructors are factories too", r"""
<p>Python's idiom for &ldquo;several ways to build the same class&rdquo; is the
<code>@classmethod</code> constructor &mdash; <code>datetime.fromtimestamp()</code>,
<code>dict.fromkeys()</code>, <code>Decimal.from_float()</code>. Same intent,
smallest possible mechanism:</p>""",
r"""
class Config:
    def __init__(self, values: dict):
        self.values = values

    @classmethod
    def from_toml(cls, path: str) -> "Config":
        import tomllib
        with open(path, "rb") as f:
            return cls(tomllib.load(f))

    @classmethod
    def from_env(cls, prefix: str = "APP_") -> "Config":
        import os
        vals = {k[len(prefix):].lower(): v
                for k, v in os.environ.items() if k.startswith(prefix)}
        return cls(vals)
"""),
],
"wild": r"""
<p><code>pathlib.Path("x")</code> secretly hands you a <code>PosixPath</code> or
<code>WindowsPath</code> &mdash; the constructor itself is a factory method choosing
a subclass. <code>logging.getLogger(name)</code> decides whether to create or reuse.
Every <code>@classmethod</code> alternative constructor in the standard library
(<code>datetime.fromisoformat</code>, <code>int.from_bytes</code>) is this pattern
in miniature, and plugin systems like <code>importlib.metadata</code> entry points
are registries at package scale.</p>""",
"avoid": r"""
<p>If there is exactly one concrete class and no credible second one on the
roadmap, <code>JsonExporter()</code> written plainly is better than a factory
&mdash; indirection you don't need is just a longer stack trace. Add the factory
when the <em>second</em> implementation arrives, not before. And don't build a
registry for two entries that change once a decade; an <code>if</code> in one
single place is honest code.</p>""",
"exercise": {
"text": r"""
<p>Refactor this payment module so that adding a provider never touches existing
code. Use a <code>Protocol</code> for the gateway interface and a decorator-based
registry. Then add a fourth provider, <code>"crypto"</code> (fee: flat 1.0),
purely by <em>adding</em> code. Bonus: make <code>create_gateway</code> raise a
helpful error listing valid providers.</p>""",
"code": r"""
def charge(provider: str, amount: float) -> str:
    if provider == "stripe":
        fee = amount * 0.029 + 0.30
        return f"stripe charged {amount + fee:.2f}"
    elif provider == "paypal":
        fee = amount * 0.034
        return f"paypal charged {amount + fee:.2f}"
    elif provider == "bank":
        return f"bank transfer of {amount:.2f} (no fee)"
    raise ValueError(provider)
""",
"hint": r"""<p>Shape: <code>GATEWAYS: dict[str, type] = {}</code>, a
<code>@register("stripe")</code> decorator, each gateway a small class with a
<code>charge(amount) -&gt; str</code> method, and one
<code>create_gateway(provider)</code> lookup. The <code>charge</code> function
shrinks to two lines.</p>"""},
"demo": {
"html": r"""
<div>
  <button id="fm-json" class="on">create_exporter("json")</button>
  <button id="fm-csv">create_exporter("csv")</button>
  <button id="fm-xml">create_exporter("xml")</button>
</div>
<div class="out" id="fm-out"></div>
<p class="note">The caller names an intent; the registry picks the class. Adding a format is one new entry &mdash; no call site changes.</p>""",
"js": r"""
(function () {
  var rows = [{id: 1, name: "Ada"}, {id: 2, name: "Grace"}];
  var registry = {
    json: ["JsonExporter", function (r) { return JSON.stringify(r, null, 2); }],
    csv:  ["CsvExporter",  function (r) { return "id,name\n" + r.map(function (x) { return x.id + "," + x.name; }).join("\n"); }],
    xml:  ["XmlExporter",  function (r) { return "<report>\n" + r.map(function (x) { return "  <row id=\"" + x.id + "\">" + x.name + "</row>"; }).join("\n") + "\n</report>"; }]
  };
  function pick(fmt) {
    var e = registry[fmt];
    document.getElementById("fm-out").textContent =
      ">>> exporter = create_exporter(\"" + fmt + "\")   # -> " + e[0] + "\n>>> exporter.export(rows)\n" + e[1](rows);
    ["json", "csv", "xml"].forEach(function (k) {
      document.getElementById("fm-" + k).classList.toggle("on", k === fmt);
    });
  }
  ["json", "csv", "xml"].forEach(function (k) {
    document.getElementById("fm-" + k).addEventListener("click", function () { pick(k); });
  });
  pick("json");
})();"""},
},

# ---------------------------------------------------------------- singleton
{
"slug": "singleton", "name": "Singleton", "category": "creational",
"intent": "Guarantee a class has one instance and give everyone the same one \u2014 the most famous pattern, and the most abused.",
"sections": [
("The problem", r"""
<p>Your app parses a 2&nbsp;MB YAML config file. Profiling shows it's parsed
forty times per request, because every module that needs a setting calls
<code>Settings()</code> and gets its own copy. Same story with connection
pools: five modules, five pools, database complains about connection limits.
You need <em>one shared instance</em>.</p>""", None),
("The classic solution", r"""
<p>The GoF answer intercepts construction so the second call returns the first
object. In Python that hook is <code>__new__</code>:</p>""",
r"""
class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        print("expensive parse happens once")
        self.values = {"debug": False, "db_url": "postgres://..."}

a = Settings()
b = Settings()
assert a is b   # same object, parsed once
"""),
"DEMO",
("The Pythonic truth", r"""
<p>Here's the part the textbooks skip: <strong>Python already has singletons
&mdash; they're called modules.</strong> A module is created once, cached in
<code>sys.modules</code>, and every <code>import</code> hands out the same
object. So the idiomatic singleton is embarrassingly small:</p>""",
r"""
# settings.py  -- the module IS the singleton
def _load() -> dict:
    print("expensive parse happens once")
    return {"debug": False, "db_url": "postgres://..."}

values = _load()

# anywhere else:
# from settings import values
"""),
(None, r"""
<p>When you need laziness (don't pay the cost until first use) or a reset
button for tests, <code>functools.lru_cache</code> on a getter gives you both
in three lines &mdash; this is my house style for the pattern:</p>""",
r"""
from functools import lru_cache

@lru_cache(maxsize=1)
def get_settings() -> dict:
    print("expensive parse happens once, on first call")
    return {"debug": False, "db_url": "postgres://..."}

# get_settings() is get_settings()  -> True
# get_settings.cache_clear()        -> reset hook for tests
"""),
("The senior warning", r"""
<p>Singleton is really <em>global mutable state wearing a design-pattern
badge</em>. Every consumer is invisibly coupled to it, tests bleed state into
each other, and one day someone needs a second instance (staging + prod
config, one pool per tenant) and the &ldquo;single&rdquo; guarantee becomes
the bug. Reach for it only for genuinely process-wide, read-mostly resources
&mdash; and even then, prefer <em>passing</em> the shared object in
(dependency injection) so the sharing is a choice made at the top of your
program, not a law baked into the class.</p>""", None),
],
"wild": r"""
<p><code>None</code>, <code>True</code>, and <code>Ellipsis</code> are real
singletons &mdash; that's why <code>is None</code> works.
<code>logging.getLogger("x")</code> returns one logger per name.
Django's <code>settings</code> object and SQLAlchemy engine instances are
module-level singletons by convention, exactly as above.</p>""",
"avoid": r"""
<p>Almost everywhere you're tempted. If a function needs the config, pass it
the config &mdash; explicit beats ambient. Avoid it for anything mutable that
tests touch, anything per-tenant or per-request, and never use it just to
avoid typing a parameter. The rule of thumb from many painful code reviews:
a singleton is fine as a <em>cache</em>, dangerous as a <em>channel</em>.</p>""",
"exercise": {
"text": r"""
<p>You inherit the <code>__new__</code>-based <code>DatabasePool</code> below.
First, write a pytest that demonstrates the problem: a test that mutates
<code>pool.connections</code> pollutes the next test. Then refactor to the
<code>lru_cache</code> getter style with a <code>cache_clear()</code> in a
fixture, and show both tests now pass in any order.</p>""",
"code": r"""
class DatabasePool:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.connections = []
        return cls._instance
""",
"hint": r"""<p>Target shape: <code>@lru_cache(maxsize=1) def get_pool() -&gt;
Pool: return Pool()</code> plus a fixture with
<code>get_pool.cache_clear()</code> in its teardown. The class itself becomes
a perfectly ordinary class &mdash; the <em>sharing policy</em> moved out of it.</p>"""},
"demo": {
"html": r"""
<div>
  <button id="sg-single">Settings()</button>
  <button id="sg-normal">dict()</button>
  <button id="sg-reset">reset demo</button>
</div>
<div class="out" id="sg-out">Click Settings() a few times, then dict() a few times.</div>
<p class="note">The singleton hands back the same id() every call; a normal constructor mints a fresh object each time.</p>""",
"js": r"""
(function () {
  var out = document.getElementById("sg-out");
  var singletonId = null, seq = 0, log = [];
  function show() { out.textContent = log.join("\n"); }
  function hexid() { seq += 1; return "0x7f3a9c" + (4000 + seq * 16).toString(16); }
  document.getElementById("sg-single").addEventListener("click", function () {
    var fresh = singletonId === null;
    if (fresh) singletonId = hexid();
    log.push(">>> id(Settings())   # " + singletonId + (fresh ? "   <- created (parse ran)" : "   <- same object, no parse"));
    show();
  });
  document.getElementById("sg-normal").addEventListener("click", function () {
    log.push(">>> id(dict())       # " + hexid() + "   <- brand new object");
    show();
  });
  document.getElementById("sg-reset").addEventListener("click", function () {
    singletonId = null; seq = 0; log = [];
    out.textContent = "Click Settings() a few times, then dict() a few times.";
  });
})();"""},
},

# ---------------------------------------------------------------- builder
{
"slug": "builder", "name": "Builder", "category": "creational",
"intent": "Construct a complex object step by step, validate at the end, and keep the call site readable \u2014 the cure for the telescoping constructor.",
"sections": [
("The problem", r"""
<p>Your HTTP client wrapper started with two parameters. Eighteen months
later:</p>""",
r"""
req = HttpRequest("https://api.example.com/v2/orders", "POST", None,
                  {"page": 1}, 30, 3, True, None, "gzip", False)
# quick: which True is which? what does the second None do?
"""),
(None, r"""
<p>This is the <em>telescoping constructor</em>: every optional feature grew
the signature, call sites became positional soup, and there's nowhere to put
cross-field rules like &ldquo;retries require an idempotent method&rdquo;.
Invalid half-configured objects are one typo away.</p>""", None),
("The pattern", r"""
<p>Builder splits construction from the product: you accumulate configuration
through small, named, chainable steps, and a final <code>build()</code>
validates the whole and returns an immutable result. Nothing half-built ever
escapes.</p>""",
r"""
from dataclasses import dataclass, field

@dataclass(frozen=True)
class HttpRequest:
    url: str
    method: str = "GET"
    headers: dict = field(default_factory=dict)
    timeout: float = 10.0
    retries: int = 0

class RequestBuilder:
    def __init__(self, url: str):
        self._url = url
        self._method = "GET"
        self._headers: dict = {}
        self._timeout = 10.0
        self._retries = 0

    def post(self) -> "RequestBuilder":
        self._method = "POST"
        return self                       # <- returning self enables chaining

    def header(self, key: str, value: str) -> "RequestBuilder":
        self._headers[key] = value
        return self

    def timeout(self, seconds: float) -> "RequestBuilder":
        self._timeout = seconds
        return self

    def retries(self, n: int) -> "RequestBuilder":
        self._retries = n
        return self

    def build(self) -> HttpRequest:
        if self._retries and self._method not in ("GET", "PUT", "DELETE"):
            raise ValueError("retries require an idempotent method")
        return HttpRequest(self._url, self._method, dict(self._headers),
                           self._timeout, self._retries)

req = (RequestBuilder("https://api.example.com/v2/orders")
       .header("Accept", "application/json")
       .timeout(5)
       .build())
"""),
"DEMO",
("The Pythonic twist", r"""
<p>Keyword arguments with defaults already solve the <em>readability</em> half
of this problem &mdash; <code>HttpRequest(url, timeout=5, retries=3)</code>
needs no builder. So in Python, Builder earns its keep only when construction
is genuinely <em>stepwise</em> (config gathered across time or code paths),
needs <em>whole-object validation</em>, or produces <em>immutable</em>
results. For &ldquo;copy with one change&rdquo; on frozen dataclasses,
<code>dataclasses.replace</code> is the built-in answer:</p>""",
r"""
from dataclasses import replace

fast = replace(req, timeout=1.0)   # new frozen object, one field changed
"""),
(None, r"""
<p>The GoF version also includes a <em>Director</em> &mdash; an object that
owns canned recipes of builder steps. In Python that's usually just a plain
function: <code>def signed_json_post(url): return
RequestBuilder(url).post().header(...)...</code>. Don't add a class where a
function will do.</p>""", None),
],
"wild": r"""
<p>SQLAlchemy's <code>select(User).where(...).order_by(...).limit(10)</code> is a
builder producing an immutable query. pandas method chains
(<code>df.query(...).groupby(...).agg(...)</code>), Django QuerySets
(<code>qs.filter(...).exclude(...)</code> &mdash; each step returns a new lazy
queryset), and <code>argparse.ArgumentParser</code> setup are all stepwise
construction with a final &ldquo;materialize&rdquo; step.</p>""",
"avoid": r"""
<p>Fewer than four or five parameters, no cross-field rules, mutable product is
fine? Use keyword arguments &mdash; a builder there is ceremony. Also skip it
when a dict + <code>**kwargs</code> unpack expresses the config naturally
(e.g. loading from TOML straight into a dataclass).</p>""",
"exercise": {
"text": r"""
<p>Design a <code>PizzaBuilder</code> producing a frozen
<code>Pizza(size, crust, toppings, vegan)</code>. Rules enforced in
<code>build()</code>: a vegan pizza rejects <code>"pepperoni"</code> and
<code>"mozzarella"</code>; a <code>"gluten-free"</code> crust only comes in
size <code>"small"</code> or <code>"medium"</code>. Then write the same API as
a plain <code>make_pizza(**kwargs)</code> function with the same validation,
and write two sentences on which you'd ship and why. There's no single right
answer &mdash; the argument is the exercise.</p>""",
"code": None,
"hint": r"""<p>Keep toppings in a list internally but store them as a
<code>tuple</code> on the frozen dataclass (lists aren't hashable and stay
mutable). Validation belongs in exactly one place &mdash; if both versions
share a <code>_validate(size, crust, toppings, vegan)</code> function, you've
found the real design.</p>"""},
"demo": {
"html": r"""
<div>
  <button id="bl-post">.post()</button>
  <button id="bl-header">.header("Accept", "json")</button>
  <button id="bl-timeout">.timeout(5)</button>
  <button id="bl-retries">.retries(3)</button>
</div>
<div class="out" id="bl-out"></div>
<p class="note">Toggle steps to compose the chain. Note how retries + POST fails at build() &mdash; the builder is where cross-field rules live.</p>""",
"js": r"""
(function () {
  var steps = {post: false, header: false, timeout: false, retries: false};
  var chain = {post: ".post()", header: ".header(\"Accept\", \"json\")", timeout: ".timeout(5)", retries: ".retries(3)"};
  function render() {
    var code = "req = (RequestBuilder(\"https://api.example.com\")";
    ["post", "header", "timeout", "retries"].forEach(function (k) {
      if (steps[k]) code += "\n       " + chain[k];
    });
    code += "\n       .build())\n\n";
    if (steps.retries && steps.post) {
      code += "ValueError: retries require an idempotent method";
    } else {
      code += "HttpRequest(method=" + (steps.post ? "\"POST\"" : "\"GET\"") +
              ", headers=" + (steps.header ? "{\"Accept\": \"json\"}" : "{}") +
              ",\n            timeout=" + (steps.timeout ? "5" : "10.0") +
              ", retries=" + (steps.retries ? "3" : "0") + ")   # frozen";
    }
    document.getElementById("bl-out").textContent = code;
    Object.keys(steps).forEach(function (k) {
      document.getElementById("bl-" + k).classList.toggle("on", steps[k]);
    });
  }
  Object.keys(steps).forEach(function (k) {
    document.getElementById("bl-" + k).addEventListener("click", function () {
      steps[k] = !steps[k]; render();
    });
  });
  render();
})();"""},
},

# ---------------------------------------------------------------- abstract factory
{
"slug": "abstract-factory", "name": "Abstract Factory", "category": "creational",
"intent": "Create whole <em>families</em> of related objects that are guaranteed to match \u2014 a factory of factories.",
"sections": [
("The problem", r"""
<p>Your app ships a light theme and a dark theme. Buttons, checkboxes, and
scrollbars each have a variant per theme &mdash; and one Friday deploy, a
screen renders a <code>DarkButton</code> next to a <code>LightCheckbox</code>,
because nothing in the code prevents mixing families:</p>""",
r"""
def build_toolbar(theme: str):
    button = DarkButton() if theme == "dark" else LightButton()
    checkbox = LightCheckbox()   # oops -- forgot the theme check here
    return button, checkbox
"""),
("The pattern", r"""
<p>Abstract Factory bundles the creation of a whole family behind one
interface. The client asks the factory for parts; it can't mismatch them,
because the factory it holds only knows one family:</p>""",
r"""
from typing import Protocol

class Button(Protocol):
    def render(self) -> str: ...

class Checkbox(Protocol):
    def render(self) -> str: ...

class ThemeFactory(Protocol):
    def create_button(self) -> Button: ...
    def create_checkbox(self) -> Checkbox: ...

class LightButton:
    def render(self) -> str: return "[ light button ]"

class LightCheckbox:
    def render(self) -> str: return "[x] light checkbox"

class DarkButton:
    def render(self) -> str: return "[ dark button ]"

class DarkCheckbox:
    def render(self) -> str: return "[x] dark checkbox"

class LightTheme:
    def create_button(self) -> Button: return LightButton()
    def create_checkbox(self) -> Checkbox: return LightCheckbox()

class DarkTheme:
    def create_button(self) -> Button: return DarkButton()
    def create_checkbox(self) -> Checkbox: return DarkCheckbox()

def build_toolbar(theme: ThemeFactory) -> str:
    return theme.create_button().render() + " " + theme.create_checkbox().render()

build_toolbar(DarkTheme())   # consistency is now structural, not disciplinary
"""),
("The Pythonic twist", r"""
<p>A &ldquo;family of constructors&rdquo; doesn't need a class hierarchy in
Python &mdash; a frozen dataclass of callables, or even a module, is a
perfectly good factory. This version is flatter and just as safe:</p>""",
r"""
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class Theme:
    button: Callable[[], "Button"]
    checkbox: Callable[[], "Checkbox"]

LIGHT = Theme(button=LightButton, checkbox=LightCheckbox)
DARK = Theme(button=DarkButton, checkbox=DarkCheckbox)

def build_toolbar(theme: Theme) -> str:
    return theme.button().render() + " " + theme.checkbox().render()
"""),
(None, r"""
<p>The single most valuable use in day-to-day work is <strong>testing</strong>:
a <code>prod</code> family (real mailer, real payment gateway) and a
<code>test</code> family (fakes), selected once at startup. Your business
logic takes the factory and never knows which world it's in &mdash; that's
dependency injection with a family guarantee.</p>""", None),
],
"wild": r"""
<p>DB-API drivers are families: <code>psycopg</code> and <code>sqlite3</code>
each produce matching connections and cursors that must not be mixed.
Matplotlib backends create consistent canvas + renderer sets. Test suites that
swap a <code>ServiceFactory</code> for a <code>FakeServiceFactory</code> use
exactly this shape, as do cloud-provider abstraction layers (an AWS family vs
a GCP family of clients).</p>""",
"avoid": r"""
<p>One family? It's not this pattern &mdash; it's just constructors. One
product per family? That's a plain Factory Method. Abstract Factory earns its
weight only with <em>two or more families</em> of <em>two or more products</em>
whose consistency actually matters; below that threshold it's architecture
cosplay.</p>""",
"exercise": {
"text": r"""
<p>Build an <code>OrderService</code> that takes a service family with
<code>mailer()</code> and <code>payments()</code>. Implement a
<code>ProdServices</code> family (methods can just return objects that print)
and a <code>FakeServices</code> family whose fakes record calls in lists. Write
a test that places an order through <code>FakeServices</code> and asserts one
payment was captured and one email queued &mdash; without monkeypatching
anything.</p>""",
"code": None,
"hint": r"""<p>The assertion target lives on the fake:
<code>fake.mailer_instance.sent == ["order #1 confirmed"]</code>. If your test
needs <code>unittest.mock.patch</code>, the factory isn't being injected
properly &mdash; the whole point is that swapping the family requires zero
patching.</p>"""},
},

# ---------------------------------------------------------------- prototype
{
"slug": "prototype", "name": "Prototype", "category": "creational",
"intent": "Create new objects by copying a pre-configured example instead of building from scratch.",
"sections": [
("The problem", r"""
<p>Spawning an enemy in your game means loading its stats from disk,
resolving its sprite sheet, and computing derived fields &mdash; 40&nbsp;ms of
work. A horde needs 200 goblins that differ only in position and a little
random health jitter. Rebuilding each one from scratch is 8 seconds of
loading screen for objects that are 99% identical.</p>""", None),
("The pattern", r"""
<p>Prototype says: build one fully-configured exemplar, then <em>clone</em> it
and tweak the differences. Python ships the cloning machinery in the
<code>copy</code> module, so the pattern is mostly a thin, intention-revealing
wrapper:</p>""",
r"""
import copy
from dataclasses import dataclass, field

@dataclass
class Enemy:
    kind: str
    health: int
    speed: float
    loot: list = field(default_factory=list)

    def clone(self, **overrides) -> "Enemy":
        new = copy.deepcopy(self)          # deep: loot list is NOT shared
        for k, v in overrides.items():
            setattr(new, k, v)
        return new

# expensive setup happens once:
GOBLIN = Enemy(kind="goblin", health=30, speed=1.2, loot=["dagger"])

horde = [GOBLIN.clone(health=30 + i % 7) for i in range(200)]
horde[0].loot.append("gold")
assert GOBLIN.loot == ["dagger"]           # exemplar untouched
"""),
(None, r"""
<p>A <em>prototype registry</em> completes the pattern: named exemplars looked
up at runtime, so level files can say <code>"goblin"</code> and get a tuned
object without knowing any class:</p>""",
r"""
REGISTRY: dict[str, Enemy] = {
    "goblin": Enemy("goblin", 30, 1.2, ["dagger"]),
    "troll": Enemy("troll", 120, 0.6, ["club", "hide"]),
}

def spawn(kind: str, **overrides) -> Enemy:
    return REGISTRY[kind].clone(**overrides)
"""),
("The Pythonic twist", r"""
<p>Know your three copy depths, because the classic Prototype bug is a
<em>shared mutable field</em> after a shallow copy:</p>""",
r"""
import copy
from dataclasses import replace

a = Enemy("goblin", 30, 1.2, ["dagger"])

s = copy.copy(a)          # shallow: s.loot IS a.loot  (danger)
d = copy.deepcopy(a)      # deep:    fully independent
r = replace(a, health=99) # dataclasses.replace: new object, shallow fields

s.loot.append("cursed ring")
assert a.loot == ["dagger", "cursed ring"]   # the shallow-copy trap, live
"""),
(None, r"""
<p>For fine control, implement <code>__copy__</code> /
<code>__deepcopy__</code> &mdash; e.g. to share an immutable sprite atlas
between clones (cheap) while deep-copying the mutable inventory (safe).
Sharing the heavy immutable parts is where Prototype quietly shades into
Flyweight.</p>""", None),
],
"wild": r"""
<p><code>copy.deepcopy</code> itself, <code>DataFrame.copy()</code> in pandas,
<code>dict(other)</code> / <code>list(other)</code> as idiomatic shallow
clones, <code>datetime.replace(hour=0)</code> and
<code>dataclasses.replace</code> as copy-with-changes. Configuration systems
that start from a default profile and override per environment are prototype
thinking, as is JavaScript's entire object model.</p>""",
"avoid": r"""
<p>If construction is cheap, just call the constructor &mdash; clones make
object provenance harder to trace. Be careful cloning objects holding live
resources (sockets, file handles, locks): copying the wrapper doesn't copy the
resource, and <code>deepcopy</code> on a big object graph can be slower than
rebuilding. When only one or two fields vary, a factory function with defaults
often reads better.</p>""",
"exercise": {
"text": r"""
<p>Implement the <code>Enemy.clone()</code> registry above, then make it fail:
change <code>deepcopy</code> to <code>copy.copy</code> and write a test that
catches the shared-loot bug. Restore <code>deepcopy</code>, then add a heavy
immutable field <code>sprite_atlas: bytes</code> and implement
<code>__deepcopy__</code> so clones <em>share</em> the atlas (assert with
<code>is</code>) while loot stays independent (assert with
<code>is not</code>).</p>""",
"code": None,
"hint": r"""<p><code>__deepcopy__(self, memo)</code> builds the new object
field by field: <code>copy.deepcopy(self.loot, memo)</code> for the list, but
plain <code>self.sprite_atlas</code> for the shared blob. The pair of
assertions <code>a.sprite_atlas is b.sprite_atlas</code> and
<code>a.loot is not b.loot</code> is the whole spec.</p>"""},
},
]
