/* ============================================================
   Signature Llama Compiler — js/compiler.js
   Pure build logic (no DOM) at the top so it can be tested in node.
   Page UI below, guarded so it only runs in a browser.
   ============================================================ */
"use strict";

/* ---------- pure helpers ---------- */
function escHtml(s){
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}

/* Build the custom Llama package from the selected add-on library objects.
   Each lib: {id,name,version,category,desc,functions,code}
   Returns {js, manifest, manifestJson}. The .js contains EXACTLY the
   selected add-ons' code, each under its own labeled banner. */
function buildBundle(libs, stamp){
  stamp = stamp || (new Date().toISOString().slice(0,10));
  var parts = [];
  parts.push("/* ============================================================");
  parts.push("   Signature Llama - custom build");
  parts.push("   Built: " + stamp + " with the on-page Llama Compiler");
  parts.push("   Add-ons inside: " + libs.length);
  libs.forEach(function(l, i){
    parts.push("   " + (i+1) + ". " + l.id + " - " + l.name + " (v" + (l.version||"?") + ")");
  });
  parts.push("   How to use: include this file AFTER sigllama.js (or llama-api.js).");
  parts.push("   Every add-on registers itself on window.SigLlama.tools['<id>'].");
  parts.push("   Independent build by Justin Addam Higgins. Not affiliated with Meta.");
  parts.push("   ============================================================ */");
  parts.push("(function(){");
  parts.push("var T = window.SigLlama = window.SigLlama || {};");
  parts.push("T.customBuild = { built: " + JSON.stringify(stamp) + ", addons: " +
    JSON.stringify(libs.map(function(l){return l.id;})) + " };");
  libs.forEach(function(l){
    parts.push("");
    parts.push("/* ----- add-on " + l.id + " | " + l.name + " v" + (l.version||"?") +
      " | " + (l.category||"") + " ----- */");
    parts.push(String(l.code || ""));
  });
  parts.push("})();");
  var js = parts.join("\n");

  var manifest = {
    built: stamp,
    generator: "Signature Llama Compiler (signature-llama/compiler.html)",
    count: libs.length,
    selections: libs.map(function(l){
      return { id: l.id, name: l.name, version: l.version || "1.0",
               category: l.category || "", functions: l.functions || [] };
    }),
    note: "Include signature-llama-custom.js after the core engine. Each add-on registers on window.SigLlama.tools['<id>']."
  };
  return { js: js, manifest: manifest, manifestJson: JSON.stringify(manifest, null, 1) };
}

/* Export for node tests */
if (typeof module !== "undefined" && module.exports){
  module.exports = { buildBundle: buildBundle, escHtml: escHtml };
}

/* ============================================================
   Page UI — browser only
   ============================================================ */
