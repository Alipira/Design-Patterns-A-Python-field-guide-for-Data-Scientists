# Structural patterns — lesson content.

PATTERNS = [

# ---------------------------------------------------------------- adapter
{
"slug": "adapter", "name": "Adapter", "category": "structural",
"intent": "Make an interface you can't change fit the interface your code expects \u2014 a translator between two shapes.",
"sections": [
("The problem", r"""
<p>Your alerting code is written against a clean protocol you designed:</p>""",
r"""
from typing import Protocol

class Notifier(Protocol):
    def send(self, message: str) -> None: ...

def alert_on_call(notifier: Notifier) -> None:
    notifier.send("Server down!")
"""),
(None, r"""
<p>Then procurement buys an SMS vendor whose SDK looks like this &mdash; and
you can't touch it, it's their package:</p>""",
r"""
class LegacySmsGateway:
    # vendor code: do not modify
    def deliver_payload(self, xml: str, priority: int) -> None:
        print(f"SMS[{priority}]: {xml}")
"""),
(None, r"""
<p>Wrong method name, wrong argument format, wrong everything. The naive fix
&mdash; sprinkling <code>if isinstance(notifier, LegacySmsGateway)</code>
through your alerting code &mdash; infects every caller with vendor
knowledge.</p>""", None),
("The pattern", r"""
<p>Adapter is a small class that <em>implements the interface you want</em>
and <em>holds the object you have</em>, translating between them. All the
impedance mismatch is quarantined in one file:</p>""",
r"""
class SmsAdapter:
    def __init__(self, gateway: LegacySmsGateway, priority: int = 1):
        self._gateway = gateway
        self._priority = priority

    def send(self, message: str) -> None:            # the interface you want
        xml = f"<sms><body>{message}</body></sms>"   # the translation
        self._gateway.deliver_payload(xml, self._priority)

alert_on_call(SmsAdapter(LegacySmsGateway()))   # client code: unchanged
"""),
"DEMO",
("The Pythonic twist", r"""
<p>Duck typing does half the work: the adapter doesn't inherit from anything,
it just <em>has the right shape</em>, and <code>Protocol</code> lets the type
checker verify it. And when the mismatch is a single callable,
the adapter shrinks to a lambda or <code>functools.partial</code>:</p>""",
r"""
from functools import partial

# a library wants callback(event) but your handler is handle(logger, event)
def handle(logger, event) -> None: ...

register_callback = lambda cb: None   # stand-in for the library hook
register_callback(partial(handle, my_logger := object()))
"""),
(None, r"""
<p>One discipline rule from years of reviewing these: <strong>adapters
translate, they don't think.</strong> The moment business rules creep into an
adapter, you've hidden logic in the least discoverable place in the codebase.
Retry policies, formatting decisions, filtering &mdash; those belong in real
components; the adapter's only job is shape conversion.</p>""", None),
],
"wild": r"""
<p><code>io.TextIOWrapper</code> adapts a byte stream to a text interface
&mdash; it's the &ldquo;T&rdquo; in every <code>open()</code> call.
<code>socket.makefile()</code> adapts a socket to a file. <code>os.PathLike</code>
lets <code>pathlib.Path</code> objects flow into APIs written for strings.
The <code>requests</code> library literally names its pluggable transport layer
<code>HTTPAdapter</code>.</p>""",
"avoid": r"""
<p>If you own both sides, don't adapt &mdash; change one interface and delete
the mismatch. Beware adapter <em>chains</em> (A adapts B adapts C): each hop
is a place for bugs and a lie about the real shape of the system. And if the
two interfaces differ in <em>semantics</em>, not just shape (sync vs async,
at-most-once vs at-least-once), an adapter can't honestly bridge that &mdash;
that's a redesign, not a wrapper.</p>""",
"exercise": {
"text": r"""
<p>Your new monitoring code expects the protocol below, but the hardware team
ships <code>OldTemperatureSensor</code>. Write <code>SensorAdapter</code> so
<code>log_reading</code> works unchanged. Then the twist: the old sensor
sometimes returns <code>"ERR"</code> &mdash; decide where that translation
belongs and defend your choice in a comment.</p>""",
"code": r"""
from typing import Protocol

class Sensor(Protocol):
    def celsius(self) -> float: ...

def log_reading(sensor: Sensor) -> None:
    print(f"{sensor.celsius():.1f} C")

class OldTemperatureSensor:
    # vendor code: returns fahrenheit as a string, or "ERR"
    def read_fahrenheit(self) -> str:
        return "98.6"
""",
"hint": r"""<p>Conversion: <code>(f - 32) * 5 / 9</code>. For
<code>"ERR"</code>: raising a domain exception (<code>SensorReadError</code>)
from the adapter keeps the protocol honest &mdash; returning a magic value
like <code>float("nan")</code> just moves the vendor's weirdness into your
domain.</p>"""},
"demo": {
"html": r"""
<div>
  <button id="ad-email" class="on">EmailService()</button>
  <button id="ad-sms">SmsAdapter(LegacySmsGateway())</button>
</div>
<div class="out" id="ad-out"></div>
<p class="note">The client line never changes. The adapter translates a clean send() into the vendor's XML-and-priority ritual.</p>""",
"js": r"""
(function () {
  var out = document.getElementById("ad-out");
  function pick(which) {
    var lines = [">>> alert_on_call(notifier)", ">>> notifier.send(\"Server down!\")"];
    if (which === "email") {
      lines.push("EMAIL to oncall@example.com: Server down!");
    } else {
      lines.push("  # adapter translates:");
      lines.push("  # gateway.deliver_payload(\"<sms><body>Server down!</body></sms>\", 1)");
      lines.push("SMS[1]: <sms><body>Server down!</body></sms>");
    }
    out.textContent = lines.join("\n");
    document.getElementById("ad-email").classList.toggle("on", which === "email");
    document.getElementById("ad-sms").classList.toggle("on", which === "sms");
  }
  document.getElementById("ad-email").addEventListener("click", function () { pick("email"); });
  document.getElementById("ad-sms").addEventListener("click", function () { pick("sms"); });
  pick("email");
})();"""},
},

# ---------------------------------------------------------------- bridge
{
"slug": "bridge", "name": "Bridge", "category": "structural",
"intent": "Split a class that varies along two independent dimensions into two hierarchies connected by composition \u2014 turning m\u00d7n subclasses into m+n.",
"sections": [
("The problem", r"""
<p>Your charting library renders shapes as either SVG or raster. With
inheritance as the only tool, the class list reads:
<code>SvgCircle</code>, <code>RasterCircle</code>, <code>SvgSquare</code>,
<code>RasterSquare</code>&hellip; Adding a triangle means two new classes;
adding a PDF renderer means one new class <em>per shape</em>. Two independent
axes of change &mdash; shape and rendering &mdash; have been multiplied into
one exploding hierarchy.</p>""", None),
("The pattern", r"""
<p>Bridge cuts the hierarchy in two: an <em>abstraction</em> side (what the
thing is &mdash; shapes) that <em>holds</em> an <em>implementation</em> side
(how it's drawn &mdash; renderers). Each axis now grows independently:</p>""",
r"""
from typing import Protocol

class Renderer(Protocol):                       # implementation axis
    def circle(self, radius: float) -> str: ...
    def square(self, side: float) -> str: ...

class SvgRenderer:
    def circle(self, radius: float) -> str:
        return f'<circle r="{radius}"/>'
    def square(self, side: float) -> str:
        return f'<rect width="{side}" height="{side}"/>'

class RasterRenderer:
    def circle(self, radius: float) -> str:
        return f"[pixels: circle r={radius}]"
    def square(self, side: float) -> str:
        return f"[pixels: square s={side}]"

class Shape:                                    # abstraction axis
    def __init__(self, renderer: Renderer):    # <- the bridge
        self.renderer = renderer

class Circle(Shape):
    def __init__(self, renderer: Renderer, radius: float):
        super().__init__(renderer)
        self.radius = radius
    def draw(self) -> str:
        return self.renderer.circle(self.radius)

class Square(Shape):
    def __init__(self, renderer: Renderer, side: float):
        super().__init__(renderer)
        self.side = side
    def draw(self) -> str:
        return self.renderer.square(self.side)

Circle(SvgRenderer(), 5).draw()      # '<circle r="5"/>'
Circle(RasterRenderer(), 5).draw()   # '[pixels: circle r=5]'
"""),
(None, r"""
<p>Count the arithmetic: 2 shapes &times; 2 renderers was heading toward 4, 6,
8 classes; the bridge holds it at 2&nbsp;+&nbsp;2, and a PDF renderer is
exactly one new class.</p>""", None),
("The Pythonic twist", r"""
<p>You've seen this move before &mdash; it's <em>composition over
inheritance</em>, and structurally it's identical to Strategy. The difference
is intent and timing: Strategy swaps an <em>algorithm</em>, often at runtime;
Bridge is an <em>architectural</em> split you make when a class has two
reasons to change, usually fixed at construction. In Python there's no
ceremony beyond what's above &mdash; the pattern is just &ldquo;pass the
other hierarchy in&rdquo;. Recognize it by the constructor:
<code>Circle(renderer, ...)</code> is a bridge in the wild.</p>""", None),
],
"wild": r"""
<p>SQLAlchemy is a giant bridge: the query abstraction on one side, dialect
implementations (PostgreSQL, SQLite, MySQL) on the other, connected through
the engine. GUI toolkits bridge widget abstractions to platform backends.
Python's <code>logging</code> splits what to log (loggers) from where it goes
(handlers) &mdash; same cut. Device drivers behind an OS API are the original
motivating case.</p>""",
"avoid": r"""
<p>One axis of variation is just ordinary polymorphism &mdash; don't pre-split
a hierarchy for a second dimension that may never come (that's speculative
generality). If both sides would always be paired one-to-one anyway
(<code>SvgCircle</code> logic that only makes sense with SVG), the bridge
buys nothing but indirection.</p>""",
"exercise": {
"text": r"""
<p>A notification system has message kinds (<code>Alert</code>,
<code>Digest</code>) and delivery channels (<code>Email</code>,
<code>Slack</code>). Implement it as a bridge: channels expose
<code>deliver(subject, body)</code>; message kinds format themselves
differently (an alert is loud and short, a digest aggregates a list) and
deliver through whatever channel they're given. Then add an <code>Sms</code>
channel and confirm you wrote exactly one new class. For contrast, list the
class names the naive inheritance version would need.</p>""",
"code": None,
"hint": r"""<p>Shape: <code>class Message: def __init__(self, channel:
Channel)</code>; <code>Alert.send()</code> builds its subject/body then calls
<code>self.channel.deliver(...)</code>. The naive version needs
<code>AlertEmail, AlertSlack, AlertSms, DigestEmail, DigestSlack,
DigestSms</code> &mdash; six and counting.</p>"""},
},

# ---------------------------------------------------------------- composite
{
"slug": "composite", "name": "Composite", "category": "structural",
"intent": "Treat single objects and whole trees of objects through one interface, so recursion replaces type-checking.",
"sections": [
("The problem", r"""
<p>You're computing the size of a backup: folders contain files <em>and other
folders</em>. Without a shared interface, every operation grows an
<code>isinstance</code> ladder &mdash; and every new operation (render, count,
search) repeats it:</p>""",
r"""
def total_size(item) -> int:
    if isinstance(item, File):
        return item.size
    elif isinstance(item, Folder):
        return sum(total_size(child) for child in item.children)
    raise TypeError(item)
"""),
("The pattern", r"""
<p>Composite gives leaf and container the <em>same</em> interface. The
container implements each operation by delegating to its children &mdash; the
recursion moves inside the structure, and clients stop caring which kind of
node they hold:</p>""",
r"""
from typing import Protocol

class Node(Protocol):
    def size(self) -> int: ...
    def render(self, indent: int = 0) -> str: ...

class File:
    def __init__(self, name: str, size: int):
        self.name, self._size = name, size

    def size(self) -> int:
        return self._size

    def render(self, indent: int = 0) -> str:
        return " " * indent + f"{self.name} ({self._size} B)"

class Folder:
    def __init__(self, name: str, *children: Node):
        self.name = name
        self.children = list(children)

    def add(self, node: Node) -> "Folder":
        self.children.append(node)
        return self

    def size(self) -> int:
        return sum(child.size() for child in self.children)   # <- the trick

    def render(self, indent: int = 0) -> str:
        lines = [" " * indent + f"{self.name}/"]
        lines += [child.render(indent + 2) for child in self.children]
        return "\n".join(lines)

root = Folder("backup",
              File("notes.txt", 300),
              Folder("photos", File("cat.jpg", 51200), File("dog.jpg", 48800)))

root.size()     # 100300 -- one call, arbitrary depth
print(root.render())
"""),
(None, r"""
<p>Notice what happened to <code>total_size</code>: it's gone. A folder of
folders of files answers <code>size()</code> the same way a single file does.
Adding an operation now means adding one method to each class &mdash; no
type ladders anywhere.</p>""", None),
("The Pythonic twist", r"""
<p>Duck typing means you don't even need the <code>Protocol</code> at runtime
&mdash; anything with <code>size()</code> and <code>render()</code> can live
in the tree, which is how plugins slot into composite structures. Two
practical notes from production trees: implement <code>__iter__</code> on the
composite (a generator with <code>yield from</code>) so clients can walk it
with a plain <code>for</code> loop, and guard against cycles if nodes can be
re-parented &mdash; a folder added to its own descendant recurses forever.</p>""",
r"""
from typing import Iterator

class Folder2(Folder):
    def __iter__(self) -> Iterator[Node]:
        for child in self.children:
            yield child
            if isinstance(child, Folder):
                yield from child          # depth-first walk for free
"""),
(None, r"""
<p>There's a classic design tension here worth knowing by name:
<em>transparency vs safety</em>. Putting <code>add()</code> on the shared
interface makes leaves and composites fully interchangeable (transparent) but
means <code>file.add(...)</code> exists and must fail at runtime. Keeping
<code>add()</code> only on <code>Folder</code> (as above) is safer but means
clients occasionally check the type. Python culture leans toward safety here;
either is defensible if chosen deliberately.</p>""", None),
],
"wild": r"""
<p><code>xml.etree.ElementTree</code>: an <code>Element</code> contains
elements, and <code>iter()</code>/<code>findall()</code> walk the tree
uniformly. Python's own <code>ast</code> module is a composite your code
becomes. GUI toolkits (a window contains panels contain buttons), scene
graphs in game engines, org charts, and JSON itself &mdash; dicts of lists of
dicts &mdash; are all this shape.</p>""",
"avoid": r"""
<p>A flat, homogeneous collection is a <code>list</code> &mdash; don't build a
tree for data with no hierarchy. If leaf and container genuinely share almost
no operations, forcing one interface produces methods that lie
(<code>NotImplementedError</code> farms). And for very deep trees, remember
Python's recursion limit: an iterative walk with an explicit stack beats
elegant recursion around a thousand levels down.</p>""",
"exercise": {
"text": r"""
<p>Build a restaurant menu: <code>MenuItem(name, price)</code> and
<code>Menu(name, *children)</code> where menus nest (Dinner &rarr; Desserts
&rarr; items). Implement <code>price()</code> (sum), <code>render()</code>
(indented), and then the real test: <code>find(name)</code> returning the
first node with that name at any depth, implemented on <em>both</em> classes
so the client never type-checks. Bonus: make <code>Menu</code> iterable and
reimplement <code>find</code> as a two-line loop over <code>self</code>.</p>""",
"code": None,
"hint": r"""<p><code>File</code>-style leaf: <code>find</code> returns
<code>self if self.name == name else None</code>. Composite: return itself on
match, otherwise loop children and return the first non-<code>None</code>.
The bonus version: <code>for node in self: if node.name == name: return
node</code>.</p>"""},
},

# ---------------------------------------------------------------- decorator
{
"slug": "decorator", "name": "Decorator", "category": "structural",
"intent": "Add responsibilities to an object by wrapping it in same-shaped layers \u2014 composition at runtime instead of subclasses at compile time.",
"sections": [
("The problem", r"""
<p>Your export pipeline writes data to a destination. Product keeps adding
optional behaviors: compression, encryption, base64 for one legacy partner.
Subclassing melts down immediately &mdash; <code>CompressedWriter</code>,
<code>EncryptedWriter</code>, <code>CompressedEncryptedWriter</code>,
<code>Base64CompressedEncryptedWriter</code>&hellip; every combination is a
class, and the order of operations is frozen into names. The flags-in-one-class
alternative is no better: an <code>if</code> forest that every feature must
thread through.</p>""", None),
("The pattern", r"""
<p>Decorator makes each optional behavior a thin wrapper with the <em>same
interface</em> as the thing it wraps: do your bit, then delegate inward.
Because wrapper and wrapped are interchangeable, you can stack any combination
in any order &mdash; at runtime:</p>""",
r"""
from typing import Protocol

class Sink(Protocol):
    def write(self, data: str) -> str: ...

class FileSink:
    def write(self, data: str) -> str:
        return f"wrote({data})"

class Gzip:
    def __init__(self, inner: Sink):
        self.inner = inner
    def write(self, data: str) -> str:
        return self.inner.write(f"gzip({data})")     # transform, delegate

class Encrypt:
    def __init__(self, inner: Sink):
        self.inner = inner
    def write(self, data: str) -> str:
        return self.inner.write(f"aes({data})")

class Base64:
    def __init__(self, inner: Sink):
        self.inner = inner
    def write(self, data: str) -> str:
        return self.inner.write(f"b64({data})")

sink = Encrypt(Gzip(FileSink()))       # compose the exact stack you need
sink.write("report")                   # 'wrote(gzip(aes(report)))'
"""),
"DEMO",
("The Pythonic twist", r"""
<p>Yes &mdash; this is <em>that</em> decorator. Python's <code>@</code> syntax
is the GoF pattern applied to callables: a function that takes a function and
returns a same-shaped function, applied at definition time. The mental
translation:</p>""",
r"""
import functools
import time

def timed(fn):
    @functools.wraps(fn)               # preserve __name__, __doc__, etc.
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            print(f"{fn.__name__}: {time.perf_counter() - t0:.4f}s")
    return wrapper

@timed                                  # sugar for: fetch = timed(fetch)
def fetch(url: str) -> str:
    return "..."
"""),
(None, r"""
<p>Two differences worth holding onto. The GoF form wraps <em>objects at
runtime</em> and can be added or removed per instance; <code>@</code> wraps
<em>the function for everyone</em> at import time &mdash; but nothing stops
you writing <code>fast_fetch = timed(fetch)</code> by hand when you want the
runtime version. And always use <code>functools.wraps</code>: an anonymous
stack of <code>wrapper</code> frames is the debugging tax this pattern
charges, so pay it down where the language lets you.</p>""", None),
],
"wild": r"""
<p>Python's <code>io</code> stack is textbook GoF: <code>open()</code> hands
you a <code>TextIOWrapper</code> wrapping a <code>BufferedReader</code>
wrapping a raw <code>FileIO</code> &mdash; three decorators before your first
<code>read()</code>. <code>gzip.open()</code> adds one more layer to the same
onion. WSGI/ASGI middleware wraps applications in applications;
<code>functools.lru_cache</code>, <code>@login_required</code>, and pytest
fixtures' wrapping behavior are all the callable form.</p>""",
"avoid": r"""
<p>If a behavior is mandatory, put it in the class &mdash; decorators are for
<em>optional, combinable</em> responsibilities. Deep stacks hurt: tracebacks
become wrapper archaeology, and <code>isinstance</code> checks break because
the outermost layer isn't the class anyone expects (interrogate behavior, not
type). If layers need to know about <em>each other</em> &mdash; encryption
that must run before compression for correctness &mdash; that ordering rule
belongs in a builder or facade that assembles the stack, not in the layers.</p>""",
"exercise": {
"text": r"""
<p>Part one, object form: given a base <code>EmailNotifier</code> with
<code>notify(msg)</code>, write decorators <code>Timestamped</code> (prefixes
the time), <code>Deduplicated</code> (drops a message identical to the last
one), and <code>SlackMirror</code> (also prints to a fake Slack). Compose them
two different ways and explain one observable difference the order makes.
Part two, callable form: write <code>@retry(times=3, delay=0)</code> that
re-invokes a failing function, uses <code>functools.wraps</code>, and re-raises
the final exception. Prove <code>fn.__name__</code> survived.</p>""",
"code": None,
"hint": r"""<p><code>retry</code> is a decorator <em>factory</em>: three
levels &mdash; <code>retry(times)</code> returns <code>deco(fn)</code> returns
<code>wrapper(*args)</code>. For ordering:
<code>Deduplicated(Timestamped(base))</code> almost never dedups (timestamps
make every message unique) while <code>Timestamped(Deduplicated(base))</code>
works &mdash; that asymmetry is your explanation.</p>"""},
"demo": {
"html": r"""
<div>
  <button id="dc-gzip">wrap in Gzip</button>
  <button id="dc-enc">wrap in Encrypt</button>
  <button id="dc-b64">wrap in Base64</button>
  <button id="dc-reset">reset</button>
</div>
<div class="out" id="dc-out"></div>
<p class="note">Each click wraps the current stack in one more layer &mdash; same interface outside, new behavior inside. Order is yours to choose.</p>""",
"js": r"""
(function () {
  var layers = [];
  var names = {gzip: "Gzip", enc: "Encrypt", b64: "Base64"};
  var ops = {gzip: "gzip", enc: "aes", b64: "b64"};
  function render() {
    var expr = "FileSink()", payload = "report";
    layers.forEach(function (k) { expr = names[k] + "(" + expr + ")"; });
    for (var i = layers.length - 1; i >= 0; i--) payload = ops[layers[i]] + "(" + payload + ")";
    document.getElementById("dc-out").textContent =
      ">>> sink = " + expr + "\n>>> sink.write(\"report\")\n'wrote(" + payload + ")'";
  }
  ["gzip", "enc", "b64"].forEach(function (k) {
    document.getElementById("dc-" + k).addEventListener("click", function () {
      layers.push(k); render();
    });
  });
  document.getElementById("dc-reset").addEventListener("click", function () {
    layers = []; render();
  });
  render();
})();"""},
},

# ---------------------------------------------------------------- facade
{
"slug": "facade", "name": "Facade", "category": "structural",
"intent": "Put one simple, intent-level entry point in front of a complicated subsystem \u2014 compress the knowledge, keep the escape hatches.",
"sections": [
("The problem", r"""
<p>Converting a video in your codebase requires five subsystem calls in
exactly the right order, with the right glue between them:</p>""",
r"""
def convert_the_hard_way(path: str) -> bytes:
    codec = CodecProbe().detect(path)
    frames = Decoder(codec).decode(path)
    frames = FilterChain(["deinterlace", "scale=720"]).run(frames)
    stream = Encoder("h264").encode(frames)
    return Muxer("mp4").mux(stream, audio=Decoder(codec).audio(path))
"""),
(None, r"""
<p>Three teams have copy-pasted this ritual; two of them forgot the audio
track. Every caller carries knowledge that belongs to the video subsystem
&mdash; and when the encoder API changes, the change fans out to all of
them.</p>""", None),
("The pattern", r"""
<p>A facade is a front door: one object (or function) that speaks the
<em>caller's</em> language and internally choreographs the subsystem. The
complexity doesn't disappear &mdash; it moves to the one place that should
own it:</p>""",
r"""
class VideoConverter:
    def convert(self, path: str, target: str = "mp4") -> bytes:
        codec = CodecProbe().detect(path)
        decoder = Decoder(codec)
        frames = FilterChain(["deinterlace", "scale=720"]).run(
            decoder.decode(path))
        stream = Encoder("h264").encode(frames)
        return Muxer(target).mux(stream, audio=decoder.audio(path))

# every caller, forever:
# VideoConverter().convert("clip.mov")
"""),
"DEMO",
("The Pythonic twist", r"""
<p>In Python a facade is very often just <em>a module with functions</em>.
The canonical story is <code>requests</code>: underneath sits connection
pooling, TLS negotiation, redirects, cookies &mdash; and the facade is
<code>requests.get(url)</code>. The standard library does it too:
<code>subprocess.run()</code> fronts the <code>Popen</code> machinery,
<code>shutil.make_archive()</code> fronts <code>zipfile</code>/<code>tarfile</code>.
The design discipline that separates a facade from a god object:</p>
<ul>
<li><strong>It orchestrates, it doesn't own.</strong> Business logic stays in
the subsystem; the facade sequences calls and translates errors.</li>
<li><strong>Escape hatches stay open.</strong> The subsystem remains importable
for the 5% of callers who need <code>Encoder</code> directly &mdash; a facade
is a default path, not a wall.</li>
<li><strong>It speaks caller vocabulary.</strong> <code>convert(path,
"mp4")</code>, not <code>run_pipeline(ProbeConfig(...))</code>.</li>
</ul>""", None),
],
"wild": r"""
<p><code>requests</code> over <code>urllib3</code>, <code>pathlib.Path</code>
over the <code>os</code>/<code>os.path</code>/<code>glob</code> sprawl,
<code>subprocess.run</code> over <code>Popen</code>, <code>print</code> over
<code>sys.stdout</code>, <code>json.dumps</code> over encoder classes. Nearly
every &ldquo;high-level interface&rdquo; note in the standard library docs is
announcing a facade.</p>""",
"avoid": r"""
<p>Don't facade a subsystem of one class, and don't let the facade accrete
logic until it <em>is</em> the subsystem (the god-object failure mode). If
callers constantly bypass it, the abstraction is wrong &mdash; listen to that
signal rather than adding parameters until the simple front door has fifteen
knobs and reproduces the complexity it was hiding.</p>""",
"exercise": {
"text": r"""
<p>Write a <code>deploy(app_name)</code> facade over five stub subsystems:
<code>Git.pull()</code>, <code>DockerBuild.build(tag)</code>,
<code>Registry.push(tag)</code>, <code>Kubernetes.rollout(tag)</code>,
<code>HealthCheck.wait(app_name)</code> (each can just print and return a
value). Requirements: a failure at any step raises <code>DeployError</code>
naming the step; the subsystems remain individually importable; and a unit
test drives <code>deploy</code> with fakes injected via keyword arguments
&mdash; which will force you to decide how the facade acquires its
collaborators.</p>""",
"code": None,
"hint": r"""<p>Signature that makes testing trivial: <code>def deploy(app,
*, git=None, builder=None, ...)</code> with <code>git = git or Git()</code>
defaults. Wrap each step in <code>try/except Exception as e: raise
DeployError(f"push failed: {e}") from e</code> &mdash; error translation is
half of what real facades do.</p>"""},
"demo": {
"html": r"""
<div>
  <button id="fc-facade">VideoConverter().convert("clip.mov")</button>
  <button id="fc-manual">what it replaced</button>
</div>
<div class="out" id="fc-out"></div>
<p class="note">One intent-level call, five subsystem calls hidden behind it. The complexity moved; it didn't vanish.</p>""",
"js": r"""
(function () {
  var out = document.getElementById("fc-out");
  function facade() {
    out.textContent = [">>> VideoConverter().convert(\"clip.mov\")",
      "  probe: codec = prores", "  decode: 1420 frames", "  filter: deinterlace, scale=720",
      "  encode: h264", "  mux: mp4 + audio", "b'\\x00\\x00\\x00\\x18ftypmp4...'  # 12.4 MB"].join("\n");
    document.getElementById("fc-facade").classList.add("on");
    document.getElementById("fc-manual").classList.remove("on");
  }
  function manual() {
    out.textContent = ["# the ritual every caller used to copy-paste:",
      "codec  = CodecProbe().detect(path)", "frames = Decoder(codec).decode(path)",
      "frames = FilterChain([\"deinterlace\", \"scale=720\"]).run(frames)",
      "stream = Encoder(\"h264\").encode(frames)",
      "video  = Muxer(\"mp4\").mux(stream, audio=Decoder(codec).audio(path))",
      "# ...and two teams forgot the audio line"].join("\n");
    document.getElementById("fc-manual").classList.add("on");
    document.getElementById("fc-facade").classList.remove("on");
  }
  document.getElementById("fc-facade").addEventListener("click", facade);
  document.getElementById("fc-manual").addEventListener("click", manual);
  facade();
})();"""},
},

# ---------------------------------------------------------------- flyweight
{
"slug": "flyweight", "name": "Flyweight", "category": "structural",
"intent": "Share the heavy, identical part of many objects instead of duplicating it \u2014 a memory optimization with a factory-managed cache.",
"sections": [
("The problem", r"""
<p>Your document editor represents each character as an object carrying its
font name, size, weight, and color. A 500-page manuscript is a million
characters &mdash; and a million copies of the string
<code>"Source Serif Pro"</code>. Memory profiling shows 90% of the heap is
identical styling data repeated per character.</p>""", None),
("The pattern", r"""
<p>Flyweight splits object state in two. <em>Intrinsic</em> state (the shared,
immutable part: the style) lives in a small number of cached objects.
<em>Extrinsic</em> state (what actually varies: the character, its position)
stays outside and is passed in or stored per instance. A factory hands out the
shared objects, creating each distinct one exactly once:</p>""",
r"""
from dataclasses import dataclass

@dataclass(frozen=True)                     # immutable -- non-negotiable
class GlyphStyle:
    font: str
    size: int
    bold: bool

class StyleFactory:
    def __init__(self):
        self._cache: dict[tuple, GlyphStyle] = {}

    def get(self, font: str, size: int, bold: bool = False) -> GlyphStyle:
        key = (font, size, bold)
        if key not in self._cache:
            self._cache[key] = GlyphStyle(font, size, bold)
        return self._cache[key]

styles = StyleFactory()

@dataclass
class Char:                                  # extrinsic state stays here
    ch: str
    style: GlyphStyle                        # reference, not copy

doc = [Char(c, styles.get("Source Serif Pro", 11)) for c in "a million chars"]
assert doc[0].style is doc[1].style          # one style object, shared
"""),
("The Pythonic twist", r"""
<p>The factory-with-a-cache is such a common shape that
<code>functools.lru_cache</code> <em>is</em> a flyweight factory when the
product is immutable:</p>""",
r"""
from functools import lru_cache

@lru_cache(maxsize=None)
def get_style(font: str, size: int, bold: bool = False) -> GlyphStyle:
    return GlyphStyle(font, size, bold)

assert get_style("Menlo", 12) is get_style("Menlo", 12)
"""),
(None, r"""
<p>Python itself flyweights aggressively: CPython caches small integers
(&minus;5 through 256), interns many strings (and lets you force it with
<code>sys.intern</code> for fast comparisons in hot dict lookups), and
<code>re.compile</code> keeps an internal cache of compiled patterns. The
companion tool in the same fight is <code>__slots__</code>, which shrinks the
per-instance overhead of whatever extrinsic state remains.</p>
<p>The one law of flyweights: <strong>shared state must be immutable.</strong>
Mutate a shared style and every &ldquo;a&rdquo; in the manuscript goes bold
at once &mdash; the hardest kind of bug to trace back. That's what
<code>frozen=True</code> is buying above.</p>""", None),
],
"wild": r"""
<p>String interning and the small-int cache in CPython, <code>re</code>'s
pattern cache, glyph and texture atlases in game engines and font renderers,
Java's <code>Integer.valueOf</code> cache &mdash; and every ORM identity map
(one object per row per session) is at least a first cousin.</p>""",
"avoid": r"""
<p>This is an optimization: apply it after <code>tracemalloc</code> says so,
not before. It buys memory with indirection and a cache to manage (unbounded
caches on user-controlled keys are a slow leak &mdash; note
<code>maxsize=None</code> above is a choice, not a default to copy blindly).
If instances rarely repeat, the cache is pure overhead; if the shared part
must change per object, it was never intrinsic state to begin with.</p>""",
"exercise": {
"text": r"""
<p>A particle system spawns 100,000 particles, each with a type (sprite name,
base color, max speed) and per-particle position and velocity. Build it twice:
naive (every particle carries its own copies) and flyweight
(<code>ParticleType</code> frozen and cached via <code>lru_cache</code>, with
<code>__slots__</code> on the particle). Measure both with
<code>tracemalloc</code> and report the ratio. Then write the test that
enforces the law: mutating a shared type must raise.</p>""",
"code": None,
"hint": r"""<p>Measure with <code>tracemalloc.start()</code>, build the list,
<code>tracemalloc.get_traced_memory()</code>. The law test is three lines:
<code>with pytest.raises(dataclasses.FrozenInstanceError):
ptype.max_speed = 99</code>. Expect roughly a 3&ndash;5&times; drop, more
with <code>__slots__</code>.</p>"""},
},

# ---------------------------------------------------------------- proxy
{
"slug": "proxy", "name": "Proxy", "category": "structural",
"intent": "Stand in front of an object with the same interface and control access to it \u2014 lazily, protectively, remotely, or with a cache.",
"sections": [
("The problem", r"""
<p>Your gallery model loads the full 50&nbsp;MB image in
<code>__init__</code>. Listing a folder instantiates every image to show
three thumbnails and a filename &mdash; ten seconds of I/O for data nobody
looked at. You need the object to <em>exist</em> cheaply and pay its real
cost only if someone actually uses it.</p>""", None),
("The pattern", r"""
<p>A proxy implements the subject's interface and holds (or knows how to get)
the real subject, deciding <em>when and whether</em> calls reach it. The lazy
(&ldquo;virtual&rdquo;) variant solves the gallery:</p>""",
r"""
from typing import Protocol

class Image(Protocol):
    def display(self) -> str: ...

class RealImage:
    def __init__(self, path: str):
        print(f"loading 50 MB from {path}...")     # the expensive part
        self.path = path

    def display(self) -> str:
        return f"[pixels of {self.path}]"

class LazyImage:
    def __init__(self, path: str):
        self.path = path                            # cheap: no I/O
        self._real: RealImage | None = None

    def display(self) -> str:
        if self._real is None:                      # load on first use
            self._real = RealImage(self.path)
        return self._real.display()

gallery = [LazyImage(f"photo_{i}.raw") for i in range(1000)]  # instant
gallery[0].display()   # only now does photo_0 load
"""),
(None, r"""
<p>Same skeleton, different gatekeeping policies &mdash; the four classic
variants: <strong>virtual</strong> (lazy, above), <strong>protection</strong>
(check permissions before delegating), <strong>remote</strong> (the local
object is a stub forwarding over the network &mdash; every RPC client),
and <strong>caching/logging</strong> (memoize or record calls on the way
through).</p>""", None),
("The Pythonic twist", r"""
<p>Python's <code>__getattr__</code> fires only for attributes the object
<em>doesn't</em> have &mdash; which makes a transparent forwarding proxy
almost free, no interface re-typing required:</p>""",
r"""
class LoggingProxy:
    def __init__(self, target):
        self._target = target

    def __getattr__(self, name):
        attr = getattr(self._target, name)
        if callable(attr):
            def logged(*args, **kwargs):
                print(f"call: {name}{args}")
                return attr(*args, **kwargs)
            return logged
        return attr
"""),
(None, r"""
<p>And for the single most common lazy-attribute case,
<code>functools.cached_property</code> is a one-decorator virtual proxy for
one attribute. Proxy vs Decorator, since they're structurally twins: a
decorator <em>adds behavior</em> and always delegates; a proxy <em>controls
access</em> and may refuse, delay, or answer from cache without ever touching
the subject. Same shape, different contract.</p>""", None),
],
"wild": r"""
<p>Django's <code>request.user</code> is a <code>SimpleLazyObject</code>
&mdash; the DB query happens only if you touch it. ORM lazy relationships
(<code>order.customer</code> triggering a query) are virtual proxies; gRPC
and other RPC stubs are remote proxies; <code>weakref.proxy</code> is one by
name; <code>functools.cached_property</code> and <code>mock.Mock</code>
(recording every call) round out the family.</p>""",
"avoid": r"""
<p>Transparent laziness moves cost to a surprising moment &mdash; the classic
production bug is a &ldquo;cheap&rdquo; template render firing forty lazy DB
loads (the ORM N+1 problem is proxy laziness biting back). Magic
<code>__getattr__</code> proxies also confuse type checkers, IDEs, and
<code>isinstance</code>. If the object is cheap, or callers always use it
immediately, the proxy is pure indirection &mdash; skip it.</p>""",
"exercise": {
"text": r"""
<p>Given a <code>WeatherService</code> whose <code>forecast(city)</code>
sleeps 2 seconds (stub the slowness), build two stackable proxies sharing its
protocol: <code>CachingProxy(service, ttl_seconds)</code> that memoizes per
city with expiry, and <code>ProtectionProxy(service, user)</code> that raises
<code>PermissionError</code> unless <code>user.role == "admin"</code>.
Compose them both ways &mdash; <code>Protection(Caching(real))</code> vs
<code>Caching(Protection(real))</code> &mdash; and write down the security
difference. One of these orders has a hole.</p>""",
"code": None,
"hint": r"""<p>Cache entries as <code>{city: (timestamp, result)}</code>
checked against <code>time.monotonic()</code>. The hole:
<code>Caching(Protection(...))</code> means an admin's earlier call can be
served from cache to a non-admin if the cache sits <em>outside</em> the
guard&hellip; wait, check which wrapper sees the request first. Trace one
request through each stack by hand &mdash; that trace is the answer.</p>"""},
},
]
