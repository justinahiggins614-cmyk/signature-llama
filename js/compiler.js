/* ============================================================
   Signature Llama Compiler — js/compiler.js
   Add-ons workshop: pick a base Llama, add/examine/interview
   add-ons, compile a real custom build (JS + Python package +
   manifest), name it (profanity-checked), and file it.

   Pure build logic at the top (no DOM) so it can be tested in
   node. Page UI below, guarded so it only runs in a browser.
   ============================================================ */
"use strict";

/* ---------- pure helpers ---------- */
function escHtml(s){
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}

/* ---------- the three base Llamas ---------- */
var LLAMA_BASES = [
  { id: "basic",
    name: "Basic Llama",
    tag: "the plain baseline",
    desc: "The plain baseline Llama \u2014 the same talking brain inside every AI in the Signature AI Telephone Book. Small, on-device, no keys, no fees. Pick this when you want the pure Signature model with your add-ons.",
    engine: "sigllama.js + SIGLLAMA-V2 weights (on-device)" },
  { id: "v2",
    name: "Signature Llama v2 (on-device)",
    tag: "the released build",
    desc: "The released on-device build \u2014 4,056,768 parameters, 5 layers, 96-word context, int8 weights that download in seconds. The full v2 patch bundle is included. Pick this for the strongest local Llama with your add-ons.",
    engine: "sigllama.js + sigllama-v2.bin (on-device, SHA-256 verified)" },
  { id: "industry",
    name: "Llama \u00B7 Industry Standard (cloud)",
    tag: "the full-scale cloud option",
    desc: "The full-scale cloud Llama the industry runs (served live by Groq, 128k context) \u2014 needs a free API key you paste on the main page. Your add-ons ride along as page tools. Pick this when you want maximum brainpower. Independent site \u2014 not affiliated with Meta.",
    engine: "industry-llama.js via Groq (cloud, bring-your-own free key)" }
];
function baseById(id){
  for (var i=0;i<LLAMA_BASES.length;i++) if (LLAMA_BASES[i].id===id) return LLAMA_BASES[i];
  return LLAMA_BASES[0];
}

