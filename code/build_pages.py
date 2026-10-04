#!/usr/bin/env python3
"""Assemble archive.html, compiler.html, showcase.html for signature-llama.
Inlines the verified shared blocks (jahnet nav, theme toggle, footer) so all
pages match the site's existing chrome. Run from the repo root."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
jahnet = open('/tmp/jahnet_block.html').read()
theme = open('/tmp/theme_block.html').read()
footer = open('/tmp/footer_block.html').read()

TABS = {
    'index':    ('&#127968; Main', 'archive'),
    'archive':  ('&#128449; Archive', 'archive'),
    'compiler': ('&#9881;&#65039; Compiler', 'compiler'),
    'showcase': ('&#9733; Best of the Best', 'showcase'),
}

def tabbar(active):
    links = []
    for key, (label, _) in [('index', TABS['index']), ('archive', TABS['archive']),
                            ('compiler', TABS['compiler']), ('showcase', TABS['showcase'])]:
        href = 'index.html' if key == 'index' else key + '.html'
        cls = 'tablink on' if key == active else 'tablink'
        aria = ' aria-current="page"' if key == active else ''
        links.append('<a class="%s" href="%s"%s>%s</a>' % (cls, href, aria, label))
    return '<nav class="jah-tabs" aria-label="Llama pages">' + ''.join(links) + '</nav>'

BASE_CSS = """:root{--bg:#070b14;--panel:#0d1424;--panel2:#111a30;--line:#1e2c4d;--txt:#d7e0f2;--dim:#8b98b8;--gold:#e8c766;--amber:#ffc93c;--amber2:#ffdf7e;--acc:#5aa2ff;--grn:#5aff8a;--red:#ff5a5a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:Georgia,'Times New Roman',serif;line-height:1.55}
.jahnet{background:#0a0f1e;color:#9aa4b2;font-size:.76em;padding:7px 10px;text-align:center;line-height:2;letter-spacing:.02em;border-bottom:1px solid var(--line)}
.jahnet-t{color:var(--gold);font-weight:700;letter-spacing:.25em;margin-right:10px}
.jahnet a{color:#9fc2ff;text-decoration:none;margin:0 7px;white-space:nowrap}
.jahnet a:hover{text-decoration:underline}
.jahnet .cur{color:var(--gold);font-weight:700;margin:0 7px}
/* calculator-style tab bar (Manon's order: Main page --> Archive) */
.jah-tabs{display:flex;gap:6px;overflow-x:auto;padding:10px 12px;background:var(--panel2);border-bottom:2px solid var(--gold)}
.jah-tabs a.tablink{flex:0 0 auto;background:var(--panel);color:var(--txt);border:1px solid var(--line);border-radius:6px;padding:9px 14px;font-size:.92em;cursor:pointer;text-decoration:none;font-family:Arial,Helvetica,sans-serif;white-space:nowrap}
.jah-tabs a.tablink.on{background:var(--gold);color:#241a02;font-weight:700;border-color:var(--gold)}
.hero{max-width:960px;margin:0 auto;padding:26px 14px 10px}
.sitekicker{display:inline-block;color:var(--gold);font-weight:700;letter-spacing:.2em;font-size:.85em;border:1px solid var(--gold);border-radius:3px;padding:1px 8px;margin:0 0 10px;white-space:nowrap}
.hero h1{margin:.1em 0 .2em;font-size:1.9em;color:var(--txt)}
.hero .offname{color:var(--amber2);letter-spacing:.12em;font-weight:700;margin:.1em 0 .6em}
.hero p.lead{max-width:660px}
.wrap{max-width:960px;margin:0 auto;padding:14px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:16px}
.panel h2{margin:0 0 4px;font-size:1.15em;color:var(--gold);letter-spacing:1px}
.panel .sub{color:var(--dim);font-size:.88em;margin:0 0 12px}
.dim{color:var(--dim)}
input[type=text]{background:#0b111c;color:var(--txt);border:1px solid var(--line);border-radius:6px;padding:11px;font-size:1em;width:100%}
button.big{background:#1a2340;border:1px solid var(--amber);color:var(--amber2);border-radius:8px;padding:11px 18px;font-size:1em;cursor:pointer;margin:6px 6px 6px 0;font-family:inherit}
button.big:hover{background:#232c52}
button.big.gold{background:var(--gold);border-color:var(--gold);color:#241a02;font-weight:800}
button.big:disabled{opacity:.5;cursor:default}
.footer{text-align:center;color:var(--dim);font-size:.82em;padding:26px 12px 60px;border-top:1px solid var(--line);margin-top:10px}
.footer .sig{color:var(--gold);letter-spacing:.25em;font-weight:700}
#jah-theme-toggle{position:fixed;right:14px;bottom:14px;z-index:99999;width:40px;height:40px;border-radius:50%;border:1px solid var(--gold);background:#0a0f1e;color:var(--gold);font-size:20px;line-height:1;cursor:pointer;opacity:.7}
html[data-theme="dark"]{filter:invert(1) hue-rotate(180deg)}
html[data-theme="dark"] img{filter:invert(1) hue-rotate(180deg)}
a{color:var(--acc)}
code{background:#0b1120;border:1px solid var(--line);border-radius:4px;padding:1px 6px;font-size:.88em}
"""

AZ_CSS = """.azgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(64px,1fr));gap:6px;margin:10px 0}
.azgrid details{border:1px solid var(--line);border-radius:8px;background:var(--panel2);overflow:hidden}
.azgrid details[open]{border-color:var(--gold);grid-column:1/-1}
.azgrid summary{list-style:none;cursor:pointer;padding:10px 6px;text-align:center;font-weight:700;color:var(--amber2);font-size:1.1em;user-select:none;-webkit-tap-highlight-color:transparent}
.azgrid summary::-webkit-details-marker{display:none}
.azgrid details[open] summary{background:#1a2340;border-bottom:1px solid var(--line)}
.azlist{padding:8px;display:grid;gap:6px}
.azlist a.bent{display:flex;align-items:center;gap:8px;text-decoration:none;color:var(--txt);background:#0b1120;border:1px solid var(--line);border-radius:6px;padding:8px 10px;font-size:.92em}
.azlist a.bent:hover{border-color:var(--gold)}
.azlist a.bent .go{margin-left:auto;color:var(--gold);font-weight:700;white-space:nowrap;font-size:.85em}
.azlist .bcat{font-size:.72em;letter-spacing:.08em;color:var(--dim);border:1px solid var(--line);border-radius:999px;padding:1px 8px;white-space:nowrap}
.azloading{padding:10px;color:var(--dim);font-size:.85em;font-style:italic}
"""

def page(title, desc, canonical, active, body_html, extra_css="", extra_head=""):
    return """<!DOCTYPE html>
<html lang="en">
<head>
<script>try{if(localStorage.getItem("jah-theme")==="dark")document.documentElement.dataset.theme="dark";}catch(e){}</script>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="https://justinahiggins614-cmyk.github.io/signature-llama/%s">
<style>%s%s</style>
%s</head>
<body>
%s
%s
%s
%s
</body>
</html>
""" % (title, desc, canonical, BASE_CSS, extra_css, extra_head, theme, jahnet, tabbar(active), body_html + footer)

# ---------------------------------------------------------------- archive.html
AZ_JS = r"""
/* Archive A-Z (lazy, same pattern as browse.html) + Ask-the-AI helper */
(function(){
"use strict";
var IDX=null, FULL=null;
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function loadIdx(){
  if(IDX) return Promise.resolve(IDX);
  return fetch("data/browse-index.json").then(function(r){if(!r.ok)throw 0;return r.json();})
    .then(function(j){IDX=j;return j;});
}
function letterOf(n){var c=String(n||"").trim().charAt(0).toUpperCase();return (c>="A"&&c<="Z")?c:"#";}
function group(items,fn){var g={};items.forEach(function(it){var L=letterOf(fn(it));(g[L]=g[L]||[]).push(it);});
  Object.keys(g).forEach(function(L){g[L].sort(function(a,b){return fn(a).toLowerCase().localeCompare(fn(b).toLowerCase());});});return g;}
var LETTERS="ABCDEFGHIJKLMNOPQRSTUVWXYZ#".split("");
function buildAZ(gridId, items, isTool){
  var grid=document.getElementById(gridId); if(!grid) return;
  var groups=group(items, function(it){return isTool?it.name:it.t;});
  var wrap=document.createElement("div");wrap.className="azgrid";grid.appendChild(wrap);
  LETTERS.forEach(function(L){
    var list=groups[L]||[];
    var d=document.createElement("details"), s=document.createElement("summary");
    s.innerHTML=esc(L)+(list.length?' <span style="font-weight:400;font-size:.72em;color:var(--dim)">('+list.length+")</span>":"");
    if(!list.length)d.style.opacity=".45";
    var body=document.createElement("div");body.className="azlist";
    body.innerHTML='<div class="azloading">'+(list.length?"Loading&hellip;":"Nothing under this letter.")+"</div>";
    d.appendChild(s);d.appendChild(body);wrap.appendChild(d);
    var filled=false;
    d.addEventListener("toggle",function(){
      if(!d.open||filled)return;filled=true;
      body.innerHTML=list.map(function(it){
        var name=isTool?it.name:it.t, cat=isTool?it.cat:it.c;
        var link=isTool?("index.html?toollib="+encodeURIComponent(it.id)):("index.html?term="+encodeURIComponent(it.t));
        return '<a class="bent" href="'+link+'"><span>'+esc(name)+'</span><span class="bcat">'+esc(cat||"")+'</span><span class="go">Open &rarr;</span></a>';
      }).join("")||'<div class="azloading">Nothing under this letter.</div>';
    });
  });
}
loadIdx().then(function(j){
  document.getElementById("termn").textContent=j.term_count;
  document.getElementById("tooln").textContent=j.tool_count;
  document.getElementById("bcount").textContent=j.term_count+" AI terms \u00b7 "+j.tool_count+" tool libraries";
  buildAZ("termaz", j.terms, false);
  buildAZ("toolaz", j.tools, true);
}).catch(function(){
  document.getElementById("termaz").innerHTML='<p class="dim">Could not load the archive. Check your connection and reload.</p>';
});
/* ---- Ask the AI about this archive: keyword finder over the real data ---- */
var askBtn=document.getElementById("askBtn"), askQ=document.getElementById("askq"), askR=document.getElementById("askres");
function fullDefs(){
  if(FULL) return Promise.resolve(FULL);
  return Promise.all([
    fetch("data/llm-dictionary.json").then(function(r){return r.json();}),
    fetch("data/tool-libraries.json").then(function(r){return r.json();})
  ]).then(function(p){
    var terms=p[0].terms||[], libs=p[1].libraries||[];
    FULL=terms.map(function(t){return {kind:"term",name:t.t,cat:t.c,text:t.d||"",link:"index.html?term="+encodeURIComponent(t.t)};})
      .concat(libs.map(function(l){return {kind:"tool",name:l.name,cat:l.category||"",text:l.desc||"",link:"index.html?toollib="+encodeURIComponent(l.id)};}));
    return FULL;
  });
}
function answer(){
  var q=(askQ.value||"").trim().toLowerCase();
  if(!q){askR.innerHTML='<p class="dim">Type a question first — for example “what is a token?” or “tools for long text”.</p>';return;}
  askR.innerHTML='<p class="dim">Thinking&hellip;</p>';
  var words=q.replace(/[?.,!]/g,"").split(/\s+/).filter(function(w){return w.length>2;});
  fullDefs().then(function(items){
    var scored=items.map(function(it){
      var hay=(it.name+" "+it.cat+" "+it.text).toLowerCase(), s=0;
      words.forEach(function(w){ if(it.name.toLowerCase().indexOf(w)>=0)s+=3; else if(hay.indexOf(w)>=0)s+=1; });
      return {it:it,s:s};
    }).filter(function(x){return x.s>0;}).sort(function(a,b){return b.s-a.s;}).slice(0,6);
    if(!scored.length){
      askR.innerHTML='<p><b>No matches in this archive.</b></p><p class="dim">Try fewer words, or browse the A&ndash;Z lists below. You can also ask the full Llama on the <a href="index.html#chat">main page chat</a>.</p>';
      return;
    }
    var html='<p><b>Here is what I found about &ldquo;'+esc(askQ.value.trim())+'&rdquo;:</b></p>';
    html+=scored.map(function(x){
      return '<div class="ans"><b>'+esc(x.it.name)+'</b> <span class="bcat">'+esc(x.it.cat||x.it.kind)+'</span><br>'+
        '<span class="dim">'+esc(x.it.text.slice(0,180))+(x.it.text.length>180?"&hellip;":"")+'</span><br>'+
        '<a href="'+x.it.link+'">Open the full record &rarr;</a></div>';
    }).join("");
    askR.innerHTML=html;
  }).catch(function(){
    askR.innerHTML='<p class="dim">The archive data did not load. Check your connection and try again.</p>';
  });
}
askBtn.addEventListener("click",answer);
askQ.addEventListener("keydown",function(e){if(e.key==="Enter")answer();});
})();
"""

archive_body = """
<div class="hero">
  <p class="sitekicker">SITE 6 OF 27 &middot; THE JAH NETWORK</p>
  <h1>The Signature Llama Archive</h1>
  <p class="offname">EVERY AI TERM &middot; EVERY TOOL LIBRARY &middot; EVERY BUILD &mdash; A TO Z</p>
  <p class="lead">The words that make the Llama tick, every plug-in tool that makes it smarter, and every released build &mdash; the complete catalog, in one place. Open a letter to browse; the page only loads what you open.</p>
  <p><b id="bcount">Loading&hellip;</b></p>
</div>
<div class="wrap">
  <div class="panel" style="border:2px solid var(--acc)">
    <h2>&#129302; ASK THE AI ABOUT THIS ARCHIVE</h2>
    <p class="sub">Plain words in, answers out. The helper searches every term, tool, and build in this archive and points you to the full records.</p>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <input type="text" id="askq" style="flex:1;min-width:200px" placeholder="Ask anything &mdash; e.g. &ldquo;what is a token?&rdquo;" aria-label="Ask about the archive">
      <button type="button" class="big gold" id="askBtn">Ask</button>
    </div>
    <div id="askres" style="margin-top:10px" aria-live="polite"></div>
  </div>
  <div class="panel" style="border:2px solid var(--gold)">
    <h2>&#9733; LLM / AI DICTIONARY &mdash; <span id="termn">&hellip;</span> ORIGINAL TERMS</h2>
    <p class="sub">The Signature original definitions behind the Llama. Each term opens its full record on the main page.</p>
    <div id="termaz"></div>
  </div>
  <div class="panel" style="border:2px solid var(--amber)">
    <h2>&#9733; TOOL LIBRARY &mdash; <span id="tooln">&hellip;</span> PLUG-IN LIBRARIES</h2>
    <p class="sub">Every plug-in add-on &mdash; text, thinking, memory, chat, search, math, web, data, voice, safety, embedding and fun. Each opens its full record on the main page.</p>
    <div id="toolaz"></div>
  </div>
  <div class="panel">
    <h2>&#128230; RELEASED BUILDS</h2>
    <p class="sub">Whole-Llama packages you can download and use.</p>
    <ul>
      <li><b>&#10022; Signature Llama v2</b> &mdash; the on-device engine. <a href="index.html#chat">Talk to it on the main page</a>.</li>
      <li><b>&#11022; Industry Standard</b> &mdash; the full-scale cloud option. <a href="index.html#chat">Set it up on the main page</a>.</li>
      <li><b>signature-llama-patch-v2.zip</b> &mdash; everything in one patch. <a href="patch/signature-llama-patch-v2.zip" download>Download v2</a> (<a href="patch/signature-llama-patch-v2.zip.sha256">sha256</a>)</li>
      <li><b>signature-llama-patch-v1.zip</b> &mdash; the first patch. <a href="patch/signature-llama-patch-v1.zip" download>Download v1</a></li>
      <li><b>sigllama v1 engine</b> &mdash; the tiny core. <a href="sigllama/v1/sigllama.js" download>sigllama.js</a></li>
      <li><b>Want your own mix?</b> &mdash; pick add-ons and build it on the <a href="compiler.html">Compiler page</a>.</li>
    </ul>
  </div>
</div>
<script>%s</script>
""" % AZ_JS

# ---------------------------------------------------------------- compiler.html
COMPILER_CSS = """.acard{background:#0b1120;border:1px solid var(--line);border-radius:8px;padding:10px;display:flex;flex-direction:column;gap:6px}
.agrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;margin-top:10px}
.aname{font-weight:700;color:var(--txt)}
.ameta{font-size:.75em;color:var(--dim);letter-spacing:.04em}
.adesc{font-size:.85em;color:var(--dim);flex:1}
.best-tag{font-size:.68em;background:var(--gold);color:#241a02;border-radius:999px;padding:1px 8px;font-weight:700;letter-spacing:.06em}
.abtn{background:#1a2340;border:1px solid var(--amber);color:var(--amber2);border-radius:6px;padding:9px;font-size:.9em;cursor:pointer}
.abtn:disabled{opacity:.55;cursor:default;border-color:var(--line);color:var(--dim)}
.tchip{display:inline-block;background:#1a2340;border:1px solid var(--gold);color:var(--amber2);border-radius:999px;padding:6px 8px 6px 12px;margin:4px;font-size:.88em}
.tchip button{background:none;border:0;color:var(--red);cursor:pointer;font-size:1em;padding:2px 6px}
.brow{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.inside{columns:2;font-size:.9em}
@media(max-width:600px){.inside{columns:1}}
.ans{background:#0b1120;border:1px solid var(--line);border-radius:8px;padding:10px;margin:8px 0}
.steps{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 12px}
.step{flex:1;min-width:160px;background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:10px;font-size:.88em}
.step b{color:var(--gold)}
"""

compiler_body = """
<div class="hero">
  <p class="sitekicker">SITE 6 OF 27 &middot; THE JAH NETWORK</p>
  <h1>The Llama Compiler</h1>
  <p class="offname">PICK ADD-ONS &middot; DROP THEM IN &middot; BUILD YOUR LLAMA</p>
  <p class="lead">This page builds you a <b>real, working</b> custom Llama file. Pick any add-ons below, drop them into the compiler tray, and hit <b>Build</b>. You get a file to download (or copy) that contains <b>exactly</b> what you picked &mdash; nothing more, nothing less. <span class="dim"><span id="libCount">&hellip;</span> add-ons available.</span></p>
</div>
<div class="wrap">
  <div class="steps">
    <div class="step"><b>Step 1.</b> Pick add-ons below (tap &ldquo;Drop into compiler&rdquo;).</div>
    <div class="step"><b>Step 2.</b> Check your tray &mdash; remove any you changed your mind about.</div>
    <div class="step"><b>Step 3.</b> Hit <b>Build my Llama</b> &mdash; download or copy the finished file.</div>
  </div>
  <div class="panel">
    <h2>&#10133; STEP 1 &mdash; PICK YOUR ADD-ONS</h2>
    <p class="sub">Every plug-in tool library on this site. Use search to narrow it down.</p>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px">
      <input type="text" id="addonSearch" style="flex:1;min-width:200px" placeholder="Search add-ons&hellip; (try &ldquo;text&rdquo;, &ldquo;voice&rdquo;, &ldquo;math&rdquo;)" aria-label="Search add-ons">
      <button type="button" class="big" id="addOptimal">&#9733; Add the best starter set</button>
    </div>
    <div class="agrid" id="addonGrid"><p class="dim">Loading add-ons&hellip;</p></div>
  </div>
  <div class="panel" style="border:2px solid var(--gold)">
    <h2>&#129717; STEP 2 &mdash; YOUR COMPILER TRAY (<span id="trayCount">0</span>)</h2>
    <p class="sub">These add-ons go into your build. Tap &#10005; to take one back out.</p>
    <div id="tray"><p class="dim">Your tray is empty. Tap &ldquo;&#10133; Drop into compiler&rdquo; on any add-on above.</p></div>
    <div style="margin-top:8px"><button type="button" class="big" id="clearTray">Clear the tray</button></div>
  </div>
  <div class="panel" style="border:2px solid var(--grn)">
    <h2>&#128296; STEP 3 &mdash; BUILD</h2>
    <p class="sub">Compiles your tray into one working file, made from the add-ons&rsquo; real code.</p>
    <button type="button" class="big gold" id="buildBtn" style="font-size:1.1em;padding:14px 26px">&#128296; Build my Llama</button>
    <div id="buildResult" hidden style="margin-top:12px"></div>
  </div>
</div>
<script src="js/compiler.js"></script>
"""

# ---------------------------------------------------------------- showcase.html
SHOWCASE_JS = r"""
(function(){
"use strict";
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
Promise.all([
  fetch("data/best/best.json").then(function(r){return r.json();}),
  fetch("data/best/changelog.json").then(function(r){return r.json();}).catch(function(){return [];})
]).then(function(p){
  var b=p[0], log=p[1]||[];
  var comp=b.components||{};
  var libs=(comp.tool_libraries||[]).map(function(l){return esc(l.name);}).join(", ");
  document.getElementById("bestTitle").textContent=b.title;
  document.getElementById("bestTag").textContent=b.tagline||"";
  document.getElementById("bestWhy").innerHTML=(b.why||[]).map(function(w){return "<li>"+esc(w)+"</li>";}).join("");
  document.getElementById("bestMeta").innerHTML=
    '<span class="bcat">pick v'+esc(b.version)+'</span> '+
    '<span class="bcat">built '+esc(b.built)+'</span> '+
    '<span class="bcat">'+esc(b.stats?b.stats.tool_libraries_total:"")+' tool libraries on site</span>';
  document.getElementById("bestParts").innerHTML=
    "<li><b>Core engine:</b> "+esc(comp.core_engine?comp.core_engine.name:"")+"</li>"+
    "<li><b>Cloud option:</b> "+esc(comp.cloud_option?comp.cloud_option.name:"")+"</li>"+
    "<li><b>Starter tool set ("+((comp.tool_libraries||[]).length)+"):</b> "+libs+"</li>"+
    "<li><b>Patch bundle:</b> "+esc(comp.patch_bundle?comp.patch_bundle.name:"")+"</li>"+
    "<li><b>Building blocks:</b> "+esc(comp.inventory?comp.inventory.name:"")+"</li>";
  document.getElementById("changelog").innerHTML=log.slice().reverse().map(function(e){
    return '<div class="ans"><b>v'+esc(e.version)+' &mdash; '+esc(e.date)+'</b><br><span class="dim">'+esc(e.change)+'</span></div>';
  }).join("")||'<p class="dim">No changes yet.</p>';
}).catch(function(){
  document.getElementById("bestBox").innerHTML='<p class="dim">The showcase data did not load. Check your connection and reload.</p>';
});
})();
"""

showcase_body = """
<div class="hero">
  <p class="sitekicker">SITE 6 OF 27 &middot; THE JAH NETWORK</p>
  <h1>&#9733; Best of the Best</h1>
  <p class="offname">THE MIX-AND-MATCH SHOWCASE &mdash; ONE CONSTANT FLAGSHIP</p>
  <p class="lead">One Llama to show off: the best-structured, most universally capable build on this site. An AI reviews every update in the background and refreshes this pick whenever something better arrives &mdash; the full history is below.</p>
</div>
<div class="wrap">
  <div class="panel" id="bestBox" style="border:2px solid var(--gold)">
    <h2 id="bestTitle">Loading&hellip;</h2>
    <p class="sub" id="bestTag"></p>
    <p id="bestMeta"></p>
    <p><b>Why this one is the best:</b></p>
    <ul id="bestWhy"></ul>
    <p><b>What is inside:</b></p>
    <ul id="bestParts"></ul>
    <div class="brow">
      <a href="index.html#chat"><button type="button" class="big gold">&#128172; Try the flagship &mdash; talk to it</button></a>
      <a href="compiler.html"><button type="button" class="big">&#9881;&#65039; Or build your own mix</button></a>
    </div>
  </div>
  <div class="panel">
    <h2>&#128203; CHANGELOG &mdash; EVERY TIME THE BEST GOT BETTER</h2>
    <p class="sub">The background AI writes here whenever a new add-on or build beats the current pick.</p>
    <div id="changelog"><p class="dim">Loading&hellip;</p></div>
  </div>
</div>
<script>%s</script>
""" % SHOWCASE_JS

open(os.path.join(ROOT, 'archive.html'), 'w').write(page(
    "Archive — Signature Llama: Every Term, Tool & Build A–Z",
    "The complete Signature Llama catalog: every AI term, every plug-in tool library, and every released build, A to Z, with an AI helper to find answers.",
    "archive.html", "archive", archive_body, AZ_CSS + ".ans{background:#0b1120;border:1px solid var(--line);border-radius:8px;padding:10px;margin:8px 0}\n"))
open(os.path.join(ROOT, 'compiler.html'), 'w').write(page(
    "Llama Compiler — Build Your Own Signature Llama",
    "Pick add-ons, drop them into the compiler tray, and build a real custom Signature Llama file to download or copy.",
    "compiler.html", "compiler", compiler_body, COMPILER_CSS))
open(os.path.join(ROOT, 'showcase.html'), 'w').write(page(
    "Best of the Best — the Signature Llama Showcase",
    "The one constant flagship: the best-structured, most universally capable Signature Llama build, refreshed by an AI reviewer on every update.",
    "showcase.html", "showcase", showcase_body, ".ans{background:#0b1120;border:1px solid var(--line);border-radius:8px;padding:10px;margin:8px 0}\n.bcat{font-size:.72em;letter-spacing:.08em;color:var(--dim);border:1px solid var(--line);border-radius:999px;padding:1px 8px;white-space:nowrap}\n.brow{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}\n"))

print("wrote archive.html, compiler.html, showcase.html")
