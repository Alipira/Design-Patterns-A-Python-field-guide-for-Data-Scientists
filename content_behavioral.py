# Behavioral patterns — lesson content.

PATTERNS = [

# ---------------------------------------------------------------- strategy
{
"slug": "strategy", "name": "Strategy", "category": "behavioral",
"intent": "Extract an algorithm that varies behind a common interface, so behavior becomes a value you pass in and swap at runtime.",
"sections": [
("The problem", r"""
<p>An e-commerce <code>Order</code> has been accumulating pricing rules for
two years:</p>""",
r"""
class Order:
    def __init__(self, subtotal: float, customer):
        self.subtotal = subtotal
        self.customer = customer

    def total(self) -> float:
        if self.customer.is_vip:
            return self.subtotal * 0.80
        elif self.customer.loyalty_points > 1000:
            return self.subtotal - self.customer.loyalty_points / 20
        elif self.customer.promo_code == "SUMMER26":
            return self.subtotal * 0.85
        # next sprint: bundles, first-order discounts, flash sales...
        return self.subtotal
"""),
(None, r"""
<p>Three compounding problems: every new rule edits <code>Order</code>, so the
class never stabilizes (a merge-conflict magnet); <code>Order</code> must know
about VIP tiers, loyalty programs, and marketing campaigns &mdash; three other
teams' business; and no rule can be tested without building a whole customer
in exactly the right state.</p>""", None),
("The pattern", r"""
<p>Extract the varying algorithm behind an interface; the context holds one
and delegates. <em>Which</em> algorithm runs becomes a decision made by
whoever creates the order, not by the order itself:</p>""",
r"""
from typing import Protocol

class DiscountStrategy(Protocol):
    def apply(self, subtotal: float) -> float: ...

class NoDiscount:
    def apply(self, subtotal: float) -> float:
        return subtotal

class PercentageDiscount:
    def __init__(self, percent: float):
        self.percent = percent

    def apply(self, subtotal: float) -> float:
        return subtotal * (1 - self.percent / 100)

class LoyaltyPointsDiscount:
    def __init__(self, points: int):
        self.points = points

    def apply(self, subtotal: float) -> float:
        return max(0.0, subtotal - self.points / 20)

class Order:
    def __init__(self, subtotal: float, discount: DiscountStrategy | None = None):
        self.subtotal = subtotal
        self.discount = discount or NoDiscount()

    def total(self) -> float:
        return self.discount.apply(self.subtotal)

order = Order(100.0, PercentageDiscount(10))
order.total()                                  # 90.0
order.discount = LoyaltyPointsDiscount(240)    # swapped at runtime
order.total()                                  # 88.0
"""),
"DEMO",
("The Pythonic twist", r"""
<p>The GoF wrote for C++ and Smalltalk, where an algorithm-you-can-pass-around
had to be wrapped in an object. Python has first-class functions, so a
stateless strategy is just a function:</p>""",
r"""
from typing import Callable

DiscountFn = Callable[[float], float]

def no_discount(subtotal: float) -> float:
    return subtotal

def percentage(percent: float) -> DiscountFn:
    return lambda subtotal: subtotal * (1 - percent / 100)
"""),
(None, r"""
<p>And the small revelation: you've used this pattern for years &mdash;
<code>sorted(words, key=len)</code> injects an interchangeable algorithm into
a stable sorting context. Rule of thumb: a plain function when the strategy is
one stateless operation; a class when it carries configuration or state, has
several related methods, or must be registered and discovered by name.
Neither, when there's only one algorithm and no variation on the horizon.</p>""", None),
],
"wild": r"""
<p><code>sorted(key=...)</code>, <code>min</code>/<code>max</code> key
functions, <code>json.dumps(default=...)</code>, <code>re.sub</code> with a
callable replacement. Django's pluggable authentication backends and DRF's
authentication classes are the class-based form; Python's pluggable hash
randomization and <code>functools.cmp_to_key</code> live in the same family.</p>""",
"avoid": r"""
<p>One algorithm, or a two-branch <code>if</code> that will never grow: keep
the <code>if</code> &mdash; it's honest code. Strategy applied preemptively is
the most common symptom of pattern fever; the pattern is a refactoring target
you move toward when variation actually appears.</p>""",
"exercise": {
"text": r"""
<p>The exercise from our chat, for the record. Refactor to Strategy twice
&mdash; once with <code>Protocol</code>-based classes, once with plain
functions &mdash; decide which you'd ship and why. Then add drone delivery
(flat 8.0, only valid under 1.5&nbsp;kg) <em>without editing any existing
strategy or the calculator</em>. That last constraint is the whole exam.</p>""",
"code": r"""
class ShippingCalculator:
    def cost(self, order) -> float:
        if order.shipping == "standard":
            return 5.0 if order.weight_kg < 2 else 5.0 + order.weight_kg * 1.2
        elif order.shipping == "express":
            return 15.0 + order.weight_kg * 2.5
        elif order.shipping == "pickup":
            return 0.0
        raise ValueError(order.shipping)
""",
"hint": r"""<p>Pair this with a registry (see Factory Method) so
<code>"drone"</code> is one new class plus one <code>@register</code> line.
The drone's weight rule lives inside the drone strategy &mdash; validation is
part of the algorithm that varies.</p>"""},
"demo": {
"html": r"""
<div>
  <button id="st-none" class="on">NoDiscount()</button>
  <button id="st-pct">PercentageDiscount(10)</button>
  <button id="st-pts">LoyaltyPointsDiscount(240)</button>
</div>
<div class="out" id="st-out"></div>
<p class="note">Same object, same total() call &mdash; only the plugged-in strategy changes. The Order class is never edited.</p>""",
"js": r"""
(function () {
  var strategies = {
    none: {label: "NoDiscount()", fn: function (s) { return s; }},
    pct:  {label: "PercentageDiscount(10)", fn: function (s) { return s * 0.9; }},
    pts:  {label: "LoyaltyPointsDiscount(240)", fn: function (s) { return Math.max(0, s - 12); }}
  };
  function pick(k) {
    var s = strategies[k];
    document.getElementById("st-out").textContent =
      ">>> order = Order(100.0, " + s.label + ")\n>>> order.total()\n" + s.fn(100).toFixed(1);
    Object.keys(strategies).forEach(function (id) {
      document.getElementById("st-" + id).classList.toggle("on", id === k);
    });
  }
  Object.keys(strategies).forEach(function (k) {
    document.getElementById("st-" + k).addEventListener("click", function () { pick(k); });
  });
  pick("none");
})();"""},
},

# ---------------------------------------------------------------- observer
{
"slug": "observer", "name": "Observer", "category": "behavioral",
"intent": "Let objects react to another object's events without the publisher knowing who's listening \u2014 the pattern inside every event system you've ever used.",
"sections": [
("The problem", r"""
<p>When an order is placed, four things must happen &mdash; and the order
service currently does all of them personally:</p>""",
r"""
class OrderService:
    def place_order(self, order) -> None:
        self.save(order)
        EmailService().send_receipt(order)        # coupling #1
        AnalyticsClient().track("order", order)   # coupling #2
        InventoryService().reserve(order)         # coupling #3
        # next sprint: loyalty points, fraud check, webhooks...

    def save(self, order) -> None: ...
"""),
(None, r"""
<p><code>place_order</code> has become a bulletin board of other teams'
requirements. Every new reaction edits it, it can't be tested without four
services, and the analytics team files a ticket against <em>your</em> module
to change <em>their</em> tracking.</p>""", None),
("The pattern", r"""
<p>Invert the dependency: the publisher keeps a list of anonymous subscribers
and notifies them; subscribers register themselves. The publisher's last
coupling to its consumers disappears:</p>""",
r"""
from typing import Protocol

class Observer(Protocol):
    def update(self, event: str, payload) -> None: ...

class Publisher:
    def __init__(self):
        self._observers: list[Observer] = []

    def attach(self, obs: Observer) -> None:
        self._observers.append(obs)

    def detach(self, obs: Observer) -> None:
        self._observers.remove(obs)

    def notify(self, event: str, payload) -> None:
        for obs in list(self._observers):     # copy: observers may detach
            obs.update(event, payload)

class OrderService(Publisher):
    def place_order(self, order) -> None:
        self.save(order)
        self.notify("order_placed", order)    # done. no names, no coupling.

    def save(self, order) -> None: ...

class EmailReceipts:
    def update(self, event: str, payload) -> None:
        print(f"emailing receipt for {payload}")

orders = OrderService()
orders.attach(EmailReceipts())
"""),
"DEMO",
("The Pythonic twist", r"""
<p>Functions being first-class flattens this too: the subscriber list is
usually just a list of callables, and that's the whole EventEmitter every
framework ships:</p>""",
r"""
from collections import defaultdict
from typing import Callable

class EventBus:
    def __init__(self):
        self._subs: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event: str, fn: Callable) -> None:
        self._subs[event].append(fn)

    def emit(self, event: str, *args, **kwargs) -> None:
        for fn in list(self._subs[event]):
            try:
                fn(*args, **kwargs)
            except Exception as e:            # one bad listener
                print(f"observer error: {e!r}")   # must not kill the rest
"""),
(None, r"""
<p>Three production lessons baked into those few lines. Iterate over a
<em>copy</em>, because handlers that unsubscribe themselves mid-notify
otherwise skip their neighbor. Isolate errors, because the email service
being down should not stop inventory reservation. And mind lifetimes: a
subject holding strong references keeps observers alive forever &mdash; for
long-lived publishers, register bound methods via
<code>weakref.WeakMethod</code> or provide disciplined <code>detach</code>
calls, or you've built a slow memory leak.</p>""", None),
],
"wild": r"""
<p>Django signals (<code>post_save</code>), Qt's signals and slots,
<code>asyncio</code>'s <code>add_done_callback</code>, every GUI
<code>bind()</code>/<code>addEventListener</code>, file-system watchers, and
&mdash; scaled up to architecture &mdash; pub/sub systems like Kafka or Redis
channels: same pattern, network-sized.</p>""",
"avoid": r"""
<p>Observer trades coupling for <em>visibility</em>: control flow becomes
&ldquo;spooky action at a distance,&rdquo; and debugging &ldquo;what changed
this?&rdquo; means hunting subscribers. Avoid it when there's exactly one
consumer (call it), when reactions must happen in a guaranteed order
(publish/subscribe promises none), or when observers trigger events that
trigger observers &mdash; feedback cascades are this pattern's signature
outage.</p>""",
"exercise": {
"text": r"""
<p>Extend the <code>EventBus</code> above with: <code>off(event, fn)</code>
to unsubscribe; <code>once(event, fn)</code> that auto-unsubscribes after the
first delivery (careful &mdash; the naive version mutates the list during
iteration); and error isolation that <em>collects</em> exceptions and raises
a single <code>BatchError(errors)</code> after all observers ran. Write tests
proving a self-unsubscribing handler doesn't make its neighbor get skipped.</p>""",
"code": None,
"hint": r"""<p><code>once</code> wraps <code>fn</code> in a closure that
calls <code>self.off(event, wrapper)</code> then <code>fn(...)</code> &mdash;
note it must unsubscribe the <em>wrapper</em>, which means the wrapper needs
a reference to itself: define it with <code>def</code>, not
<code>lambda</code>. The neighbor-skipping test: subscribe two handlers, make
the first a <code>once</code>, emit, assert both ran.</p>"""},
"demo": {
"html": r"""
<div>
  <button id="ob-tick">feed.publish(next_price)</button>
  <button id="ob-chart" class="on">chart subscribed</button>
  <button id="ob-sms">sms alerts off</button>
</div>
<div class="out" id="ob-out">Publish a few prices, then toggle subscribers between ticks.</div>
<p class="note">The feed never names its subscribers &mdash; it just walks the list. Attach and detach at runtime and publish again.</p>""",
"js": r"""
(function () {
  var price = 100.0, chart = true, sms = false;
  var out = document.getElementById("ob-out");
  var log = [];
  document.getElementById("ob-tick").addEventListener("click", function () {
    price = Math.max(1, price + (Math.random() * 8 - 4));
    var p = price.toFixed(2);
    var lines = [">>> feed.publish(" + p + ")"];
    if (chart) lines.push("    ChartDisplay.update(" + p + ")   # redraws");
    if (sms) lines.push("    SmsAlerts.update(" + p + ")     # texts on-call");
    if (!chart && !sms) lines.push("    # no observers attached -- publish is a no-op");
    log = log.concat(lines).slice(-9);
    out.textContent = log.join("\n");
  });
  function label() {
    var c = document.getElementById("ob-chart"), s = document.getElementById("ob-sms");
    c.textContent = chart ? "chart subscribed" : "chart detached";
    c.classList.toggle("on", chart);
    s.textContent = sms ? "sms alerts on" : "sms alerts off";
    s.classList.toggle("on", sms);
  }
  document.getElementById("ob-chart").addEventListener("click", function () { chart = !chart; label(); });
  document.getElementById("ob-sms").addEventListener("click", function () { sms = !sms; label(); });
  label();
})();"""},
},

# ---------------------------------------------------------------- command
{
"slug": "command", "name": "Command", "category": "behavioral",
"intent": "Turn an action into an object, so it can be queued, logged, replayed \u2014 and undone.",
"sections": [
("The problem", r"""
<p>Your editor needs undo. But &ldquo;insert text&rdquo; currently happens as
a direct method call from six places &mdash; a menu item, a hotkey, a paste
handler, a macro player&hellip; There is no <em>thing</em> that represents
&ldquo;what just happened,&rdquo; so there's nothing to put on an undo stack,
nothing to log, and nothing a macro could replay.</p>""", None),
("The pattern", r"""
<p>Reify the action: each operation becomes an object that knows how to
<code>execute()</code> itself and how to <code>undo()</code> itself,
capturing everything it needs. Invokers (buttons, hotkeys) just hold
commands; a history stack makes undo almost free:</p>""",
r"""
from typing import Protocol

class Command(Protocol):
    def execute(self) -> None: ...
    def undo(self) -> None: ...

class Document:
    def __init__(self):
        self.text = ""

class InsertText:
    def __init__(self, doc: Document, pos: int, s: str):
        self.doc, self.pos, self.s = doc, pos, s

    def execute(self) -> None:
        self.doc.text = self.doc.text[:self.pos] + self.s + self.doc.text[self.pos:]

    def undo(self) -> None:
        self.doc.text = self.doc.text[:self.pos] + self.doc.text[self.pos + len(self.s):]

class DeleteRange:
    def __init__(self, doc: Document, start: int, end: int):
        self.doc, self.start, self.end = doc, start, end
        self._removed = ""                       # captured for undo

    def execute(self) -> None:
        self._removed = self.doc.text[self.start:self.end]
        self.doc.text = self.doc.text[:self.start] + self.doc.text[self.end:]

    def undo(self) -> None:
        self.doc.text = self.doc.text[:self.start] + self._removed + self.doc.text[self.start:]

class Editor:
    def __init__(self, doc: Document):
        self.doc = doc
        self._history: list[Command] = []

    def do(self, cmd: Command) -> None:
        cmd.execute()
        self._history.append(cmd)

    def undo(self) -> None:
        if self._history:
            self._history.pop().undo()

doc = Document()
ed = Editor(doc)
ed.do(InsertText(doc, 0, "hello world"))
ed.do(DeleteRange(doc, 5, 11))
ed.undo()                     # ' world' comes back
"""),
(None, r"""
<p>Look at <code>DeleteRange</code> closely: <code>execute()</code> stashes
what it destroyed so <code>undo()</code> can restore it. That's the heart of
the pattern &mdash; a command captures not just <em>what to do</em> but
<em>enough state to reverse it</em>.</p>""", None),
("The Pythonic twist", r"""
<p>If you only need &ldquo;an action as a value&rdquo; &mdash; queue it, defer
it, pass it around &mdash; a closure or <code>functools.partial</code>
<em>is</em> a command, and Python code uses them constantly without the name.
The class form earns its keep exactly when you need the second method:
<code>undo()</code>, or serialization for a task queue, or introspection for
logging. A pleasant middle ground is a frozen dataclass command &mdash; free
<code>__repr__</code> for your audit log, free equality for tests.</p>""",
r"""
from functools import partial

queue = []
queue.append(partial(print, "deferred hello"))   # a command, informally
for task in queue:
    task()
"""),
],
"wild": r"""
<p>Every task queue (Celery serializes command objects to workers), database
migrations with <code>upgrade()</code>/<code>downgrade()</code>, GUI
frameworks' QAction/menu items, transactional outboxes, macro recording, and
<code>functools.partial</code> whenever code hands an action to an executor
(<code>ThreadPoolExecutor.submit</code> takes commands all day).</p>""",
"avoid": r"""
<p>No undo, no queue, no log, no macro? Then a command class is a function
call wearing a costume &mdash; just call the function. Beware command-class
explosions for trivial operations, and know the memory tradeoff: commands
that capture large state for undo shade into Memento territory, where
snapshotting may be simpler than reversing.</p>""",
"exercise": {
"text": r"""
<p>Build a <code>BankAccount</code> with <code>Deposit(amount)</code> and
<code>Withdraw(amount)</code> commands, plus an invoker supporting
<code>undo()</code> <em>and</em> <code>redo()</code> (two stacks; a fresh
<code>do()</code> clears the redo stack &mdash; think about why). Then add
<code>Transfer(src, dst, amount)</code> as a <em>composite command</em> that
executes a Withdraw and a Deposit and undoes them in reverse order. Test:
deposit 100, withdraw 30, undo, undo, redo &mdash; assert the balance at
every step.</p>""",
"code": None,
"hint": r"""<p>Redo is just <code>cmd = self._redo.pop(); cmd.execute();
self._undo.append(cmd)</code>. The composite:
<code>execute()</code> runs children in order, <code>undo()</code> runs
<code>reversed(self.children)</code> &mdash; reverse order matters the moment
commands interact.</p>"""},
},

# ---------------------------------------------------------------- template method
{
"slug": "template-method", "name": "Template Method", "category": "behavioral",
"intent": "Fix the skeleton of an algorithm in a base class and let subclasses fill in the steps \u2014 \u201cdon\u2019t call us, we\u2019ll call you.\u201d",
"sections": [
("The problem", r"""
<p>Three data importers &mdash; CSV, JSON, and a REST API &mdash; were written
by three people. Each one fetches, parses, validates, and saves&hellip; in
three slightly different orders, with the deduplication fix applied to two of
them and the retry fix to a different two. The <em>skeleton</em> is shared;
only the parsing genuinely differs. Copy-paste has turned one algorithm into
three drifting ones.</p>""", None),
("The pattern", r"""
<p>Put the invariant skeleton in a base class method that calls a mix of
concrete steps, abstract steps (subclasses must fill), and optional hooks
(subclasses may override). The base class owns the order forever:</p>""",
r"""
from abc import ABC, abstractmethod

class Importer(ABC):
    def run(self, source: str) -> int:          # the template method
        raw = self.fetch(source)
        records = self.parse(raw)               # <- varies (abstract)
        records = [r for r in records if self.is_valid(r)]
        self.post_process(records)              # <- hook (optional)
        return self.save(records)

    def fetch(self, source: str) -> str:
        with open(source) as f:
            return f.read()

    @abstractmethod
    def parse(self, raw: str) -> list[dict]: ...

    def is_valid(self, record: dict) -> bool:   # sensible default
        return bool(record.get("id"))

    def post_process(self, records: list[dict]) -> None:
        pass                                    # hook: default is nothing

    def save(self, records: list[dict]) -> int:
        print(f"saving {len(records)} records")
        return len(records)

class CsvImporter(Importer):
    def parse(self, raw: str) -> list[dict]:
        header, *rows = raw.strip().splitlines()
        keys = header.split(",")
        return [dict(zip(keys, row.split(","))) for row in rows]

class JsonImporter(Importer):
    def parse(self, raw: str) -> list[dict]:
        import json
        return json.loads(raw)
"""),
(None, r"""
<p>The inversion is the point: subclasses don't call the framework, the
framework calls them &mdash; the Hollywood principle. Fix deduplication once
in <code>run()</code> and every importer, present and future, gets it.</p>""", None),
("The Pythonic twist", r"""
<p>This is the one classic pattern where inheritance is the mechanism rather
than a smell &mdash; but Python gives you a composition alternative: pass the
varying step in as a function, and the &ldquo;base class&rdquo; becomes a
plain function. Same skeleton, no hierarchy:</p>""",
r"""
from typing import Callable

def run_import(source: str, parse: Callable[[str], list[dict]]) -> int:
    with open(source) as f:
        raw = f.read()
    records = [r for r in parse(raw) if r.get("id")]
    print(f"saving {len(records)} records")
    return len(records)
"""),
(None, r"""
<p>Choosing between them: Template Method when there are <em>several</em>
related steps and hooks that belong together, or when a framework wants a
class to register; the function version when exactly one step varies &mdash;
at which point you've rediscovered Strategy, which is precisely the
relationship between these two patterns.</p>""", None),
],
"wild": r"""
<p><code>unittest.TestCase</code> is the canonical one: the framework's
skeleton calls your <code>setUp</code>, <code>test_*</code>,
<code>tearDown</code>. Django class-based views (<code>get_context_data</code>
and friends), <code>http.server.BaseHTTPRequestHandler.do_GET</code>,
<code>cmd.Cmd</code>, and asyncio's protocol callbacks
(<code>connection_made</code>, <code>data_received</code>) all hand you hooks
inside a fixed skeleton.</p>""",
"avoid": r"""
<p>When the steps vary <em>independently</em> (parse varies AND save varies
AND validation varies), one inheritance axis can't express the combinations
&mdash; compose strategies instead. Deep template hierarchies develop the
fragile-base-class disease: a change to the skeleton silently breaks
subclasses you forgot exist. Keep it one level deep and the skeleton short.</p>""",
"exercise": {
"text": r"""
<p>Implement the <code>Importer</code> above plus an <code>ApiImporter</code>
whose <code>fetch</code> is also overridden (return a canned JSON string;
no network). Give it a <code>post_process</code> hook that lowercases every
record's keys. Then rewrite the whole thing as the composition version with
<em>two</em> injected functions (<code>parse</code>, <code>validate</code>)
and answer in two sentences: at how many varying steps does the class version
start winning?</p>""",
"code": None,
"hint": r"""<p>There's no universally right answer, but a defensible one:
with one varying step, functions win outright; at two or three <em>related</em>
steps plus a hook, the class starts paying for itself because the steps share
state via <code>self</code> instead of threading arguments.</p>"""},
},

# ---------------------------------------------------------------- composite is structural; state next
{
"slug": "state", "name": "State", "category": "behavioral",
"intent": "Give an object different behavior per lifecycle state by making each state a class \u2014 the if-ladder\u2019s dignified retirement.",
"sections": [
("The problem", r"""
<p>An order moves through a lifecycle: new &rarr; paid &rarr; shipped &rarr;
delivered, with cancellation rules that differ at every stage. As a string
field, every method becomes a ladder &mdash; and the ladders multiply and
drift:</p>""",
r"""
class Order:
    def __init__(self):
        self.status = "new"

    def cancel(self) -> None:
        if self.status == "new":
            self.status = "cancelled"
        elif self.status == "paid":
            self.status = "cancelled"   # ...and refund? someone forgot
        elif self.status == "shipped":
            raise ValueError("can't cancel a shipped order")
        # 'delivered'? falls through silently. bug.
"""),
("The pattern", r"""
<p>Make each state a class that implements the behavior valid <em>in that
state</em> &mdash; including which transitions are legal. The context
delegates everything and just holds the current state object:</p>""",
r"""
class InvalidTransition(Exception):
    pass

class OrderState:
    name = "base"

    def pay(self, order) -> None:
        raise InvalidTransition(f"can't pay from {self.name}")

    def ship(self, order) -> None:
        raise InvalidTransition(f"can't ship from {self.name}")

    def cancel(self, order) -> None:
        raise InvalidTransition(f"can't cancel from {self.name}")

class New(OrderState):
    name = "new"
    def pay(self, order) -> None:
        order.state = Paid()
    def cancel(self, order) -> None:
        order.state = Cancelled()

class Paid(OrderState):
    name = "paid"
    def ship(self, order) -> None:
        order.state = Shipped()
    def cancel(self, order) -> None:
        print("issuing refund")               # state-specific behavior
        order.state = Cancelled()

class Shipped(OrderState):
    name = "shipped"

class Cancelled(OrderState):
    name = "cancelled"

class Order:
    def __init__(self):
        self.state: OrderState = New()

    def pay(self) -> None: self.state.pay(self)
    def ship(self) -> None: self.state.ship(self)
    def cancel(self) -> None: self.state.cancel(self)

o = Order()
o.pay()
o.cancel()          # prints 'issuing refund'
# o.ship()          # InvalidTransition: can't ship from cancelled
"""),
(None, r"""
<p>Every behavior now lives with the state it belongs to, illegal moves fail
loudly by default (the base class), and adding a <code>Returned</code> state
is one new class &mdash; not an edit to five ladders.</p>""", None),
("The Pythonic twist", r"""
<p>For machines where transitions are the whole story and per-state
<em>behavior</em> is thin, a table beats a class family &mdash; data over
code:</p>""",
r"""
TRANSITIONS = {
    ("new", "pay"): "paid",
    ("new", "cancel"): "cancelled",
    ("paid", "ship"): "shipped",
    ("paid", "cancel"): "cancelled",
    ("shipped", "deliver"): "delivered",
}

class Order:
    def __init__(self):
        self.status = "new"

    def fire(self, event: str) -> None:
        try:
            self.status = TRANSITIONS[(self.status, event)]
        except KeyError:
            raise InvalidTransition(f"{event!r} invalid in {self.status!r}") from None
"""),
(None, r"""
<p>The honest heuristic: table for transition-heavy/behavior-light machines,
state classes once states carry real logic (the refund above). State vs
Strategy, since they're structurally identical: strategies are interchangeable
peers that don't know each other; states know their neighbors and drive their
own succession.</p>""", None),
],
"wild": r"""
<p>TCP connection lifecycles, parsers and lexers (tokenizer modes), game AI
(patrol/chase/flee), payment and order lifecycles in every commerce system,
<code>asyncio.Task</code>'s pending/running/done, and workflow engines. The
<code>transitions</code> library on PyPI is the table form productized.</p>""",
"avoid": r"""
<p>Two or three states with trivial rules: an <code>Enum</code> field and a
couple of honest <code>if</code>s is less machinery. The class family's cost
is boilerplate and object churn; don't pay it until states have real,
divergent behavior. And resist state objects that accumulate mutable fields
&mdash; keep them stateless singletons where possible so they can be
shared.</p>""",
"exercise": {
"text": r"""
<p>Model a vending machine: states <code>Idle</code>, <code>HasCoin</code>,
<code>Dispensing</code>; events <code>insert_coin</code>,
<code>select_item</code>, <code>refund</code>. Rules: selecting from Idle
raises; refund from HasCoin returns the coin and goes Idle; Dispensing
auto-returns to Idle after dispensing. Implement with state classes, then
again with a transition table, and note which version made the
&ldquo;auto-return after dispensing&rdquo; rule easier to express &mdash;
that's the classifying question for your future machines.</p>""",
"code": None,
"hint": r"""<p>Auto-return is awkward in a pure table (it's behavior, not
just a transition) &mdash; in the class version, <code>Dispensing.enter()</code>
or the <code>select_item</code> handler can do work <em>then</em> transition.
When you find yourself wanting entry/exit actions, you've outgrown the
table.</p>"""},
},

# ---------------------------------------------------------------- proxy is structural; chain next
{
"slug": "chain-of-responsibility", "name": "Chain of Responsibility", "category": "behavioral",
"intent": "Pass a request along a line of handlers until one deals with it \u2014 the shape of every middleware stack.",
"sections": [
("The problem", r"""
<p>Incoming support tickets should be answered by the bot if possible,
escalated to tier 1, then tier 2, then engineering. The routing logic is one
function that knows every team's criteria &mdash; and every team edits
it weekly:</p>""",
r"""
def route(ticket) -> str:
    if ticket.kind == "faq":
        return "bot answered"
    elif ticket.kind in ("billing", "login") and not ticket.urgent:
        return "tier1 handled"
    elif ticket.kind in ("billing", "login"):
        return "tier2 handled"
    elif ticket.kind == "bug":
        return "engineering ticket filed"
    return "nobody could help"
"""),
("The pattern", r"""
<p>Give each handler two options: deal with the request, or pass it to the
next handler. Assembly of the chain &mdash; who's in it, in what order &mdash;
becomes configuration, separated from each handler's private logic:</p>""",
r"""
class Handler:
    def __init__(self):
        self._next: "Handler | None" = None

    def set_next(self, handler: "Handler") -> "Handler":
        self._next = handler
        return handler                      # enables chaining setup

    def handle(self, ticket) -> str | None:
        if self._next:
            return self._next.handle(ticket)
        return None                         # fell off the end

class Bot(Handler):
    def handle(self, ticket) -> str | None:
        if ticket.kind == "faq":
            return "bot answered"
        return super().handle(ticket)

class Tier1(Handler):
    def handle(self, ticket) -> str | None:
        if ticket.kind in ("billing", "login") and not ticket.urgent:
            return "tier1 handled"
        return super().handle(ticket)

class Engineering(Handler):
    def handle(self, ticket) -> str | None:
        if ticket.kind == "bug":
            return "engineering ticket filed"
        return super().handle(ticket)

front = Bot()
front.set_next(Tier1()).set_next(Engineering())
result = front.handle(ticket) or "escalate to a human"
"""),
("The Pythonic twist", r"""
<p>The linked-list plumbing is optional ceremony &mdash; a list of callables
and a loop expresses the same contract in five lines, and is what you'll
usually ship:</p>""",
r"""
from typing import Callable, Optional

HandlerFn = Callable[[object], Optional[str]]

def route(ticket, handlers: list[HandlerFn]) -> str:
    for handle in handlers:
        result = handle(ticket)
        if result is not None:              # first non-None wins
            return result
    return "escalate to a human"
"""),
(None, r"""
<p>The other family member is the <em>processing pipeline</em>, where every
handler runs (possibly wrapping the rest) instead of the first match winning
&mdash; that's middleware: auth, rate limiting, logging, each deciding to
short-circuit or pass through. Same pattern, different termination rule.
Distinguish it from a dispatch table: a dict maps a <em>key</em> to one
handler; a chain lets each handler apply arbitrary logic to decide, in
order.</p>""", None),
],
"wild": r"""
<p>WSGI/ASGI and Django middleware, <code>except</code> clauses tried in order
&mdash; and exception propagation itself is a chain of responsibility up the
call stack until a handler catches. Python's <code>logging</code> walks the
logger hierarchy the same way, DOM event bubbling is the browser version, and
servlet filters / Express middleware are the same idea in other worlds.</p>""",
"avoid": r"""
<p>Chains can silently drop requests off the end &mdash; if handling is
mandatory, make the terminal handler explicit and loud. Debugging &ldquo;who
handled this?&rdquo; costs real time in long chains, so log the path in
anything production-grade. And if exactly one handler could ever match per
key, use a dict &mdash; the chain's flexibility is overhead there.</p>""",
"exercise": {
"text": r"""
<p>Build an HTTP-ish pipeline as a list of callables:
<code>rate_limit</code> (rejects after N requests), <code>auth</code>
(rejects missing token), <code>cache</code> (returns a stored response for
repeated paths), and <code>app</code> (always answers). Each takes a request
dict and returns a response or <code>None</code>. Assemble two different
chains &mdash; public API (all four) and internal admin (no rate limit)
&mdash; and add a tracing wrapper that records which handler answered each
request. The trace log is your debugging answer from the pitfalls above.</p>""",
"code": None,
"hint": r"""<p>The tracer doesn't need to touch the handlers:
<code>def traced(handlers): return [wrap(h) for h in handlers]</code> where
<code>wrap</code> records <code>h.__name__</code> when it returns
non-<code>None</code>. You've just decorated a chain &mdash; patterns
compose.</p>"""},
},

# ---------------------------------------------------------------- iterator
{
"slug": "iterator", "name": "Iterator", "category": "behavioral",
"intent": "Walk a collection without exposing how it's built \u2014 so deeply woven into Python that you stopped seeing it.",
"sections": [
("The problem", r"""
<p>Your <code>LinkedList</code> works, but callers traverse it by grabbing
<code>head</code> and following <code>.next_node</code> by hand &mdash; every
caller re-implements the walk, and none of them can survive you switching to
a doubly-linked or chunked representation. The structure's internals have
become its public API.</p>""", None),
("The pattern", r"""
<p>The collection hands out a separate <em>iterator</em> object that knows
the current position and how to advance; clients use only that. Python bakes
the contract into the language: <code>__iter__</code> returns an iterator,
<code>__next__</code> advances it, <code>StopIteration</code> ends it &mdash;
and <code>for</code> speaks that protocol natively:</p>""",
r"""
class _Node:
    def __init__(self, value, next_node=None):
        self.value, self.next_node = value, next_node

class LinkedList:
    def __init__(self, *values):
        self.head = None
        for v in reversed(values):
            self.head = _Node(v, self.head)

    def __iter__(self):
        node = self.head
        while node:
            yield node.value           # a generator IS an iterator
            node = node.next_node

lst = LinkedList(1, 2, 3)
for v in lst:                          # no .head, no .next_node in sight
    print(v)
total = sum(lst)                       # every builtin now works
"""),
(None, r"""
<p>That <code>yield</code> is the entire GoF pattern: the generator object
Python creates for you <em>is</em> the iterator class you'd otherwise write
by hand, with the position bookkeeping stored in the paused frame. Writing
<code>__next__</code> manually is museum-grade Python &mdash; know how it
works, almost never write it.</p>""", None),
("The Pythonic twist", r"""
<p>The distinction worth actually internalizing is <em>iterable</em> (can
produce iterators; a list) versus <em>iterator</em> (one exhausted-once walk;
a generator). Collections should return a <em>fresh</em> iterator from every
<code>__iter__</code> call &mdash; that's what lets two loops walk the same
structure simultaneously, and it's the bug when someone's custom class
mysteriously &ldquo;goes empty&rdquo; on the second loop. Beyond that,
<code>itertools</code> is the pattern's standard library:
<code>islice</code>, <code>chain</code>, <code>takewhile</code> compose walks
without materializing lists, which is the whole performance story of lazy
iteration.</p>""",
r"""
class Countdown:
    def __init__(self, n: int):
        self.n = n

    def __iter__(self):                # fresh iterator per call
        n = self.n
        while n > 0:
            yield n
            n -= 1

c = Countdown(3)
list(zip(c, c))                        # [(3, 3), (2, 2), (1, 1)] -- independent walks
"""),
],
"wild": r"""
<p>Everywhere: <code>for</code>, comprehensions, <code>zip</code>,
<code>enumerate</code>, file objects yielding lines, <code>dict</code> views,
<code>csv.reader</code>, <code>Path.iterdir()</code>, database cursors,
<code>range</code>. Every generator you've written was you using the GoF
Iterator pattern with language-level sugar.</p>""",
"avoid": r"""
<p>Nothing to avoid about the pattern itself in Python &mdash; the traps are
usage-level: returning <code>self</code> from a collection's
<code>__iter__</code> (one shared walk, the goes-empty bug), calling
<code>list()</code> on an infinite iterator, and iterating a structure while
mutating it. If callers need random access or length, an iterator is the
wrong gift &mdash; hand them a sequence.</p>""",
"exercise": {
"text": r"""
<p>Build a binary search tree with <code>insert</code>, then give it
<code>__iter__</code> yielding values in sorted order via recursive
<code>yield from</code>. Add a second traversal, <code>breadth_first()</code>,
as a generator using <code>collections.deque</code>. Final proof of
independence: <code>list(zip(tree, tree.breadth_first()))</code> must
interleave both walks over the same tree without interference.</p>""",
"code": None,
"hint": r"""<p>In-order:
<code>if node.left: yield from self._walk(node.left)</code>, yield the node,
recurse right. Breadth-first: seed a deque with the root,
<code>popleft</code>, yield, append children. Both being generators is what
makes the zip interleaving work for free.</p>"""},
},

# ---------------------------------------------------------------- mediator
{
"slug": "mediator", "name": "Mediator", "category": "behavioral",
"intent": "Replace a tangle of objects that all talk to each other with a hub that owns the conversation.",
"sections": [
("The problem", r"""
<p>A signup dialog: the &ldquo;company account&rdquo; checkbox reveals the
VAT field, the VAT field's validity gates the submit button, submitting
disables everything, errors re-enable some of it. Implemented naively, each
widget holds references to the others &mdash; four widgets, and already a
web where adding a fifth means teaching it about everyone (n&sup2; couplings,
in the limit).</p>""", None),
("The pattern", r"""
<p>Components stop knowing each other. Each one reports events to a single
mediator; the mediator owns all the interaction rules and directs the
components. n&sup2; couplings become n:</p>""",
r"""
class Component:
    def __init__(self, mediator: "SignupDialog", name: str):
        self.mediator = mediator
        self.name = name

    def changed(self, event: str) -> None:
        self.mediator.notify(self, event)     # the ONLY outgoing arrow

class Checkbox(Component):
    def __init__(self, mediator, name):
        super().__init__(mediator, name)
        self.checked = False

class Field(Component):
    def __init__(self, mediator, name):
        super().__init__(mediator, name)
        self.visible = False
        self.value = ""

class Button(Component):
    def __init__(self, mediator, name):
        super().__init__(mediator, name)
        self.enabled = False

class SignupDialog:                            # the mediator
    def __init__(self):
        self.company = Checkbox(self, "company")
        self.vat = Field(self, "vat")
        self.submit = Button(self, "submit")

    def notify(self, sender: Component, event: str) -> None:
        if sender is self.company and event == "toggled":
            self.vat.visible = self.company.checked
            self.submit.enabled = not self.company.checked
        elif sender is self.vat and event == "edited":
            self.submit.enabled = len(self.vat.value) == 11

dialog = SignupDialog()
dialog.company.checked = True
dialog.company.changed("toggled")              # vat appears, submit gated
"""),
(None, r"""
<p>All the &ldquo;when X then Y&rdquo; policy now lives in one readable
method. Widgets became reusable dumb components; the dialog became the one
file you open when the interaction rules change.</p>""", None),
("The Pythonic twist", r"""
<p>Mediator and Observer are siblings, and real systems often fuse them: the
mediator <em>is</em> an event hub components publish to. The difference is
where the coordination logic lives &mdash; Observer scatters reactions across
subscribers (each knows its own response); Mediator centralizes the rules in
the hub (components stay policy-free). Pick by asking where you want to read
the rules later. In Python the mediator is frequently just &ldquo;the parent
object&rdquo;: a controller class holding its children and brokering their
interactions, no framework required. The failure mode has a name &mdash;
<em>god object</em> &mdash; and the guard rail is that a mediator holds
<em>interaction</em> policy only; the moment it computes VAT validity itself
rather than asking the field, it has started absorbing its components.</p>""", None),
],
"wild": r"""
<p>Air traffic control is the canonical metaphor (planes never negotiate with
each other). Chat room servers, GUI dialog controllers and MVC controllers,
message brokers and service buses at architecture scale, and Redux-style
single-store dispatch in frontend land.</p>""",
"avoid": r"""
<p>Two components with one interaction: let them talk &mdash; a mediator
there is bureaucracy. Watch the mediator's size in review; when
<code>notify</code> becomes a 300-line rule engine, split it by concern or
push behavior back into components. And keep components genuinely ignorant of
each other, or you quietly pay for both architectures at once.</p>""",
"exercise": {
"text": r"""
<p>Build a chat room mediator: <code>User.send(text)</code> calls
<code>room.route(sender, text)</code>; the room broadcasts to everyone else.
Users hold no references to other users. Then add features <em>touching only
the room</em>: direct messages (<code>"@name hello"</code>), a mute list
(muted users' messages route nowhere), and a transcript. Finish with the
test that proves the architecture: creating a user requires only a room,
never another user.</p>""",
"code": None,
"hint": r"""<p><code>Room.route</code> parses the <code>@name</code> prefix
itself &mdash; that's interaction policy, so it belongs in the mediator, not
in <code>User.send</code>. If you felt tempted to put it in the user, that
tension is the lesson.</p>"""},
},

# ---------------------------------------------------------------- memento
{
"slug": "memento", "name": "Memento", "category": "behavioral",
"intent": "Snapshot an object's state into an opaque token so it can be restored later \u2014 undo by photograph instead of by reversal.",
"sections": [
("The problem", r"""
<p>Your editor needs undo, but unlike the Command lesson's neatly reversible
inserts and deletes, some operations are hard to invert &mdash; a regex
replace-all, a reflow, a plugin that touched everything. Writing an
<code>undo()</code> that reconstructs the before-state of an arbitrary
operation is somewhere between hard and impossible. What's easy is
<em>photographing</em> the state before the operation runs.</p>""", None),
("The pattern", r"""
<p>Three roles: the <em>originator</em> (the editor) produces and consumes
snapshots of its own state; the <em>memento</em> is that snapshot, opaque to
everyone else; the <em>caretaker</em> (the history) stores mementos without
looking inside:</p>""",
r"""
from dataclasses import dataclass
from collections import deque

@dataclass(frozen=True)
class _Snapshot:                      # the memento: frozen, private-ish
    text: str
    cursor: int

class Editor:                         # the originator
    def __init__(self):
        self.text = ""
        self.cursor = 0

    def save(self) -> _Snapshot:
        return _Snapshot(self.text, self.cursor)

    def restore(self, snap: _Snapshot) -> None:
        self.text = snap.text
        self.cursor = snap.cursor

class History:                        # the caretaker: stores, never inspects
    def __init__(self, limit: int = 50):
        self._stack: deque[_Snapshot] = deque(maxlen=limit)

    def push(self, snap: _Snapshot) -> None:
        self._stack.append(snap)

    def pop(self) -> _Snapshot:
        return self._stack.pop()

ed, history = Editor(), History()
ed.text, ed.cursor = "hello world", 11
history.push(ed.save())
ed.text = "HELLO WORLD (regex replaced everything)"
ed.restore(history.pop())
assert ed.text == "hello world"
"""),
(None, r"""
<p>The encapsulation point is the pattern's soul: the caretaker can hold
snapshots without gaining access to the editor's internals, so the editor
remains free to change its representation. Python enforces privacy only by
convention, so signal it &mdash; a leading underscore, a frozen dataclass,
and no getters.</p>""", None),
("The Pythonic twist", r"""
<p>Snapshotting machinery is built in: <code>copy.deepcopy(self)</code> is
the sledgehammer memento for gnarly state, and the standard library ships a
perfect specimen &mdash; <code>random.getstate()</code> /
<code>random.setstate()</code> is a literal originator API. The engineering
decision is <strong>Memento vs Command-undo</strong>: snapshots cost memory
(mitigate with <code>deque(maxlen=...)</code>, or snapshot deltas) but handle
any operation uniformly; inverse commands cost design effort per operation
but stay tiny. Real editors mix them &mdash; commands for keystrokes,
snapshots around the scary operations.</p>""",
r"""
import random

state = random.getstate()             # memento from the stdlib
a = random.random()
random.setstate(state)
assert random.random() == a           # time rewound
"""),
],
"wild": r"""
<p>Database transactions and savepoints (<code>ROLLBACK</code> restores a
memento), game save files, editor undo in every serious editor, VM and
container snapshots, and <code>random.getstate()</code>/<code>setstate</code>
in the standard library. Git commits are mementos with a caretaker so good it
became the product.</p>""",
"avoid": r"""
<p>Big state &times; frequent snapshots = memory cliff &mdash; measure, cap
the history, or store diffs. Deep-copying objects holding live resources
(sockets, locks, file handles) copies the wrapper, not the resource; exclude
them explicitly. And if every operation is cheaply invertible, Command-undo
is leaner &mdash; don't photograph what you can simply reverse.</p>""",
"exercise": {
"text": r"""
<p>Build a <code>DrawingCanvas</code> whose state is a list of shape dicts.
Implement <code>save()</code>/<code>restore()</code> with proper snapshot
independence &mdash; then write the test that catches the classic bug: take a
snapshot, mutate a shape <em>in place</em> on the live canvas, restore, and
assert the old value came back. Make the test fail with a shallow snapshot,
then fix it. Cap history at 10 with <code>deque</code> and verify snapshot 1
evaporates after 11 saves.</p>""",
"code": None,
"hint": r"""<p>The failing version stores <code>list(self.shapes)</code>
&mdash; new list, same dicts, so in-place mutation leaks into the
&ldquo;snapshot.&rdquo; The fix is <code>copy.deepcopy</code>, or storing
immutable tuples of frozen dataclasses. You met this exact trap in Prototype
&mdash; same physics, different pattern.</p>"""},
},

# ---------------------------------------------------------------- visitor
{
"slug": "visitor", "name": "Visitor", "category": "behavioral",
"intent": "Add new operations to a stable family of classes without touching them \u2014 the operation travels to the data.",
"sections": [
("The problem", r"""
<p>A document model: <code>Paragraph</code>, <code>Image</code>,
<code>Table</code>. Product wants HTML export. Then word count. Then Markdown
export, then an accessibility audit&hellip; If each becomes a method on every
node class, the classes bloat with concerns that aren't theirs (why does
<code>Image</code> know about Markdown?), and every new operation means
editing the whole family.</p>""", None),
("The pattern", r"""
<p>Flip it: the operation becomes a class with one method per node type, and
nodes just hand themselves to it. The classic form routes through an
<code>accept</code> method &mdash; the double-dispatch trick that picks the
right <code>visit_*</code> based on both the node type and the visitor:</p>""",
r"""
class Paragraph:
    def __init__(self, text: str):
        self.text = text
    def accept(self, visitor):
        return visitor.visit_paragraph(self)

class Image:
    def __init__(self, src: str, alt: str = ""):
        self.src, self.alt = src, alt
    def accept(self, visitor):
        return visitor.visit_image(self)

class Document:
    def __init__(self, *children):
        self.children = list(children)
    def accept(self, visitor):
        return visitor.visit_document(self)

class HtmlExporter:                       # a new operation = a new class
    def visit_paragraph(self, p) -> str:
        return f"<p>{p.text}</p>"
    def visit_image(self, i) -> str:
        return f'<img src="{i.src}" alt="{i.alt}">'
    def visit_document(self, d) -> str:
        return "\n".join(child.accept(self) for child in d.children)

class WordCounter:                        # second operation: zero node edits
    def visit_paragraph(self, p) -> int:
        return len(p.text.split())
    def visit_image(self, i) -> int:
        return 0
    def visit_document(self, d) -> int:
        return sum(child.accept(self) for child in d.children)

doc = Document(Paragraph("design patterns in python"), Image("cat.png"))
doc.accept(HtmlExporter())
doc.accept(WordCounter())                 # 4
"""),
("The Pythonic twist", r"""
<p>Python can dispatch on type without the <code>accept</code> plumbing:
<code>functools.singledispatch</code> gives you the visitor as a plain
function family, and nodes need no knowledge of visitors at all:</p>""",
r"""
from functools import singledispatch

@singledispatch
def to_html(node) -> str:
    raise TypeError(f"no renderer for {type(node).__name__}")

@to_html.register
def _(p: Paragraph) -> str:
    return f"<p>{p.text}</p>"

@to_html.register
def _(i: Image) -> str:
    return f'<img src="{i.src}" alt="{i.alt}">'

@to_html.register
def _(d: Document) -> str:
    return "\n".join(to_html(c) for c in d.children)
"""),
(None, r"""
<p>A <code>match node: case Paragraph(): ...</code> statement is the third
spelling. All three sit on the same tradeoff, worth knowing by its academic
name &mdash; the <em>expression problem</em>: methods-on-classes make adding
a <em>type</em> easy and adding an <em>operation</em> expensive; visitors
make adding an <em>operation</em> easy and adding a <em>type</em> expensive
(every visitor must learn <code>visit_video</code>). Choose by which axis
actually changes in your system &mdash; Visitor is the right answer exactly
when the type family is stable and the operations proliferate.</p>""", None),
],
"wild": r"""
<p><code>ast.NodeVisitor</code> in the standard library is a literal,
documented GoF Visitor &mdash; subclass it, define <code>visit_FunctionDef</code>,
and you've written a linter. Compilers and static analyzers are visitor
farms; serializers walking object graphs and <code>singledispatch</code>-based
renderers are the everyday form.</p>""",
"avoid": r"""
<p>If node types change often, Visitor multiplies the pain &mdash; every new
type breaks every visitor. One operation, or two? Just write methods. And
mind traversal ownership: decide once whether visitors recurse into children
(as above) or the structure walks itself calling visitors per node
(<code>ast.NodeVisitor</code>'s <code>generic_visit</code> style) &mdash;
mixing the two double-visits nodes, a classic visitor bug.</p>""",
"exercise": {
"text": r"""
<p>Model shapes: <code>Circle(r)</code>, <code>Rect(w, h)</code>, and
<code>Group(*children)</code>. With <code>singledispatch</code>, write
<code>area()</code> and <code>to_svg()</code> (groups sum and wrap in
<code>&lt;g&gt;</code> respectively). Then perform both halves of the
expression problem yourself: add a <code>Triangle</code> type (count the
functions you had to touch), then add a <code>perimeter()</code> operation
(count again). Write one sentence stating which change Visitor made cheap and
which it made expensive.</p>""",
"code": None,
"hint": r"""<p>The unregistered-type failure is worth engineering: the
<code>@singledispatch</code> base raising <code>TypeError</code> is your
safety net when <code>Triangle</code> arrives &mdash; a loud crash beats a
silently wrong total. That default-function-as-guard is the idiom to
keep.</p>"""},
},

# ---------------------------------------------------------------- interpreter
{
"slug": "interpreter", "name": "Interpreter", "category": "behavioral",
"intent": "Represent a small language's grammar as a class tree, and evaluate sentences by walking it \u2014 powerful, and the pattern to reach for last.",
"sections": [
("The problem", r"""
<p>Ops wants to configure alert rules without a deploy:
<code>"cpu &gt; 90 and disk &gt; 80"</code>, editable in a settings screen.
Hardcoding rules as Python functions means a release per tweak; and no,
<code>eval()</code> on operator-entered strings is not on the table &mdash;
that's remote code execution with extra steps.</p>""", None),
("The pattern", r"""
<p>Give each grammar element a class with an <code>interpret(context)</code>
method: terminals (variables, numbers) evaluate themselves; composites
(comparisons, <code>and</code>/<code>or</code>) evaluate their children and
combine. A rule becomes a tree; evaluation is a walk:</p>""",
r"""
from typing import Protocol

class Expr(Protocol):
    def interpret(self, ctx: dict) -> object: ...

class Num:
    def __init__(self, value: float):
        self.value = value
    def interpret(self, ctx: dict) -> float:
        return self.value

class Var:
    def __init__(self, name: str):
        self.name = name
    def interpret(self, ctx: dict) -> float:
        return ctx[self.name]

class Gt:
    def __init__(self, left: Expr, right: Expr):
        self.left, self.right = left, right
    def interpret(self, ctx: dict) -> bool:
        return self.left.interpret(ctx) > self.right.interpret(ctx)

class And:
    def __init__(self, left: Expr, right: Expr):
        self.left, self.right = left, right
    def interpret(self, ctx: dict) -> bool:
        return self.left.interpret(ctx) and self.right.interpret(ctx)

# "cpu > 90 and disk > 80", as a tree:
rule = And(Gt(Var("cpu"), Num(90)), Gt(Var("disk"), Num(80)))

rule.interpret({"cpu": 95, "disk": 85})   # True
rule.interpret({"cpu": 95, "disk": 40})   # False
"""),
(None, r"""
<p>Notice the pattern is only the <em>evaluation</em> half &mdash; something
still has to turn the string into the tree. For a grammar this small, a
tokenizer plus a short recursive-descent parser (one function per precedence
level) is a well-trodden afternoon; that's the exercise below.</p>""", None),
("The senior warning", r"""
<p>This is the pattern I've most often <em>removed</em> from codebases. A
custom language starts as three classes and becomes parentheses, operator
precedence, string escaping, error messages with line numbers, a debugger
request&hellip; You are signing up to maintain a language runtime. The
checklist before building one: can the rules live in data
(thresholds in a table)? Is there an existing mini-language
(<code>jmespath</code>, SQL, <code>re</code>, JSON Logic) that fits? Is
<code>ast.literal_eval</code> (safe literals only) enough? Only when the
domain genuinely needs its own notation &mdash; and users will write enough
of it to repay a parser &mdash; does Interpreter earn its keep. Then it's
lovely.</p>""", None),
],
"wild": r"""
<p><code>re</code> is an interpreter for the regex language you feed it
(compiled patterns are the tree). SQL engines, spreadsheet formulas, Jinja
templates, <code>str.format</code>'s mini-language, and Python's own
<code>ast</code> module &mdash; your code is a tree being walked by an
interpreter right now.</p>""",
"avoid": r"""
<p>Almost always, at first. Prefer configuration-as-data, an embedded
existing language, or plain Python callables in a registry. Never
<code>eval()</code>/<code>exec()</code> untrusted input &mdash; not even
&ldquo;sanitized&rdquo;. And if the grammar starts growing operators monthly,
graduate to a parser library (Lark, pyparsing) before the hand-rolled parser
becomes the bug farm.</p>""",
"exercise": {
"text": r"""
<p>Extend the tree with <code>Or</code> and <code>Not</code>, then write the
missing half: <code>parse(tokens)</code> for pre-tokenized rules like
<code>["cpu", "&gt;", "90", "and", "not", "disk", "&gt;", "80"]</code>.
Use recursive descent with precedence <code>or</code> &lt; <code>and</code>
&lt; <code>not</code> &lt; comparison. Evaluate three rules against a list of
server dicts and return the servers that alert. Bonus: a helpful
<code>ParseError</code> naming the unexpected token &mdash; error quality is
where hand-rolled parsers go to die.</p>""",
"code": None,
"hint": r"""<p>One function per level: <code>parse_or</code> calls
<code>parse_and</code> and loops on <code>"or"</code>; <code>parse_and</code>
calls <code>parse_not</code>; <code>parse_not</code> consumes an optional
<code>"not"</code> then calls <code>parse_cmp</code>. Keep a position index
in a small <code>Parser</code> class &mdash; threading it through bare
functions is the fiddly part the class removes.</p>"""},
},
]