/* ---------- Llama name check (profanity blocklist) ---------- */
var CURSES = ("fuck fucking fucker fucked shit shitty shite bitch bitches bastard "+
"dick dickhead cock cocksucker pussy pussies cunt whore slut motherfucker "+
"asshole arsehole nigger nigga fag faggot retard retarded twat wanker tosser "+
"bollocks bugger damn goddamn hell crap piss pissed jizz cum tits boob").split(" ");
function checkLlamaName(name){
  var n = String(name||"").trim();
  if (!n) return { ok:false, msg:"Give your Llama a name first \u2014 type one above." };
  if (n.length > 48) return { ok:false, msg:"Keep the name under 48 characters." };
  var words = n.toLowerCase().replace(/[^a-z\s]/g," ").split(/\s+/);
  for (var i=0;i<words.length;i++){
    if (CURSES.indexOf(words[i]) >= 0)
      return { ok:false, msg:"Let\u2019s pick another name \u2014 that one isn\u2019t allowed here." };
  }
  if (/^[a-z0-9 _\-'.()]+$/i.test(n)) return { ok:true, name:n };
  return { ok:false, msg:"Use letters, numbers, spaces and simple punctuation only." };
}

/* ---------- SHA-256 (compact, standard) : hex of a UTF-8 string ---------- */
function sha256hex(str){
  function rr(x,n){ return (x>>>n)|(x<<(32-n)); }
  var K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
   0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
   0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
   0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
   0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
   0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
   0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
   0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  var H=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
  var bytes=[];
  for (var i=0;i<str.length;i++){
    var c=str.charCodeAt(i);
    if (c<128) bytes.push(c);
    else if (c<2048) bytes.push(192|(c>>6),128|(c&63));
    else if (c>=55296&&c<57344&&i+1<str.length){ i++; var c2=str.charCodeAt(i);
      var cp=65536+((c&1023)<<10)+(c2&1023);
      bytes.push(240|(cp>>18),128|((cp>>12)&63),128|((cp>>6)&63),128|(cp&63)); }
    else bytes.push(224|(c>>12),128|((c>>6)&63),128|(c&63));
  }
  var bitLen=bytes.length*8;
  bytes.push(128);
  while ((bytes.length%64)!==56) bytes.push(0);
  for (var b=7;b>=0;b--) bytes.push(Math.floor(bitLen/Math.pow(2,b*8))&255);
  var w=new Array(64);
  for (var off=0;off<bytes.length;off+=64){
    for (var t=0;t<16;t++) w[t]=(bytes[off+t*4]<<24)|(bytes[off+t*4+1]<<16)|(bytes[off+t*4+2]<<8)|bytes[off+t*4+3];
    for (t=16;t<64;t++){
      var s0=rr(w[t-15],7)^rr(w[t-15],18)^(w[t-15]>>>3);
      var s1=rr(w[t-2],17)^rr(w[t-2],19)^(w[t-2]>>>10);
      w[t]=(w[t-16]+s0+w[t-7]+s1)|0;
    }
    var a=H[0],b2=H[1],c2=H[2],d=H[3],e=H[4],f=H[5],g=H[6],h=H[7];
    for (t=0;t<64;t++){
      var S1=rr(e,6)^rr(e,11)^rr(e,25), ch=(e&f)^(~e&g);
      var t1=(h+S1+ch+K[t]+w[t])|0;
      var S0=rr(a,2)^rr(a,13)^rr(a,22), mj=(a&b2)^(a&c2)^(b2&c2);
      var t2=(S0+mj)|0;
      h=g;g=f;f=e;e=(d+t1)|0;d=c2;c2=b2;b2=a;a=(t1+t2)|0;
    }
    H[0]=(H[0]+a)|0;H[1]=(H[1]+b2)|0;H[2]=(H[2]+c2)|0;H[3]=(H[3]+d)|0;
    H[4]=(H[4]+e)|0;H[5]=(H[5]+f)|0;H[6]=(H[6]+g)|0;H[7]=(H[7]+h)|0;
  }
  var out="";
  for (var k=0;k<8;k++){ var x=H[k]>>>0; out+=("00000000"+x.toString(16)).slice(-8); }
  return out;
}

/* ---------- CRC32 + stored (uncompressed) ZIP writer -> base64 ----------
   Real ZIP files: readable by every unzip tool. No compression (method 0). */
var CRC_T=(function(){
  var t=new Array(256),i,j,c;
  for(i=0;i<256;i++){ c=i; for(j=0;j<8;j++) c=(c&1)?(0xEDB88320^(c>>>1)):(c>>>1); t[i]=c>>>0; }
  return t;
})();
function crc32bytes(u8){
  var c=0xFFFFFFFF,i;
  for(i=0;i<u8.length;i++) c=CRC_T[(c^u8[i])&255]^(c>>>8);
  return (c^0xFFFFFFFF)>>>0;
}
function strToU8(s){
  var out=[],i,c;
  for(i=0;i<s.length;i++){ c=s.charCodeAt(i);
    if(c<128) out.push(c);
    else if(c<2048) out.push(192|(c>>6),128|(c&63));
    else out.push(224|(c>>12),128|((c>>6)&63),128|(c&63)); }
  return out;
}
function u16(n){ return [n&255,(n>>8)&255]; }
function u32(n){ return [n&255,(n>>8)&255,(n>>16)&255,(n>>24)&255]; }
function zipStore(files){
  var chunks=[], central=[], offset=0, i;
  function push(arr){ for(var k=0;k<arr.length;k++) chunks.push(arr[k]&255); }
  for(i=0;i<files.length;i++){
    var name=files[i].name, d=files[i].data, u8;
    if (typeof d==="string") u8=strToU8(d);
    else { u8=[]; for(var q=0;q<d.length;q++) u8.push(d[q]&255); }
    var crc=crc32bytes(u8), nb=strToU8(name);
    push(u32(0x04034b50)); push(u16(20)); push(u16(0)); push(u16(0));
    push(u16(0)); push(u16(0)); push(u32(crc)); push(u32(u8.length)); push(u32(u8.length));
    push(u16(nb.length)); push(u16(0)); push(nb); push(u8);
    central.push({nb:nb,crc:crc,len:u8.length,off:offset});
    offset += 30 + nb.length + u8.length;
  }
  var cdStart=chunks.length, cd=[];
  function cpush(arr){ for(var k=0;k<arr.length;k++) cd.push(arr[k]&255); }
  for(i=0;i<central.length;i++){
    var e=central[i];
    cpush(u32(0x02014b50)); cpush(u16(20)); cpush(u16(20));
    cpush(u16(0)); cpush(u16(0)); cpush(u16(0)); cpush(u16(0));
    cpush(u32(e.crc)); cpush(u32(e.len)); cpush(u32(e.len));
    cpush(u16(e.nb.length)); cpush(u16(0)); cpush(u16(0)); cpush(u16(0)); cpush(u16(0));
    cpush(u32(0)); cpush(u32(e.off)); cpush(e.nb);
  }
  var cdLen=cd.length;
  push(cd);
  push(u32(0x06054b50)); push(u16(0)); push(u16(0));
  push(u16(files.length)); push(u16(files.length));
  push(u32(cdLen)); push(u32(cdStart)); push(u16(0));
  var bytes=chunks, bin="", k2;
  for(k2=0;k2<bytes.length;k2++) bin+=String.fromCharCode(bytes[k2]);
  if (typeof btoa!=="undefined") return btoa(bin);
  if (typeof Buffer!=="undefined") return Buffer.from(bytes).toString("base64");
  throw new Error("no base64 encoder");
}

/* ---------- the JS build: base + exactly the selected add-ons ----------
   libs: [{id,name,version,category,desc,functions,code}]
   opts: {stamp, base (LLAMA_BASES entry), buildName} */
function buildBundle(libs, opts){
  opts = opts || {};
  var stamp = opts.stamp || (new Date().toISOString().slice(0,10));
  var base = opts.base || LLAMA_BASES[0];
  var name = opts.buildName || "My Custom Llama";
  var parts = [];
  parts.push("/* ============================================================");
  parts.push("   " + name + " — a custom Signature Llama build");
  parts.push("   Base: " + base.name + " (" + base.engine + ")");
  parts.push("   Built: " + stamp + " with the on-page Llama Compiler");
  parts.push("   Add-ons inside: " + libs.length);
  libs.forEach(function(l, i){
    parts.push("   " + (i+1) + ". " + l.id + " - " + l.name + " (v" + (l.version||"?") + ")");
  });
  parts.push("   How to use: include this file AFTER the core engine for your base");
  parts.push("   (" + base.engine + ").");
  parts.push("   Every add-on registers itself on window.SigLlama.tools['<id>'].");
  parts.push("   Independent build by Justin Addam Higgins. Not affiliated with Meta.");
  parts.push("   ============================================================ */");
  parts.push("(function(){");
  parts.push("var T = window.SigLlama = window.SigLlama || {};");
  parts.push("T.customBuild = { name: " + JSON.stringify(name) +
    ", base: " + JSON.stringify(base.id) +
    ", built: " + JSON.stringify(stamp) +
    ", addons: " + JSON.stringify(libs.map(function(l){return l.id;})) + " };");
  libs.forEach(function(l){
    parts.push("");
    parts.push("/* ----- add-on " + l.id + " | " + l.name + " v" + (l.version||"?") +
      " | " + (l.category||"") + " ----- */");
    parts.push(String(l.code || ""));
  });
  parts.push("})();");
  var js = parts.join("\n");

  var manifest = {
    build_name: name,
    base_llama: { id: base.id, name: base.name, engine: base.engine },
    built: stamp,
    generator: "Signature Llama Compiler (signature-llama/compiler.html)",
    count: libs.length,
    selections: libs.map(function(l){
      return { id: l.id, name: l.name, version: l.version || "1.0",
               category: l.category || "", functions: l.functions || [] };
    }),
    note: "Include the JS build after the core engine for the chosen base. Each add-on registers on window.SigLlama.tools['<id>']."
  };
  return { js: js, manifest: manifest, manifestJson: JSON.stringify(manifest, null, 1) };
}

/* ---------- build summary: descriptions, stats, what it does, implications ---------- */
function buildSummary(base, libs, name){
  var cats = {};
  libs.forEach(function(l){ cats[l.category||"General"] = (cats[l.category||"General"]||0)+1; });
  var catList = Object.keys(cats).sort().map(function(c){ return c+" ("+cats[c]+")"; });
  var fns = [];
  libs.forEach(function(l){ (l.functions||[]).forEach(function(f){ fns.push(l.id+": "+f); }); });
  var stats = [
    "Base Llama: " + base.name,
    "Add-ons: " + libs.length,
    "Tool functions: " + fns.length,
    "Categories covered: " + (catList.length ? catList.join(", ") : "none")
  ];
  var implications = [];
  if (base.id === "industry")
    implications.push("Cloud base: needs a free API key (pasted on the main page); answers come from the cloud, not your device.");
  else
    implications.push("On-device base: private — nothing leaves your device; no keys, no fees.");
  if (libs.length)
    implications.push("The add-ons run as ordinary page JavaScript with the permissions listed on each card — only the ones you picked are included.");
  else
    implications.push("No add-ons picked: this is the pure base Llama, nothing extra.");
  implications.push("The model can invent facts — verify anything important before acting on it.");
  var doesList = libs.map(function(l){ return l.name + ": " + (l.desc||""); });
  return {
    title: name,
    description: name + " is a custom Signature Llama built on " + base.name +
      " with " + libs.length + " hand-picked add-on" + (libs.length===1?"":"s") + ".",
    stats: stats,
    implications: implications,
    whatItDoes: doesList,
    functions: fns
  };
}

/* ---------- add-on interview: honest helper answers from the real record ---------- */
function interviewAnswer(lib, question){
  var q = String(question||"").toLowerCase().trim();
  if (!q) return "Ask me anything about this add-on — what it does, its functions, an example, or its permissions.";
  function has(){ for (var i=0;i<arguments.length;i++) if (q.indexOf(arguments[i])>=0) return true; return false; }
  if (has("permission","access","safe","trust","network","camera","microphone"))
    return lib.name + " permissions: " +
      "network=" + !!(lib.capabilities&&lib.capabilities.network) +
      ", camera=" + !!(lib.capabilities&&lib.capabilities.camera) +
      ", microphone=" + !!(lib.capabilities&&lib.capabilities.microphone) +
      ", storage=" + !!(lib.capabilities&&lib.capabilities.storage) + ". " +
      (lib.trust_note || "It runs as ordinary page JavaScript.");
  if (has("example")) return "Example: " + (lib.example || "no example recorded — try its functions below.");
  if (has("function","do","method","api","call"))
    return lib.name + " gives you: " + (lib.functions||[]).join("; ") + ".";
  if (has("version")) return lib.name + " is at version " + (lib.version||"1.0") + ".";
  if (has("categor")) return lib.name + " lives in the " + (lib.category||"General") + " group.";
  if (has("what","who","about","describe"))
    return lib.name + ": " + (lib.desc||"no description recorded.");
  return lib.name + " — " + (lib.desc||"") +
    " Ask me about its functions, an example, or its permissions.";
}

/* ---------- Python package sources (real, runnable) ---------- */
function pyTokenizer(){
  return [
  '"""Word-level tokenizer for the Signature Llama Python companion package.',
  'Loads the REAL vocab2.json (2,879 word tokens) shipped in this package.',
  'Same vocabulary the on-device engine was trained with."""',
  'import json, os, re',
  '',
  'class SigTokenizer:',
  '    def __init__(self, vocab_path=None):',
  '        if vocab_path is None:',
  '            vocab_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocab2.json")',
  '        with open(vocab_path, encoding="utf-8") as f:',
  '            v = json.load(f)',
  '        self.itos = v["itos"]',
  '        self.stoi = v["stoi"]',
  '        self.unk_id = v.get("unk_id", 0)',
  '        self.vocab_size = len(self.itos)',
  '',
  '    def encode(self, text):',
  '        """Text -> list of token ids (word-level)."""',
  '        toks = re.findall(r"[A-Za-z\']+|[0-9]+|[^\\sA-Za-z0-9\']", str(text).lower())',
  '        return [self.stoi.get(t, self.unk_id) for t in toks]',
  '',
  '    def decode(self, ids):',
  '        """Token ids -> text."""',
  '        return " ".join(self.itos[i] if 0 <= i < len(self.itos) else "<unk>" for i in ids)',
  ''
  ].join("\n");
}

function pyEngine(){
  return [
  '"""Companion chat engine for a compiled Signature Llama (Python).',
  '',
  'HONEST LABEL: this is the Python companion runtime. It answers from the',
  'build manifest plus the selected tools\\u2019 real descriptions, using the real',
  'word-level tokenizer above. The full 4,056,768-parameter neural model runs',
  'in the JavaScript build (the custom .js file + sigllama.js), not here.',
  '"""',
  'import json, os, re',
  '',
  'class CompanionEngine:',
  '    def __init__(self, package_dir=None):',
  '        if package_dir is None:',
  '            package_dir = os.path.dirname(os.path.abspath(__file__))',
  '        with open(os.path.join(package_dir, "manifest.json"), encoding="utf-8") as f:',
  '            self.manifest = json.load(f)',
  '        with open(os.path.join(package_dir, "tools_manifest.json"), encoding="utf-8") as f:',
  '            self.tools = json.load(f)["tools"]',
  '        base = self.manifest.get("base_llama", {})',
  '        self.build_name = self.manifest.get("build_name", "My Custom Llama")',
  '        self.base_name = base.get("name", "Basic Llama")',
  '',
  '    def _find_tools(self, text):',
  '        words = [w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 2]',
  '        scored = []',
  '        for t in self.tools:',
  '            hay = (t.get("name","") + " " + t.get("category","") + " " + t.get("desc","")).lower()',
  '            s = sum(3 if w in t.get("name","").lower() else (1 if w in hay else 0) for w in words)',
  '            if s: scored.append((s, t))',
  '        scored.sort(key=lambda x: -x[0])',
  '        return [t for _, t in scored[:3]]',
  '',
  '    def respond(self, text):',
  '        t = text.strip()',
  '        tl = t.lower()',
  '        if not t:',
  '            return "Type something and I\\u2019ll answer from the build\\u2019s knowledge."',
  '        if any(k in tl for k in ("who are you", "your name", "what are you")):',
  '            return ("I\\u2019m " + self.build_name + ", a custom Signature Llama built on " +',
  '                    self.base_name + " with " + str(len(self.tools)) + " add-ons. " +',
  '                    "Python companion runtime \\u2014 the neural weights run in the JS build.")',
  '        if any(k in tl for k in ("what tools", "list tools", "addons", "add-ons", "inside")):',
  '            names = ", ".join(x.get("name","?") for x in self.tools) or "no add-ons"',
  '            return "Inside this build (" + str(len(self.tools)) + " add-ons): " + names + "."',
  '        if "base" in tl or "llama" in tl and "which" in tl:',
  '            return "This build runs on " + self.base_name + "."',
  '        found = self._find_tools(t)',
  '        if found:',
  '            bits = []',
  '            for x in found:',
  '                fns = "; ".join(x.get("functions", []))',
  '                bits.append(x.get("name","?") + ": " + x.get("desc","") +',
  '                            (" Functions: " + fns + "." if fns else ""))',
  '            return " ".join(bits)',
  '        return ("I\\u2019m the companion runtime for " + self.build_name + ". " +',
  '                "Ask me which tools are inside, what a tool does, or which base Llama this uses. " +',
  '                "For open chat, use the JS build in a browser.")',
  ''
  ].join("\n");
}

function pyChat(){
  return [
  '#!/usr/bin/env python3',
  '"""Command-line chat for your compiled Signature Llama.',
  '',
  'Runs the Python companion runtime (real tokenizer + knowledge engine).',
  'Usage:  python3 chat.py',
  'Commands: /tools  list the add-ons inside   /help  this help   /quit  exit',
  '"""',
  'import sys',
  'from tokenizer import SigTokenizer',
  'from engine import CompanionEngine',
  '',
  'def main():',
  '    tok = SigTokenizer()',
  '    eng = CompanionEngine()',
  '    print("=" * 60)',
  '    print(eng.build_name)',
  '    print("Python companion chat  |  vocab: %d tokens" % tok.vocab_size)',
  '    print("Type /quit to exit, /tools to list add-ons.")',
  '    print("=" * 60)',
  '    while True:',
  '        try:',
  '            text = input("\\n> ")',
  '        except (EOFError, KeyboardInterrupt):',
  '            print("\\nBye.")',
  '            break',
  '        cmd = text.strip().lower()',
  '        if cmd in ("/quit", "/exit", "quit"):',
  '            print("Bye.")',
  '            break',
  '        if cmd == "/tools":',
  '            for t in eng.tools:',
  '                print(" - %s (%s)" % (t.get("name","?"), t.get("category","")))',
  '            continue',
  '        if cmd == "/help":',
  '            print("Ask about the build or its tools. /tools lists add-ons. /quit exits.")',
  '            continue',
  '        ids = tok.encode(text)',
  '        print("[tokens: %d]" % len(ids))',
  '        print(eng.respond(text))',
  '',
  'if __name__ == "__main__":',
  '    main()',
  ''
  ].join("\n");
}

function pyReadme(buildName, baseName, nTools){
  return [
  buildName + " — Python companion package",
  "=".repeat(Math.min(buildName.length + 28, 70)),
  "",
  "A REAL, runnable Python package for your compiled Signature Llama.",
  "Base: " + baseName + "  |  Add-ons inside: " + nTools,
  "",
  "WHAT IS REAL HERE",
  "- tokenizer.py ..... loads the REAL vocab2.json (2,879 word tokens) shipped",
  "                       in this package — encode()/decode() genuinely work.",
  "- engine.py ........ the Python companion runtime: answers from the build",
  "                       manifest + your add-ons' real descriptions.",
  "- chat.py .......... a command-line chat that ACTUALLY RUNS.",
  "- tools_manifest.json  your selected add-ons' real metadata.",
  "- tools_js/ .......... your selected add-ons' REAL JavaScript source.",
  "- manifest.json ...... the full build manifest + phone-book records.",
  "",
  "HONEST NOTE: the full 4,056,768-parameter neural model runs in the",
  "JavaScript build (the .js file from the Compiler page + sigllama.js).",
  "This Python package is its companion: real tokenizer, real runnable chat,",
  "real tool sources — no fake downloads, ever.",
  "",
  "RUN IT",
  "  python3 chat.py",
  "",
  "Independent build by Justin Addam Higgins. Not affiliated with Meta.",
  ""
  ].join("\n");
}

/* Build the full Python package file list.
   args: {buildName, base, libs, stamp, manifest, phonebook:[sig,best], vocabJson (string)} */
function buildPythonPackage(args){
  var files = [];
  var safe = String(args.buildName||"llama").toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"") || "llama";
  files.push({ name: safe + "/README.txt", data: pyReadme(args.buildName, args.base.name, args.libs.length) });
  files.push({ name: safe + "/tokenizer.py", data: pyTokenizer() });
  files.push({ name: safe + "/engine.py", data: pyEngine() });
  files.push({ name: safe + "/chat.py", data: pyChat() });
  files.push({ name: safe + "/vocab2.json", data: args.vocabJson });
  files.push({ name: safe + "/manifest.json", data: JSON.stringify(args.manifest, null, 1) });
  files.push({ name: safe + "/tools_manifest.json", data: JSON.stringify({ build: args.buildName,
    tools: args.libs.map(function(l){ return { id:l.id, name:l.name, version:l.version||"1.0",
      category:l.category||"", desc:l.desc||"", functions:l.functions||[], example:l.example||"",
      capabilities:l.capabilities||{} }; }) }, null, 1) });
  args.libs.forEach(function(l){
    files.push({ name: safe + "/tools_js/" + l.id + ".js", data: String(l.code||"// no code recorded") });
  });
  return { files: files, zipBase64: zipStore(files), dirName: safe };
}

/* ---------- phone-book entries: the Signature version + the improved best ----------
   Matches the ai-catalog.json record schema exactly.
   args: {buildName, base, libs, optimalAdded:[{id,name}], stamp, seq, manifestJson} */
function buildPhoneBookEntries(args){
  var stamp = args.stamp, seq = args.seq;
  function pad(n){ n=String(n); while(n.length<4) n="0"+n; return n; }
  function num(n){ n=String(n); while(n.length<7) n="0"+n; return n; }
  var ids = args.libs.map(function(l){ return l.id; });
  var lineage = "Compiled from " + args.base.name + " + " + args.libs.length +
    " add-on" + (args.libs.length===1?"":"s") + (ids.length ? " ("+ids.join(", ")+")" : "") +
    " on " + stamp + " via the Signature Llama Compiler.";
  function runtime(dl){
    return {
      what_you_download: "Real generated files: Python companion package (.zip, runs: python3 chat.py), custom JS build, manifest JSON \u2014 logic and tool code, not trained-model weights",
      what_the_demo_is: "the compiled build's own files running (JS in browser, Python chat on the command line)",
      what_the_chat_is: "Python companion runtime on-device (tokenizer + knowledge engine); JS build answers through the base Llama engine \u2014 every reply says which answered",
      works_offline: "YES \u2014 after download",
      internet_required: "NO for the Python chat and JS build (cloud base needs its key + network)",
      browser_only: "NO \u2014 Python package runs anywhere with Python 3; JS build runs in a browser",
      local_download: "YES"
    };
  }
  function artifact(zipName, stampId){
    return {
      download: zipName,
      deep_link: "#file-" + stampId.toLowerCase(),
      live_url: "https://justinahiggins614-cmyk.github.io/signature-llama/compiler.html"
    };
  }
  var zipSafe = String(args.buildName).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"") || "llama";
  var sig = {
    ID: "JAH-AI-CMP-" + pad(seq),
    NAME: args.buildName,
    TYPE: "sl",
    CATEGORY: "Compiled Llama",
    DESCRIPTION: args.buildName + " \u2014 a user-compiled Signature Llama. " + lineage,
    CAPABILITIES: [
      "Runs the compiled build: " + args.base.name + " plus " + args.libs.length + " add-ons",
      "Python companion chat (real tokenizer, knowledge engine) via python3 chat.py",
      "JS build registers every add-on on window.SigLlama.tools"
    ].concat(ids.slice(0,6).map(function(id){ return "Add-on aboard: " + id; })),
    LIMITATIONS: "Chat answers come from the companion runtime or the base engine \u2014 the model can invent facts; verify important ones.",
    STATUS: "PUBLISHED",
    VERSION: "1.0",
    ROLE: "COMPILED LLAMA",
    RUNTIME: runtime(),
    DEMO: { kind: "build-download", runs_in: "browser+python",
      url: "https://justinahiggins614-cmyk.github.io/signature-llama/compiler.html" },
    VOICE: { read_aloud: true, engine: "browser speech synthesis (tiered TTS)" },
    SIGNATURE_NUMBER: "1-700-" + num(seq),
    SOURCE: "Compiled on the Signature Llama Compiler page by the user \u2014 Signature-made by Justin Addam Higgins",
    RELATIONSHIPS: { compiled_from: args.base.id, addons: ids },
    HASH: "sha256:" + sha256hex(args.manifestJson || ""),
    ARTIFACTS: artifact(zipSafe + "-python.zip", "JAH-AI-CMP-" + pad(seq))
  };
  var addedIds = (args.optimalAdded||[]).map(function(l){ return l.id; });
  var best = {
    ID: "JAH-AI-CMP-" + pad(seq+1),
    NAME: args.buildName + " Best",
    TYPE: "sl",
    CATEGORY: "Compiled Llama",
    DESCRIPTION: args.buildName + " Best \u2014 the improved best-practice version of " + args.buildName +
      ". Takes the user's exact build (" + lineage + ") and adds the recommended add-ons the builder didn't pick" +
      (addedIds.length ? " (" + addedIds.join(", ") + ")" : " (none needed \u2014 the build already had them all)") + ".",
    CAPABILITIES: sig.CAPABILITIES.concat(addedIds.map(function(id){ return "Best-practice add-on: " + id; })),
    LIMITATIONS: sig.LIMITATIONS,
    STATUS: "PUBLISHED",
    VERSION: "1.0",
    ROLE: "COMPILED LLAMA \u2014 BEST",
    RUNTIME: runtime(),
    DEMO: { kind: "build-download", runs_in: "browser+python",
      url: "https://justinahiggins614-cmyk.github.io/signature-llama/compiler.html" },
    VOICE: { read_aloud: true, engine: "browser speech synthesis (tiered TTS)" },
    SIGNATURE_NUMBER: "1-700-" + num(seq+1),
    SOURCE: "Auto-improved by the Signature Llama Compiler's best-practice reviewer \u2014 Signature-made by Justin Addam Higgins",
    RELATIONSHIPS: { compiled_from: args.base.id, addons: ids, improves: "JAH-AI-CMP-" + pad(seq),
      best_practice_addons: addedIds },
    HASH: "sha256:" + sha256hex(args.manifestJson || ""),
    ARTIFACTS: artifact(zipSafe + "-best-python.zip", "JAH-AI-CMP-" + pad(seq+1))
  };
  return [sig, best];
}