if (typeof document !== "undefined"){
(function(){
  var LIBS = [], TRAY = [];  /* TRAY = array of lib ids, in add order */
  var grid = document.getElementById("addonGrid"),
      trayEl = document.getElementById("tray"),
      trayCount = document.getElementById("trayCount"),
      q = document.getElementById("addonSearch"),
      result = document.getElementById("buildResult");

  function byId(id){
    for (var i=0;i<LIBS.length;i++) if (LIBS[i].id===id) return LIBS[i];
    return null;
  }
  function inTray(id){ return TRAY.indexOf(id) >= 0; }

  function cardHTML(l){
    var added = inTray(l.id);
    return '<div class="acard" data-id="'+escHtml(l.id)+'">' +
      '<div class="aname">'+escHtml(l.name)+
      (l.optimal ? ' <span class="best-tag">starter pick</span>' : '') + '</div>' +
      '<div class="ameta">'+escHtml(l.category||"")+' · v'+escHtml(l.version||"1.0")+'</div>' +
      '<div class="adesc">'+escHtml(l.desc||"")+'</div>' +
      '<button type="button" class="abtn" data-add="'+escHtml(l.id)+'"'+(added?' disabled':'')+'>'+
      (added ? '✓ In the tray' : '➕ Drop into compiler') + '</button></div>';
  }

  function renderGrid(){
    var term = (q.value||"").toLowerCase().trim();
    var html = "";
    LIBS.forEach(function(l){
      var hay = (l.name+" "+l.id+" "+(l.category||"")+" "+(l.desc||"")).toLowerCase();
      if (term && hay.indexOf(term) < 0) return;
      html += cardHTML(l);
    });
    grid.innerHTML = html || '<p class="dim">No add-ons match that search.</p>';
  }

  function renderTray(){
    trayCount.textContent = TRAY.length;
    if (!TRAY.length){
      trayEl.innerHTML = '<p class="dim">Your tray is empty. Tap “➕ Drop into compiler” on any add-on above.</p>';
      return;
    }
    trayEl.innerHTML = TRAY.map(function(id){
      var l = byId(id);
      return '<span class="tchip">'+escHtml(l ? l.name : id)+
        ' <button type="button" data-rm="'+escHtml(id)+'" aria-label="Remove">✕</button></span>';
    }).join("");
  }

  function refresh(){ renderGrid(); renderTray(); }

  grid.addEventListener("click", function(e){
    var b = e.target.closest("[data-add]");
    if (!b || b.disabled) return;
    var id = b.getAttribute("data-add");
    if (!inTray(id)){ TRAY.push(id); refresh(); }
  });
  trayEl.addEventListener("click", function(e){
    var b = e.target.closest("[data-rm]");
    if (!b) return;
    var id = b.getAttribute("data-rm");
    TRAY = TRAY.filter(function(x){ return x !== id; });
    refresh();
  });
  q.addEventListener("input", renderGrid);

  document.getElementById("addOptimal").addEventListener("click", function(){
    LIBS.forEach(function(l){ if (l.optimal && !inTray(l.id)) TRAY.push(l.id); });
    refresh();
  });
  document.getElementById("clearTray").addEventListener("click", function(){
    TRAY = []; result.hidden = true; refresh();
  });

  function download(filename, text, mime){
    var blob = new Blob([text], {type: mime || "text/plain;charset=utf-8"});
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); }, 800);
  }
  function copyText(text, btn){
    function done(){ var o=btn.textContent; btn.textContent="✓ Copied!"; setTimeout(function(){btn.textContent=o;},1500); }
    if (navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(done, function(){ fallback(); });
    } else fallback();
    function fallback(){
      var ta = document.createElement("textarea");
      ta.value = text; ta.style.position="fixed"; ta.style.opacity="0";
      document.body.appendChild(ta); ta.select();
      try{ document.execCommand("copy"); }catch(e){}
      ta.remove(); done();
    }
  }

  var lastBuild = null;
  document.getElementById("buildBtn").addEventListener("click", function(){
    if (!TRAY.length){
      result.hidden = false;
      result.innerHTML = '<p class="dim"><b>Your tray is empty.</b> Add at least one add-on above, then build.</p>';
      return;
    }
    var libs = TRAY.map(byId).filter(Boolean);
    lastBuild = buildBundle(libs);
    var inside = libs.map(function(l){
      return '<li><b>'+escHtml(l.name)+'</b> <span class="dim">('+escHtml(l.id)+' v'+escHtml(l.version||"1.0")+')</span></li>';
    }).join("");
    result.hidden = false;
    result.innerHTML =
      '<h3>🎉 Your Llama is built!</h3>' +
      '<p>'+libs.length+' add-on'+(libs.length===1?'':'s')+' inside. The files below contain <b>exactly</b> what you picked — nothing more, nothing less.</p>' +
      '<p class="dim" style="font-size:.85em">What\u2019s inside:</p><ul class="inside">'+inside+'</ul>' +
      '<div class="brow">' +
      '<button type="button" class="big gold" id="dlJs">⤓ Download signature-llama-custom.js</button>' +
      '<button type="button" class="big" id="dlJson">⤓ Download build list (.json)</button>' +
      '</div><div class="brow">' +
      '<button type="button" class="big" id="cpJs">📋 Copy the .js</button>' +
      '<button type="button" class="big" id="cpJson">📋 Copy the build list</button>' +
      '</div>' +
      '<p class="dim" style="font-size:.85em">Use it: put <code>signature-llama-custom.js</code> on your page after the core engine. Each add-on lives at <code>window.SigLlama.tools["&lt;id&gt;"]</code>.</p>';
    document.getElementById("dlJs").addEventListener("click", function(){
      download("signature-llama-custom.js", lastBuild.js, "text/javascript;charset=utf-8");
    });
    document.getElementById("dlJson").addEventListener("click", function(){
      download("signature-llama-custom-build.json", lastBuild.manifestJson, "application/json;charset=utf-8");
    });
    document.getElementById("cpJs").addEventListener("click", function(){ copyText(lastBuild.js, this); });
    document.getElementById("cpJson").addEventListener("click", function(){ copyText(lastBuild.manifestJson, this); });
    result.scrollIntoView({behavior:"smooth", block:"start"});
  });

  fetch("data/tool-libraries.json").then(function(r){
    if(!r.ok) throw new Error("http "+r.status);
    return r.json();
  }).then(function(j){
    LIBS = j.libraries || [];
    document.getElementById("libCount").textContent = LIBS.length;
    refresh();
  }).catch(function(){
    grid.innerHTML = '<p class="dim">Could not load the add-on list. Check your connection and reload.</p>';
  });
})();
}
