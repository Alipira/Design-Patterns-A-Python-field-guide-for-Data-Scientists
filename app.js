/* GoF Field Guide — shared behavior. No dependencies, works from file://. */
(function () {
  "use strict";

  /* ---------- tiny Python syntax highlighter ---------- */
  var KW = "def|class|return|if|elif|else|for|while|in|not|and|or|is|None|True|False|import|from|as|pass|raise|try|except|finally|with|lambda|yield|global|nonlocal|del|assert|async|await|match|case|break|continue";
  var master = new RegExp(
    "(#[^\\n]*)" +                                             // 1 comment
    "|(\"\"\"[\\s\\S]*?\"\"\"|'''[\\s\\S]*?'''" +              // 2 strings
    "|f?\"(?:\\\\.|[^\"\\\\\\n])*\"|f?'(?:\\\\.|[^'\\\\\\n])*')" +
    "|(@[A-Za-z_][\\w.]*)" +                                   // 3 decorator
    "|\\b(" + KW + ")\\b" +                                    // 4 keyword
    "|\\b(self|cls)\\b" +                                      // 5 self
    "|\\b(\\d+(?:\\.\\d+)?)\\b",                               // 6 number
    "g"
  );

  function highlight(codeEl) {
    var src = codeEl.textContent;
    var frag = document.createDocumentFragment();
    var last = 0, m;
    master.lastIndex = 0;
    while ((m = master.exec(src)) !== null) {
      if (m.index > last) frag.appendChild(document.createTextNode(src.slice(last, m.index)));
      var cls = m[1] ? "tok-c" : m[2] ? "tok-s" : m[3] ? "tok-d" :
                m[4] ? "tok-k" : m[5] ? "tok-self" : "tok-n";
      var span = document.createElement("span");
      span.className = cls;
      span.textContent = m[0];
      frag.appendChild(span);
      last = m.index + m[0].length;
    }
    if (last < src.length) frag.appendChild(document.createTextNode(src.slice(last)));
    codeEl.textContent = "";
    codeEl.appendChild(frag);
    // second pass: names after def/class get the function color
    codeEl.querySelectorAll(".tok-k").forEach(function (k) {
      if (k.textContent === "def" || k.textContent === "class") {
        var next = k.nextSibling;
        if (next && next.nodeType === 3) {
          var t = next.textContent, mm = /^(\s+)([A-Za-z_]\w*)/.exec(t);
          if (mm) {
            var name = document.createElement("span");
            name.className = "tok-fn";
            name.textContent = mm[2];
            var rest = document.createTextNode(t.slice(mm[0].length));
            next.textContent = mm[1];
            k.parentNode.insertBefore(name, next.nextSibling);
            k.parentNode.insertBefore(rest, name.nextSibling);
          }
        }
      }
    });
  }

  /* ---------- progress tracking (index page) ---------- */
  function store(key, val) {
    try {
      if (val === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, val);
    } catch (e) { return null; }
  }

  function initProgress() {
    var boxes = document.querySelectorAll(".chip input[type=checkbox]");
    if (!boxes.length) return;
    var counter = document.getElementById("progress-count");
    function refresh() {
      var done = document.querySelectorAll(".chip input:checked").length;
      if (counter) counter.textContent = done + " / " + boxes.length + " studied";
    }
    boxes.forEach(function (b) {
      if (store("gof-" + b.dataset.slug) === "1") b.checked = true;
      b.addEventListener("change", function () {
        store("gof-" + b.dataset.slug, b.checked ? "1" : "0");
        refresh();
      });
      // don't navigate when clicking the checkbox inside the link
      b.addEventListener("click", function (e) { e.stopPropagation(); });
    });
    refresh();
  }

  /* ---------- arrow-key navigation between lessons ---------- */
  function initKeys() {
    var prev = document.querySelector('a[rel="prev"]');
    var next = document.querySelector('a[rel="next"]');
    document.addEventListener("keydown", function (e) {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
      if (e.key === "ArrowLeft" && prev) location.href = prev.getAttribute("href");
      if (e.key === "ArrowRight" && next) location.href = next.getAttribute("href");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("pre code").forEach(highlight);
    initProgress();
    initKeys();
  });
})();