/* Export for node tests */
if (typeof module !== "undefined" && module.exports){
  module.exports = {
    escHtml: escHtml, LLAMA_BASES: LLAMA_BASES, baseById: baseById,
    checkLlamaName: checkLlamaName, sha256hex: sha256hex,
    crc32bytes: crc32bytes, zipStore: zipStore,
    buildBundle: buildBundle, buildSummary: buildSummary,
    interviewAnswer: interviewAnswer,
    buildPythonPackage: buildPythonPackage, buildPhoneBookEntries: buildPhoneBookEntries
  };
}

/* ============================================================
   Page UI — browser only
   ============================================================ */
if (typeof document !== "undefined"){
(function(){
  var LIBS = [], TRAY = [];
  var grid = document.getElementById("addonGrid"),
      trayEl = document.getElementById("tray"),
      trayCount = document.getElementById("trayCount"),
      trayBase = document.getElementById("trayBase"),
      q = document.getElementById("addonSearch"),
      result = document.getElementById("buildResult"),
      basePick = document.getElementById("basePick"),
      baseDesc = document.getElementById("baseDesc");

  function byId(id){
    for (var i=0;i<LIBS.length;i++) if (LIBS[i].id===id) return LIBS[i];
    return null;
  }
  function inTray(id){ return TRAY.indexOf(id) >= 0; }
  function selBase(){ return baseById(basePick ? basePick.value : "basic"); }

  /* ----- read-aloud: one global controller, never stacked ----- */
  function speak(text, label){
    try{
      var R = window.__JAHREAD;
      if (R){ if(!R.playGuard(label||"speak")) return; }
      else if (window.speechSynthesis) window.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(String(text).slice(0, 1200));
      window.speechSynthesis.speak(u);
    }catch(e){}
  }

  function download(filename, content, mime){
    var blob = (content instanceof Blob) ? content : new Blob([content], {type: mime || "text/plain;charset=utf-8"});
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = filename;
    document.body.appendChild(a); a.click();
    setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); }, 1200);
  }
  function b64ToBlob(b64, mime){
    var bin = atob(b64), len = bin.length, u8 = new Uint8Array(len);
    for (var i=0;i<len;i++) u8[i] = bin.charCodeAt(i);
    return new Blob([u8], {type: mime});
  }
  function copyText(text, btn){
    function done(){ var o=btn.textContent; btn.textContent="\u2713 Copied!"; setTimeout(function(){btn.textContent=o;},1500); }
    function fallback(){
      var ta=document.createElement("textarea"); ta.value=text;
      ta.style.position="fixed"; ta.style.opacity="0";
      document.body.appendChild(ta); ta.select();
      try{ document.execCommand("copy"); }catch(e){}
      ta.remove(); done();
    }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback);
    else fallback();
  }

  function libText(l){
    return l.name+" (v"+(l.version||"1.0")+") ["+(l.category||"")+"]\n"+(l.desc||"")+
      "\nFunctions: "+(l.functions||[]).join("; ")+
      (l.example ? "\nExample: "+l.example : "");
  }

  /* ----- add-on cards ----- */
  function cardHTML(l){
    var added = inTray(l.id), id = escHtml(l.id);
    return '<div class="acard" data-id="'+id+'">' +
      '<div class="aname">'+escHtml(l.name)+
      (l.optimal ? ' <span class="best-tag">starter pick</span>' : '') + '</div>' +
      '<div class="ameta">'+escHtml(l.category||"")+' \u00B7 v'+escHtml(l.version||"1.0")+'</div>' +
      '<div class="adesc">'+escHtml(l.desc||"")+'</div>' +
      '<div class="abtnrow">' +
      '<button type="button" class="abtn" data-add="'+id+'"'+(added?' disabled':'')+'>'+(added?'\u2713 In the tray':'\u2795 Add to '+escHtml(selBase().name))+'</button>' +
      '<button type="button" class="abtn ghost" data-examine="'+id+'">\uD83D\uDD0D Examine</button>' +
      '<button type="button" class="abtn ghost" data-interview="'+id+'">\uD83D\uDCAC Interview</button>' +
      '</div><div class="abtnrow">' +
      '<button type="button" class="abtn ghost" data-copy="'+id+'">\uD83D\uDCCB Copy</button>' +
      '<button type="button" class="abtn ghost" data-dl="'+id+'">\u2913 Download</button>' +
      '<button type="button" class="abtn ghost" data-read="'+id+'">\uD83D\uDD0A Read</button>' +
      '</div>' +
      '<div class="xdetail" data-xdetail="'+id+'" hidden></div>' +
      '<div class="xinterview" data-xinterview="'+id+'" hidden>' +
        '<div class="ilog" data-ilog="'+id+'"></div>' +
        '<div class="irow"><input type="text" data-iq="'+id+'" placeholder="Ask about this add-on\u2026" aria-label="Ask about '+escHtml(l.name)+'">' +
        '<button type="button" class="abtn" data-isend="'+id+'">Ask</button></div>' +
        '<p class="dim" style="font-size:.75em;margin:.3em 0 0">Add-on helper \u2014 answers from the add-on\u2019s real record.</p>' +
      '</div></div>';
  }

  function renderGrid(){
    var term = (q.value||"").toLowerCase().trim(), html = "";
    LIBS.forEach(function(l){
      var hay = (l.name+" "+l.id+" "+(l.category||"")+" "+(l.desc||"")).toLowerCase();
      if (term && hay.indexOf(term) < 0) return;
      html += cardHTML(l);
    });
    grid.innerHTML = html || '<p class="dim">No add-ons match that search.</p>';
  }

  function renderTray(){
    var b = selBase();
    trayCount.textContent = TRAY.length;
    if (trayBase) trayBase.textContent = b.name;
    if (!TRAY.length){
      trayEl.innerHTML = '<p class="dim">Your tray is empty. Tap \u201C\u2795 Add\u201D on any add-on above.</p>';
      return;
    }
    trayEl.innerHTML = TRAY.map(function(id){
      var l = byId(id);
      return '<span class="tchip">'+escHtml(l ? l.name : id)+
        ' <button type="button" data-rm="'+escHtml(id)+'" aria-label="Remove">\u2715</button></span>';
    }).join("");
  }
  function refresh(){ renderGrid(); renderTray(); }

  function examineHTML(l){
    var caps = l.capabilities || {};
    return '<dl class="xdl">' +
      '<dt>What it does</dt><dd>'+escHtml(l.desc||"")+'</dd>' +
      '<dt>Functions</dt><dd><code>'+escHtml((l.functions||[]).join("</code>, <code>"))+'</code></dd>' +
      (l.example ? '<dt>Example</dt><dd>'+escHtml(l.example)+'</dd>' : '') +
      '<dt>Permissions</dt><dd>network: '+(!!caps.network)+', camera: '+(!!caps.camera)+
      ', microphone: '+(!!caps.microphone)+', storage: '+(!!caps.storage)+
      ', code runs on your page: '+(!!caps.code_execution)+'</dd>' +
      (l.trust_note ? '<dt>Trust note</dt><dd>'+escHtml(l.trust_note)+'</dd>' : '') +
      '<dt>Version</dt><dd>'+escHtml(l.version||"1.0")+'</dd>' +
      '</dl>';
  }

  grid.addEventListener("click", function(e){
    var t = e.target, l, id;
    function closest(attr){ var b=t.closest ? t.closest("["+attr+"]") : null; return b ? b.getAttribute(attr) : null; }
    if ((id = closest("data-add"))){
      if (!inTray(id)){ TRAY.push(id); refresh(); }
      return;
    }
    if ((id = closest("data-examine"))){
      l = byId(id); if(!l) return;
      var xd = grid.querySelector('[data-xdetail="'+id+'"]');
      if (xd.hidden){ xd.innerHTML = examineHTML(l); xd.hidden = false; }
      else xd.hidden = true;
      return;
    }
    if ((id = closest("data-interview"))){
      var xi = grid.querySelector('[data-xinterview="'+id+'"]');
      xi.hidden = !xi.hidden;
      return;
    }
    if ((id = closest("data-isend"))){
      l = byId(id); if(!l) return;
      var inp = grid.querySelector('[data-iq="'+id+'"]'), log = grid.querySelector('[data-ilog="'+id+'"]');
      var question = inp.value.trim(); if(!question) return;
      log.innerHTML += '<div class="imsg q"><b>You:</b> '+escHtml(question)+'</div>';
      log.innerHTML += '<div class="imsg a"><b>'+escHtml(l.name)+':</b> '+escHtml(interviewAnswer(l, question))+'</div>';
      inp.value = ""; log.scrollTop = log.scrollHeight;
      return;
    }
    if ((id = closest("data-copy"))){ l = byId(id); if(l) copyText(libText(l), t); return; }
    if ((id = closest("data-dl"))){ l = byId(id); if(l) download(id+".js", String(l.code||""), "text/javascript;charset=utf-8"); return; }
    if ((id = closest("data-read"))){ l = byId(id); if(l) speak(l.name+". "+(l.desc||""), "addon-"+id); return; }
  });
  grid.addEventListener("keydown", function(e){
    if (e.key !== "Enter") return;
    var inp = e.target.closest ? e.target.closest("[data-iq]") : null;
    if (inp){
      var id = inp.getAttribute("data-iq");
      var btn = grid.querySelector('[data-isend="'+id+'"]');
      if (btn) btn.click();
    }
  });

  trayEl.addEventListener("click", function(e){
    var b = e.target.closest ? e.target.closest("[data-rm]") : null;
    if (!b) return;
    var id = b.getAttribute("data-rm");
    TRAY = TRAY.filter(function(x){ return x !== id; });
    refresh();
  });
  q.addEventListener("input", renderGrid);
  basePick.addEventListener("change", refresh);

  document.getElementById("addOptimal").addEventListener("click", function(){
    LIBS.forEach(function(l){ if (l.optimal && !inTray(l.id)) TRAY.push(l.id); });
    refresh();
  });
  document.getElementById("clearTray").addEventListener("click", function(){
    TRAY = []; result.hidden = true; refresh();
  });

  /* ----- phone-book queue (this browser) ----- */
  function pbQueue(){ var PS = (typeof JAHProfile !== 'undefined') ? JAHProfile.store : localStorage; try{ return JSON.parse(PS.get("jah-llama-phonebook-queue")||"[]"); }catch(e){ return []; } }
  function pbQueueSave(a){ var PS = (typeof JAHProfile !== 'undefined') ? JAHProfile.store : localStorage; try{ PS.set("jah-llama-phonebook-queue", JSON.stringify(a)); }catch(e){} }
  function nextSeq(){ var PS = (typeof JAHProfile !== 'undefined') ? JAHProfile.store : localStorage; var s=3; try{ s=parseInt(PS.get("jah-llama-cmp-seq")||"3",10)||3; }catch(e){} return s; }
  function bumpSeq(s){ var PS = (typeof JAHProfile !== 'undefined') ? JAHProfile.store : localStorage; try{ PS.set("jah-llama-cmp-seq", String(s+2)); }catch(e){} }

  /* ----- compile flow ----- */
  var lastBuild = null;
  document.getElementById("compileBtn").addEventListener("click", function(){
    if (!TRAY.length){
      result.hidden = false;
      result.innerHTML = '<p class="dim"><b>Your tray is empty.</b> Add at least one add-on above, then compile.</p>';
      result.scrollIntoView();
      return;
    }
    var base = selBase(), libs = TRAY.map(byId).filter(Boolean);
    var stamp = new Date().toISOString().slice(0,10);
    var sum = buildSummary(base, libs, "Your custom Llama");
    var fnList = sum.functions.length ?
      '<ul class="inside">'+sum.functions.map(function(f){ return '<li><code>'+escHtml(f)+'</code></li>'; }).join("")+'</ul>' :
      '<p class="dim">No listed functions.</p>';
    result.hidden = false;
    result.innerHTML =
      '<h3>\uD83D\uDD0D Build summary \u2014 read before you name it</h3>' +
      '<p><b>'+escHtml(sum.description)+'</b></p>' +
      '<h4>What\u2019s inside</h4><ul>'+
        libs.map(function(l){ return '<li><b>'+escHtml(l.name)+'</b> <span class="dim">('+escHtml(l.id)+' v'+escHtml(l.version||"1.0")+')</span><br><span class="dim">'+escHtml(l.desc||"")+'</span></li>'; }).join("")+'</ul>' +
      '<h4>Stats</h4><ul>'+sum.stats.map(function(s){ return '<li>'+escHtml(s)+'</li>'; }).join("")+'</ul>' +
      '<h4>Implications</h4><ul>'+sum.implications.map(function(s){ return '<li>'+escHtml(s)+'</li>'; }).join("")+'</ul>' +
      '<details><summary style="cursor:pointer;color:var(--gold)">\uD83D\uDCBB Show the tool functions ('+sum.functions.length+')</summary>'+fnList+'</details>' +
      '<div class="namebox"><label for="llamaName"><b>\uD83C\uDFF7\uFE0F Name your Llama</b></label>' +
      '<input type="text" id="llamaName" maxlength="48" placeholder="e.g. My Study Helper" aria-label="Name your Llama">' +
      '<p class="dim" id="nameMsg" style="font-size:.85em"></p>' +
      '<button type="button" class="big gold" id="finishBtn" style="font-size:1.1em;padding:14px 26px">\u2714 Name it &amp; finish the build</button></div>' +
      '<div id="finalDl"></div>';
    result.scrollIntoView();
    document.getElementById("finishBtn").addEventListener("click", function(){
      var nameInput = document.getElementById("llamaName"),
          msg = document.getElementById("nameMsg"),
          chk = checkLlamaName(nameInput.value);
      if (!chk.ok){
        msg.innerHTML = '<b style="color:var(--red)">'+escHtml(chk.msg)+'</b>';
        nameInput.focus();
        return;
      }
      finishBuild(chk.name, base, libs, stamp);
    });
  });

  function finishBuild(name, base, libs, stamp){
    var box = document.getElementById("finalDl");
    box.innerHTML = '<p class="dim">Building your Python package\u2026</p>';
    var bundle = buildBundle(libs, { stamp: stamp, base: base, buildName: name });
    var optimalMissing = LIBS.filter(function(l){ return l.optimal && !inTray(l.id); });
    var seq = nextSeq();
    var entries = buildPhoneBookEntries({ buildName: name, base: base, libs: libs,
      optimalAdded: optimalMissing, stamp: stamp, seq: seq, manifestJson: bundle.manifestJson });
    function done(vocabText){
      var manifest = JSON.parse(bundle.manifestJson);
      manifest.phonebook_filed = entries.map(function(e){ return { id: e.ID, name: e.NAME }; });
      manifest.summary = buildSummary(base, libs, name);
      var pkg = buildPythonPackage({ buildName: name, base: base, libs: libs,
        stamp: stamp, manifest: manifest, vocabJson: vocabText });
      var zipName = pkg.dirName + "-python.zip";
      var jsName = pkg.dirName + ".js";
      // file behind the scenes: queue the phone-book entries in this browser
      var qq = pbQueue(); entries.forEach(function(e){ qq.push(e); }); pbQueueSave(qq); bumpSeq(seq);
      // build history
      saveHistory({ name: name, base: base.name, stamp: stamp, manifest: manifest });
      var sum = manifest.summary;
      box.innerHTML =
        '<h3>\uD83C\uDF89 '+escHtml(name)+' is built!</h3>' +
        '<p>'+escHtml(sum.description)+'</p>' +
        '<div class="brow">' +
        '<button type="button" class="big gold" id="dlZip">\u2913 Download Python package (.zip)</button>' +
        '<button type="button" class="big" id="dlJs2">\u2913 Download JS build (.js)</button>' +
        '<button type="button" class="big" id="dlMani">\u2913 Download manifest (.json)</button>' +
        '</div><div class="brow">' +
        '<button type="button" class="big" id="cpSum">\uD83D\uDCCB Copy the summary</button>' +
        '<button type="button" class="big" id="readSum">\uD83D\uDD0A Read summary aloud</button>' +
        '</div>' +
        '<h4>\uD83D\uDCDE Filed into the AI Phone Book (queued)</h4>' +
        '<p class="dim" style="font-size:.85em">Every compile is recorded behind the scenes: the Signature version (exactly what you built) plus an improved best version. They\u2019re queued in this browser and ride inside your manifest download \u2014 they join the public Phone Book with the next catalog update.</p>' +
        entries.map(function(e){
          return '<div class="ans"><b>'+escHtml(e.ID)+'</b> \u2014 '+escHtml(e.NAME)+
            '<br><span class="dim">'+escHtml(e.DESCRIPTION.slice(0,160))+'\u2026</span><br>' +
            '<button type="button" class="abtn ghost" data-cppb="'+escHtml(e.ID)+'">\uD83D\uDCCB Copy entry</button></div>';
        }).join("") +
        '<p class="dim" style="font-size:.85em">Use it: Python \u2014 unzip and run <code>python3 chat.py</code>. JS \u2014 put <code>'+escHtml(jsName)+'</code> on your page after the core engine for '+escHtml(base.name)+'.</p>';
      box.scrollIntoView();
      document.getElementById("dlZip").addEventListener("click", function(){
        download(zipName, b64ToBlob(pkg.zipBase64, "application/zip"), "application/zip");
      });
      document.getElementById("dlJs2").addEventListener("click", function(){
        download(jsName, bundle.js, "text/javascript;charset=utf-8");
      });
      document.getElementById("dlMani").addEventListener("click", function(){
        download(pkg.dirName+"-manifest.json", JSON.stringify(manifest,null,1), "application/json;charset=utf-8");
      });
      var sumText = sum.title+"\n"+sum.description+"\nStats: "+sum.stats.join("; ")+
        "\nImplications: "+sum.implications.join(" ")+
        "\nDoes: "+sum.whatItDoes.join(" | ");
      document.getElementById("cpSum").addEventListener("click", function(){ copyText(sumText, this); });
      document.getElementById("readSum").addEventListener("click", function(){ speak(sumText, "summary"); });
      box.addEventListener("click", function(e){
        var b = e.target.closest ? e.target.closest("[data-cppb]") : null;
        if (!b) return;
        var id = b.getAttribute("data-cppb");
        var en = entries.filter(function(x){ return x.ID===id; })[0];
        if (en) copyText(JSON.stringify(en, null, 1), b);
      });
      speak(name + " is built. " + sum.description, "built");
    }
    fetch("sigllama/vocab2.json").then(function(r){
      if(!r.ok) throw 0; return r.text();
    }).then(done).catch(function(){
      box.innerHTML = '<p style="color:var(--red)"><b>The vocabulary file didn\u2019t load.</b> Check your connection and press \u201CName it &amp; finish\u201D again \u2014 nothing was downloaded.</p>';
    });
  }

  /* ----- build history (this browser) ----- */
  function getHistory(){ var PS = (typeof JAHProfile !== 'undefined') ? JAHProfile.store : localStorage; try{ return JSON.parse(PS.get("jah-llama-compiles")||"[]"); }catch(e){ return []; } }
  function saveHistory(h){
    var PS = (typeof JAHProfile !== 'undefined') ? JAHProfile.store : localStorage;
    try{
      var a = getHistory(); a.unshift(h);
      PS.set("jah-llama-compiles", JSON.stringify(a.slice(0,20)));
    }catch(e){}
    renderHistory();
  }
  function renderHistory(){
    var el = document.getElementById("historyList"); if(!el) return;
    var a = getHistory();
    el.innerHTML = a.length ? a.map(function(h, i){
      return '<div class="ans"><b>'+escHtml(h.name)+'</b> <span class="dim">\u2014 '+escHtml(h.base)+' \u00B7 '+escHtml(h.stamp)+'</span><br>' +
        '<button type="button" class="abtn ghost" data-hist="'+i+'">\uD83D\uDCCB Copy manifest</button></div>';
    }).join("") : '<p class="dim">Nothing compiled yet on this device.</p>';
  }
  document.addEventListener("click", function(e){
    var b = e.target.closest ? e.target.closest("[data-hist]") : null;
    if (!b) return;
    var h = getHistory()[parseInt(b.getAttribute("data-hist"),10)];
    if (h) copyText(JSON.stringify(h.manifest, null, 1), b);
  });

  /* ----- boot ----- */
  function paintBase(){
    var b = selBase();
    baseDesc.innerHTML = '<b>'+escHtml(b.name)+'</b> <span class="dim">\u2014 '+escHtml(b.tag)+'</span><br>'+escHtml(b.desc)+
      '<br><span class="dim" style="font-size:.85em">Engine: '+escHtml(b.engine)+'</span>';
  }
  basePick.addEventListener("change", paintBase);
  fetch("data/tool-libraries.json").then(function(r){
    if(!r.ok) throw new Error("http "+r.status);
    return r.json();
  }).then(function(j){
    LIBS = j.libraries || [];
    document.getElementById("libCount").textContent = LIBS.length;
    paintBase(); refresh(); renderHistory();
  }).catch(function(){
    grid.innerHTML = '<p class="dim">Could not load the add-on list. Check your connection and reload.</p>';
  });
})();
}
