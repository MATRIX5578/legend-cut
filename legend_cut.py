# Legend Cut — مونتاج كامل بالذكاء الاصطناعي (ويندوز) — من عائلة Legend
import os, sys, re, json, time, queue, shutil, bisect, hashlib, tempfile, threading, subprocess, importlib, importlib.util, site, webbrowser
import urllib.request
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

VERSION = "1.0.0"; REPO = "MATRIX5578/legend-cut"
FROZEN = getattr(sys, "frozen", False)                       # True لما يشتغل كـ exe
RES = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
for _s in ("stdout", "stderr"):                               # exe بدون كونسول: نمنع كراش الطباعة
    if getattr(sys, _s) is None: setattr(sys, _s, open(os.devnull, "w"))
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

APP = "Legend Cut"; ACC = "#7C5CFF"; ACC2 = "#9A82FF"; BG = "#0F1115"; PANEL = "#171A21"; HOV = "#222632"
FG = "#E8E8EE"; MUT = "#8A8FA3"; CUT = "#2A2E3A"; ZOOM = "#FFB547"
HOME = os.path.join(os.path.expanduser("~"), ".legend_cut"); os.makedirs(HOME, exist_ok=True)
NOWIN = 0x08000000 if os.name == "nt" else 0
DEPS = [("imageio_ffmpeg", "imageio-ffmpeg"), ("tkinterdnd2", "tkinterdnd2")]   # خفيفة، قبل الفتح
HEAVY = [("faster_whisper", "faster-whisper")]                                       # ثقيلة، بالخلفية

SYS_AUTO = """انت مونتير محترف لفيديوهات يوتيوب وسوشال ميديا. عندك تفريغ مقطع بالتوقيت (ثواني من الفيديو الأصلي).
رجّع JSON فقط بدون أي كلام ثاني بهالشكل:
{"keep":[[start,end,zoom]],"titles":[{"text":"..","at":sec,"dur":sec,"pos":"top|center"}],"reply":"وش سويت باختصار بالعامية"}
- keep: المقاطع اللي تبقى بالترتيب. احذف الصمت الطويل والتكرار والتهتهة والأخطاء والأجزاء المملة، وخل الإيقاع سريع وممتع.
- zoom=1 لزوم سريع على لحظة قوية أو نكتة أو نقطة مهمة (بشكل معتدل، مو كل مقطع).
- titles: عناوين موشن جرافيك متحركة قليلة ومفيدة (عنوان افتتاحي قوي + فواصل للأقسام) بلغة المقطع، قصيرة جداً.
- لا تستخدم أي أدوات. JSON فقط."""

SYS_CHAT = """انت مساعد المونتاج داخل برنامج Legend Cut، تتكلم بالعامية الخليجية وبدون رسميات.
الخطة: keep = مقاطع [start,end,zoom] بتوقيت الفيديو الأصلي، titles = عناوين موشن {text,at,dur,pos}،
captions = true/false (كابشن متحرك كلمة كلمة)، cap_color = لون الكابشن والعناوين (#hex).
نفّذ طلب المستخدم ورجّع JSON فقط فيه الحقول اللي تغيرت كاملة + "reply" (رد قصير ودود).
لو سؤال بدون تعديل رجّع {"reply":"..."} بس. لا تستخدم أي أدوات."""

# ---------------- أدوات ----------------
def missing(deps): return [p for m, p in deps if importlib.util.find_spec(m) is None]

def pip_install(pkgs, cb=None):
    user = [] if sys.prefix != sys.base_prefix else ["--user"]
    p = subprocess.Popen([sys.executable, "-m", "pip", "install", "--prefer-binary", "--disable-pip-version-check", *user, *pkgs],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="ignore", creationflags=NOWIN)
    tail = []
    for line in p.stdout:
        line = line.strip()
        if line: tail = (tail + [line])[-12:]; cb and cb(line)
    p.wait()
    sp = site.getusersitepackages()
    if sp not in sys.path: sys.path.append(sp)
    importlib.invalidate_caches()
    if p.returncode: raise RuntimeError("فشل تثبيت " + " ".join(pkgs) + ":\n" + "\n".join(tail[-6:]))

def first_run():
    if FROZEN: return                                         # النسخة الرسمية كل شي جاهز داخلها
    miss = missing(DEPS)
    if not miss: return
    w = tk.Tk(); w.title(APP); w.configure(bg=BG); w.geometry("520x170")
    tk.Label(w, text="◆ أجهز Legend Cut لأول مرة...", fg=FG, bg=BG, font=("Segoe UI", 12)).pack(pady=(28, 6))
    lb = tk.Label(w, text="", fg=MUT, bg=BG, font=("Segoe UI", 9), wraplength=480); lb.pack()
    err = []
    def job():
        try: pip_install(miss, lambda l: w.after(0, lb.config, {"text": l[:90]}))
        except Exception as e: err.append(str(e))
        w.after(0, w.destroy)
    threading.Thread(target=job, daemon=True).start(); w.mainloop()
    if err: messagebox.showwarning(APP, err[0] + "\n\nالبرنامج بيفتح، بس بعض المزايا ممكن ما تشتغل.")

_FF = None
def FF():
    global _FF
    if not _FF:
        import imageio_ffmpeg; _FF = imageio_ffmpeg.get_ffmpeg_exe()
    return _FF

_ASS = None
def has_ass():
    global _ASS
    if _ASS is None:
        r = subprocess.run([FF(), "-hide_banner", "-filters"], capture_output=True, text=True, errors="ignore", creationflags=NOWIN)
        _ASS = bool(re.search(r"\sass\s", r.stdout))
    return _ASS

def claude_exe():
    p = shutil.which("claude")
    if p: return p
    for c in (os.path.expanduser(r"~\.local\bin\claude.exe"), os.path.join(os.environ.get("APPDATA", ""), "npm", "claude.cmd")):
        if os.path.exists(c): return c

def cl_env(): return {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}  # يخصم من اشتراكك مو API

def claude_logged():
    exe = claude_exe()
    if not exe: return False
    try: return subprocess.run([exe, "auth", "status"], capture_output=True, env=cl_env(), cwd=HOME, creationflags=NOWIN, timeout=40).returncode == 0
    except Exception: return False

def install_claude():
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "irm https://claude.ai/install.ps1 | iex"],
                   capture_output=True, creationflags=NOWIN, timeout=900)
    if not claude_exe(): raise RuntimeError("ما قدرت أثبّت كلود — تأكد من النت وجرب مرة ثانية")

def ask_claude(prompt):
    exe = claude_exe()
    if not exe: raise RuntimeError("سجّل دخول كلود من الزر فوق أول")
    r = subprocess.run([exe, "-p", "--model", "opus", "--tools", "", "--no-session-persistence"], input=prompt, capture_output=True,
                       text=True, encoding="utf-8", errors="ignore", env=cl_env(), cwd=HOME, creationflags=NOWIN, timeout=1200)
    out = (r.stdout or "").strip()
    if r.returncode or not out: raise RuntimeError((r.stderr or "")[-400:] or "كلود ما رد — تأكد إنك مسجل دخول")
    return out

def jparse(s):
    m = re.search(r"\{.*\}", s, re.S)
    if not m: raise RuntimeError("رد كلود ما كان مفهوم، جرب مرة ثانية")
    return json.loads(m.group(0))

def probe(src):
    r = subprocess.run([FF(), "-hide_banner", "-i", src], capture_output=True, text=True, encoding="utf-8", errors="ignore", creationflags=NOWIN).stderr
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r); m = re.search(r"Video:.*?, (\d{2,5})x(\d{2,5})", r)
    if not m: raise RuntimeError("هذا الملف ما فيه فيديو أقدر أقراه")
    w, h = int(m[1]), int(m[2]); rot = re.search(r"rotat\w* of (-?[\d.]+)|rotate\s*:\s*(-?\d+)", r)
    if rot and abs(float(rot[1] or rot[2])) % 180 == 90: w, h = h, w
    return {"dur": int(d[1]) * 3600 + int(d[2]) * 60 + float(d[3]) if d else 0, "w": w - w % 2, "h": h - h % 2, "audio": "Audio:" in r}

def load_audio(src):                                          # نقرا الصوت بـ ffmpeg المدمج (أقوى ويدعم كل الصيغ)
    import numpy as np
    raw = os.path.join(tempfile.mkdtemp(prefix="lcut_"), "a.f32")
    r = subprocess.run([FF(), "-nostdin", "-y", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", raw],
                       capture_output=True, text=True, errors="ignore", creationflags=NOWIN)
    if r.returncode: raise RuntimeError("ما قدرت أقرا صوت المقطع:\n" + r.stderr[-300:])
    a = np.fromfile(raw, np.float32); shutil.rmtree(os.path.dirname(raw), ignore_errors=True)
    return a

def transcribe(src, model, cb):
    from faster_whisper import WhisperModel
    audio = load_audio(src)
    def run(dev, ct):
        m = WhisperModel(model, device=dev, compute_type=ct)
        segs, info = m.transcribe(audio, word_timestamps=True, vad_filter=True); words = []
        for s in segs:
            words += [[round(w.start, 2), round(w.end, 2), w.word.strip()] for w in (s.words or [])]
            cb(min(99, int(s.end / max(info.duration, 1) * 100)))
        return words
    try: return run("cuda", "float16")          # كرت شاشة NVIDIA = أسرع
    except Exception: return run("cpu", "int8")

def lines_of(words):
    L, cur = [], []
    for w in words:
        if cur and (w[0] - cur[-1][1] > 0.6 or len(cur) >= 14): L.append(cur); cur = []
        cur.append(w)
    if cur: L.append(cur)
    return [(l[0][0], l[-1][1], " ".join(x[2] for x in l)) for l in L]

def tx(lines): return "\n".join(f"[{a:.2f}-{b:.2f}] {t}" for a, b, t in lines)

def clean(keep, dur, pad=0.12):
    k = []
    for x in keep or []:
        try: a, b, z = float(x[0]) - pad, float(x[1]) + pad, int(x[2]) if len(x) > 2 else 0
        except Exception: continue
        a, b = max(0, a), min(dur, b)
        if b - a > 0.05: k.append([a, b, z])
    k.sort(); out = []
    for a, b, z in k:
        if out and a <= out[-1][1] + 0.2:
            if z == out[-1][2] or b <= out[-1][1]: out[-1][1] = max(out[-1][1], b); continue
            a = out[-1][1]
        out.append([round(a, 3), round(b, 3), z])
    return [x for x in out if x[1] - x[0] > 0.05]

def auto_plan(words, dur, cb):
    plan = {"keep": [[0, dur, 0]], "titles": [], "captions": True, "cap_color": ACC, "reply": ""}
    if not words: plan["reply"] = "ما لقيت كلام بالمقطع، خليته كامل. قولي وش تبي أسوي فيه."; return plan
    chunks, cur = [], []
    for l in lines_of(words):                 # المقاطع الطويلة تنقسم أجزاء ~15 دقيقة
        if cur and l[1] - cur[0][0] > 900: chunks.append(cur); cur = []
        cur.append(l)
    chunks.append(cur); keep, titles, rep = [], [], []
    for i, c in enumerate(chunks):
        cb(i, len(chunks))
        p = jparse(ask_claude(SYS_AUTO + f"\n\nهذا الجزء {i+1} من {len(chunks)} (مدة الفيديو كامل {dur:.0f} ثانية).\n\nالتفريغ:\n" + tx(c)))
        keep += p.get("keep", []); titles += p.get("titles", []); rep.append(p.get("reply", ""))
    plan.update(keep=clean(keep, dur) or [[0, dur, 0]], titles=titles, reply=" ".join(rep).strip())
    return plan

# ---------------- الرندر + الموشن جرافيك ----------------
def ass_t(t): t = max(0, t); return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
def col(hx): hx = hx.lstrip("#"); return f"&H00{hx[4:6]}{hx[2:4]}{hx[0:2]}".upper()
def ocol(hx): hx = hx.lstrip("#"); return f"&H{hx[4:6]}{hx[2:4]}{hx[0:2]}&".upper()
def esc(t): return str(t).replace("{", "(").replace("}", ")").replace("\n", " ")

def build_ass(plan, words, W, H):
    keep = plan["keep"]; starts = [k[0] for k in keep]; offs, o = [], 0
    for a, b, _ in keep: offs.append(o); o += b - a
    def mp(t, nxt=False):
        i = bisect.bisect_right(starts, t) - 1
        if i >= 0 and t <= keep[i][1]: return offs[i] + t - keep[i][0]
        return offs[i + 1] if nxt and i + 1 < len(keep) else None
    fs = int(min(W, H) * 0.075); vert = H > W; c = plan.get("cap_color") or ACC
    ev = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial,{fs},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{max(2, fs//12)},2,2,40,40,{int(H*(0.22 if vert else 0.08))},1
Style: Title,Arial,{int(fs*1.2)},&H00FFFFFF,&H00FFFFFF,{col(c)},{col(c)},1,0,0,0,100,100,0,0,3,{max(6, fs//4)},0,8,60,60,{int(H*0.1)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
    if plan.get("captions", True):            # كابشن متحرك: يطلع بـ pop والكلمة الحالية تتلون
        ws = [(mp(a), mp(b), t) for a, b, t in words]; ws = [w for w in ws if w[0] is not None and w[1] is not None]
        for i in range(0, len(ws), 3):
            g = ws[i:i+3]
            for j, (a, b, _) in enumerate(g):
                end = max(a + 0.05, g[j+1][0] if j + 1 < len(g) else b + 0.15)
                txt = " ".join(f"{{\\c{ocol(c)}}}{esc(x[2])}{{\\c&HFFFFFF&}}" if k == j else esc(x[2]) for k, x in enumerate(g))
                pop = "{\\fscx78\\fscy78\\t(0,110,\\fscx100\\fscy100)}" if j == 0 else ""
                ev.append(f"Dialogue: 0,{ass_t(a)},{ass_t(end)},Cap,,0,0,0,,{pop}{txt}")
    for t in plan.get("titles", []):           # عناوين موشن: سكيل + بلور + فيد
        try: a = mp(float(t.get("at", 0)), True); d = float(t.get("dur", 2.5))
        except Exception: continue
        if a is None or not t.get("text"): continue
        an = 5 if t.get("pos") == "center" else 8
        ev.append(f"Dialogue: 1,{ass_t(a)},{ass_t(a+d)},Title,,0,0,0,,{{\\an{an}\\fad(220,260)\\fscx65\\fscy65\\blur4\\t(0,280,\\fscx100\\fscy100\\blur0)}}{esc(t['text'])}")
    return "\n".join(ev) + "\n"

def render(src, plan, meta, words, out, cb):
    keep = plan["keep"]; W, H = meta["w"], meta["h"]; tmp = tempfile.mkdtemp(prefix="lcut_")
    total = sum(b - a for a, b, _ in keep) or 1
    sel = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b, _ in keep)
    fc = f"[0:v]select='{sel}',setpts=N/FRAME_RATE/TB,scale={W}:{H},setsar=1[v0];"
    if meta["audio"]: fc += f"[0:a]aselect='{sel}',asetpts=N/SR/TB[aout];"
    zs, o, last = [], 0, "v0"
    for a, b, z in keep:
        if z: zs.append(f"between(t,{o:.3f},{o+b-a:.3f})")
        o += b - a
    if zs:                                     # زوم سريع (punch-in) على اللحظات القوية
        fc += f"[v0]split[za][zb];[zb]crop=iw*0.84:ih*0.84,scale={W}:{H},setsar=1[zc];[za][zc]overlay=0:0:enable='{'+'.join(zs)}'[v1];"; last = "v1"
    if has_ass() and (plan.get("captions", True) or plan.get("titles")):
        os.makedirs(os.path.join(tmp, "fonts"))
        for f in ("arial.ttf", "arialbd.ttf"):
            p = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", f)
            if os.path.exists(p): shutil.copy(p, os.path.join(tmp, "fonts"))
        open(os.path.join(tmp, "s.ass"), "w", encoding="utf-8").write(build_ass(plan, words, W, H))
        fc += f"[{last}]ass=s.ass:fontsdir=fonts[vout]"
    else: fc += f"[{last}]null[vout]"
    open(os.path.join(tmp, "fc.txt"), "w", encoding="utf-8").write(fc)
    cmd = [FF(), "-y", "-hide_banner", "-i", os.path.abspath(src), "-filter_complex_script", "fc.txt", "-map", "[vout]"]
    if meta["audio"]: cmd += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-progress", "pipe:1", "-nostats", os.path.abspath(out)]
    log = open(os.path.join(tmp, "log.txt"), "w", encoding="utf-8", errors="ignore")
    p = subprocess.Popen(cmd, cwd=tmp, stdout=subprocess.PIPE, stderr=log, text=True, creationflags=NOWIN)
    for line in p.stdout:
        if line.startswith("out_time_ms=") and line[12:].strip().isdigit(): cb(min(100, int(line[12:]) / 1e6 / total * 100))
    p.wait(); log.close()
    if p.returncode: raise RuntimeError("فشل التصدير:\n" + open(os.path.join(tmp, "log.txt"), encoding="utf-8", errors="ignore").read()[-500:])
    shutil.rmtree(tmp, ignore_errors=True)

def fmt(t): t = int(t); return f"{t//3600}:{t%3600//60:02d}:{t%60:02d}" if t >= 3600 else f"{t//60}:{t%60:02d}"

# ---------------- الواجهة ----------------
class App:
    def __init__(s):
        try: from tkinterdnd2 import TkinterDnD, DND_FILES; s.dnd = DND_FILES; s.root = TkinterDnD.Tk()
        except Exception: s.dnd = None; s.root = tk.Tk()
        r = s.root; r.title(APP); r.geometry("1200x740"); r.minsize(940, 620); r.configure(bg=BG)
        try: r.iconbitmap(os.path.join(RES, "assets", "icon.ico"))
        except Exception: pass
        try: r.attributes("-alpha", 0.0)
        except tk.TclError: pass
        st = ttk.Style(); st.theme_use("clam")
        st.configure("TCombobox", fieldbackground=PANEL, background=PANEL, foreground=FG, arrowcolor=FG, bordercolor=PANEL)
        s.q = queue.Queue(); s.busy = False; s.plan = None; s.words = []; s.hist = []; s.dirty = False
        s.wready = threading.Event(); s.werr = None; s.claude_ok = False; s.logging = False
        top = tk.Frame(r, bg=BG); top.pack(fill="x", padx=18, pady=(14, 0)); s.top = top
        tk.Label(top, text="◆ " + APP, font=("Segoe UI Semibold", 16), fg=FG, bg=BG).pack(side="right")
        tk.Label(top, text=f"v{VERSION}", font=("Segoe UI", 8), fg=MUT, bg=BG).pack(side="right", padx=6)
        s.lb = s.btn(top, "… أتأكد من كلود", s.login); s.lb.pack(side="left")
        s.wm = tk.StringVar(value="small")
        ttk.Combobox(top, textvariable=s.wm, values=["small", "medium", "large-v3"], width=9, state="readonly").pack(side="left", padx=(10, 4))
        tk.Label(top, text="دقة السماع", fg=MUT, bg=BG).pack(side="left")
        s.body = tk.Frame(r, bg=BG); s.body.pack(fill="both", expand=True, padx=18, pady=12)
        s.status = tk.Label(r, text="", fg=MUT, bg=BG, anchor="e"); s.status.pack(fill="x", padx=18, pady=(0, 8))
        s.splash(); r.after(50, s.poll); threading.Thread(target=s.boot, daemon=True).start()

    # --- مساعدات واجهة
    def btn(s, p, t, cmd, acc=False):
        base, hov = (ACC, ACC2) if acc else (PANEL, HOV)
        b = tk.Label(p, text=t, bg=base, fg="white" if acc else FG, padx=14, pady=7, font=("Segoe UI", 10), cursor="hand2")
        b.bind("<Button-1>", lambda e: cmd()); b.bind("<Enter>", lambda e: b.config(bg=hov)); b.bind("<Leave>", lambda e: b.config(bg=base))
        return b
    def ui(s, fn, *a): s.q.put((fn, a))
    def poll(s):
        try:
            while True: fn, a = s.q.get_nowait(); fn(*a)
        except queue.Empty: pass
        s.root.after(50, s.poll)
    def fade(s, a, b, done=None, steps=14):
        def st(i=0):
            try: s.root.attributes("-alpha", a + (b - a) * (1 - (1 - i / steps) ** 3))
            except tk.TclError: pass
            if i < steps: s.root.after(16, st, i + 1)
            elif done: done()
        st()
    def switch(s, page): s.fade(1, .4, lambda: (page(), s.fade(.4, 1, steps=10)), steps=7)
    def clear(s):
        for w in s.body.winfo_children(): w.destroy()
    def set_status(s, t): s.status.config(text=t)

    def splash(s):
        f = tk.Frame(s.body, bg=BG); f.place(relx=.5, rely=.45, anchor="c")
        tk.Label(f, text="◆", fg=ACC, bg=BG, font=("Segoe UI", 46)).pack()
        tk.Label(f, text=APP, fg=FG, bg=BG, font=("Segoe UI Semibold", 26)).pack()
        tk.Label(f, text="ارفع المقطع… والباقي علينا", fg=MUT, bg=BG, font=("Segoe UI", 11)).pack(pady=4)
        s.fade(0, 1, lambda: s.root.after(650, lambda: s.switch(s.page_drop)), steps=20)

    def boot(s):
        threading.Thread(target=s.check_update, daemon=True).start()
        s.claude_ok = claude_logged(); s.ui(s.set_login)
        try:
            if not FROZEN and missing(HEAVY):
                s.ui(s.set_status, "⬇ أنزّل محرك السماع بالخلفية (مرة وحدة بس، ياخذ كم دقيقة)... تقدر ترفع مقطعك عادي")
                pip_install([p for _, p in HEAVY], lambda l: s.ui(s.set_status, "⬇ أنزّل محرك السماع: " + l[:80]))
        except Exception as e: s.werr = str(e)
        finally: s.wready.set()
        try:
            FF(); msg = "جاهز ✓" if s.claude_ok else "👆 اضغط «سجّل دخول كلود» فوق — مرة وحدة بس"
            if s.werr: msg = "⚠ محرك السماع ما تثبت — شوف رسالة الخطأ لما ترفع مقطع"
            elif not has_ass(): msg += "  •  (الكابشن والعناوين مو مدعومة بنسخة ffmpeg هذي)"
            s.ui(s.set_status, msg)
        except Exception as e: s.ui(s.set_status, f"مشكلة بالتجهيز: {e}")

    # --- تسجيل دخول كلود من داخل التطبيق (المتصفح بس)
    def set_login(s):
        if s.claude_ok: s.lb.config(text="✓ كلود متصل", fg=FG, bg=PANEL); s.lb.bind("<Leave>", lambda e: s.lb.config(bg=PANEL))
        else: s.lb.config(text="سجّل دخول كلود", bg=ACC, fg="white"); s.lb.bind("<Leave>", lambda e: s.lb.config(bg=ACC))
    def login(s):
        if s.claude_ok or s.logging: return
        s.logging = True; s.lb.config(text="… جاري التسجيل"); threading.Thread(target=s.login_job, daemon=True).start()
    def login_job(s):
        st = lambda t: s.ui(s.set_status, t)
        try:
            if not claude_exe(): st("⬇ أجهّز كلود بالخلفية (مرة وحدة، دقيقة تقريباً)..."); install_claude()
            if not claude_logged():
                st("🌐 كمّل تسجيل الدخول بالمتصفح بحساب Pro أو Max، وبعدها ارجع هنا")
                p = subprocess.Popen([claude_exe(), "auth", "login"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, errors="ignore", env=cl_env(), cwd=HOME, creationflags=NOWIN)
                url = []
                def rd():
                    for line in p.stdout:
                        m = re.search(r"https://\S+", line)
                        if m and not url: url.append(m.group(0))
                threading.Thread(target=rd, daemon=True).start()
                for i in range(200):                            # ينتظر لين تخلص بالمتصفح (~10 دقايق)
                    time.sleep(3)
                    if i == 2 and url: webbrowser.open(url[0])  # لو المتصفح ما انفتح لحاله
                    if claude_logged(): break
                    if p.poll() is not None and i > 3: break
                try: p.kill()
                except Exception: pass
            s.claude_ok = claude_logged()
            st("✓ تم! كلود متصل — اسحب مقطعك" if s.claude_ok else "ما اكتمل التسجيل — اضغط الزر وجرب مرة ثانية")
        except Exception as e: st(f"⚠ {e}")
        finally: s.logging = False; s.ui(s.set_login)

    # --- تحديثات تلقائية من GitHub Releases
    def check_update(s):
        try:
            req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/latest", headers={"User-Agent": APP})
            d = json.load(urllib.request.urlopen(req, timeout=8)); tag = d["tag_name"].lstrip("vV")
            if tuple(map(int, tag.split("."))) > tuple(map(int, VERSION.split("."))):
                a = next((x["browser_download_url"] for x in d.get("assets", []) if x["name"].lower().endswith("setup.exe")), None)
                if a: s.ui(s.show_update, a, tag)
        except Exception: pass
    def show_update(s, url, tag):
        s.btn(s.top, f"⬆ تحديث v{tag}", lambda: threading.Thread(target=s.do_update, args=(url,), daemon=True).start(), True).pack(side="left", padx=8)
    def do_update(s, url):
        try:
            s.ui(s.set_status, "⬇ أنزّل التحديث..."); f = os.path.join(tempfile.gettempdir(), "LegendCut-Setup.exe")
            urllib.request.urlretrieve(url, f)
            subprocess.Popen([f, "/SILENT", "/CLOSEAPPLICATIONS"]); s.ui(s.root.destroy)
        except Exception as e: s.ui(s.set_status, f"⚠ ما قدرت أنزّل التحديث: {e}")

    # --- صفحة الرفع
    def page_drop(s):
        s.clear(); c = tk.Canvas(s.body, bg=BG, highlightthickness=0, cursor="hand2"); c.pack(fill="both", expand=True)
        s.dc = c; s.dglow = 0
        def draw(e=None):
            c.delete("all"); w, h = c.winfo_width(), c.winfo_height(); g = s.dglow
            c.create_rectangle(40, 40, w - 40, h - 40, fill=PANEL, outline=ACC2 if g else ACC, dash=(8, 6), width=3 if g else 2)
            c.create_text(w / 2, h / 2 - 30, text="⬆", fill=ACC, font=("Segoe UI", 44 if g else 40))
            c.create_text(w / 2, h / 2 + 40, text="اسحب المقطع هنا أو اضغط للاختيار", fill=FG, font=("Segoe UI", 16))
            c.create_text(w / 2, h / 2 + 76, text="أي صيغة • أي مقاس • أي طول — والذكاء الاصطناعي يمنتجه كامل بالموشن", fill=MUT, font=("Segoe UI", 10))
        def glow(v): s.dglow = v; draw()
        c.bind("<Configure>", draw); c.bind("<Enter>", lambda e: glow(1)); c.bind("<Leave>", lambda e: glow(0))
        c.bind("<Button-1>", lambda e: s.pick())
        if s.dnd:
            c.drop_target_register(s.dnd); c.dnd_bind("<<Drop>>", lambda e: s.start(s.root.tk.splitlist(e.data)[0]))

    def pick(s):
        f = filedialog.askopenfilename(title="اختر المقطع", filetypes=[("فيديو", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.wmv *.flv *.ts *.3gp"), ("الكل", "*.*")])
        if f: s.start(f)

    # --- صفحة الشغل
    def page_work(s):
        s.clear(); f = tk.Frame(s.body, bg=BG); f.place(relx=.5, rely=.45, anchor="c")
        s.stage = tk.Label(f, text="", fg=FG, bg=BG, font=("Segoe UI", 16)); s.stage.pack(pady=10)
        s.pc = tk.Canvas(f, width=480, height=8, bg=PANEL, highlightthickness=0); s.pc.pack()
        s.bar = s.pc.create_rectangle(0, 0, 0, 8, fill=ACC, width=0); s.pv = s.pt = 0
        s.sub = tk.Label(f, text="", fg=MUT, bg=BG); s.sub.pack(pady=8); s.anim_bar()
    def anim_bar(s):
        try:
            if not s.pc.winfo_exists(): return
            s.pv += (s.pt - s.pv) * 0.12; s.pc.coords(s.bar, 0, 0, 4.8 * s.pv, 8); s.root.after(16, s.anim_bar)
        except tk.TclError: pass
    def prog(s, stage, p, sub=""): s.ui(s._prog, stage, p, sub)
    def _prog(s, stage, p, sub):
        try: s.stage.config(text=stage); s.sub.config(text=sub); s.pt = p
        except (tk.TclError, AttributeError): pass

    def start(s, path):
        if s.busy: return
        if not s.claude_ok:
            messagebox.showinfo(APP, "سجّل دخول كلود أول (مرة وحدة بس) وبعدها ارفع المقطع 👌"); s.login(); return
        s.src = path; s.out = os.path.splitext(path)[0] + "_LegendCut.mp4"; s.hist = []
        s.busy = True; s.switch(s.page_work); threading.Thread(target=s.pipeline, daemon=True).start()

    def proj(s):
        st = os.stat(s.src); return os.path.join(HOME, hashlib.md5(f"{s.src}|{st.st_size}|{st.st_mtime}".encode()).hexdigest() + ".json")
    def save(s): json.dump({"words": s.words, "plan": s.plan}, open(s.proj(), "w", encoding="utf-8"), ensure_ascii=False)

    def pipeline(s):
        try:
            s.meta = probe(s.src); d = {}
            if os.path.exists(s.proj()): d = json.load(open(s.proj(), encoding="utf-8"))   # يكمل مشروعك من وين وقفت
            if "words" in d: s.words = d["words"]
            elif s.meta["audio"]:
                if not s.wready.is_set(): s.prog("⬇ أكمّل تنزيل محرك السماع...", 1, "مرة وحدة بس، بعدها يبدأ على طول"); s.wready.wait()
                if s.werr: raise RuntimeError(s.werr)
                s.prog("🎧 أسمع المقطع وأفرّغه...", 2, "أول مرة ياخذ وقت أكثر (ينزل نموذج السماع)")
                s.words = transcribe(s.src, s.wm.get(), lambda p: s.prog("🎧 أسمع المقطع وأفرّغه...", p * .4, f"{p}%"))
            else: s.words = []
            s.plan = d.get("plan"); s.save()
            if not s.plan:
                s.plan = auto_plan(s.words, s.meta["dur"], lambda i, n: s.prog("🧠 الذكاء الاصطناعي يمنتج...", 42 + 18 * i / n,
                                   f"الجزء {i+1} من {n} • يقص الممل ويصمم الموشن"))
                s.save()
            s.do_render(lambda p: s.prog("🎬 أركّب المقطع والموشن جرافيك...", 60 + p * .4, f"{int(p)}%"))
            s.ui(s.switch, s.page_edit)
        except Exception as e: s.ui(s.fail, str(e))
        finally: s.busy = False

    def do_render(s, cb):
        try: render(s.src, s.plan, s.meta, s.words, s.out, cb)
        except RuntimeError:
            global _ASS
            if not _ASS: raise
            _ASS = False; render(s.src, s.plan, s.meta, s.words, s.out, cb)   # لو الكابشن عيّا، يكمل بدونه
        s.dirty = False

    def fail(s, msg):
        messagebox.showerror(APP, msg)
        s.switch(s.page_edit if s.plan and os.path.exists(getattr(s, "out", "")) else s.page_drop)

    # --- صفحة التعديل + المساعد
    def page_edit(s):
        s.clear()
        right = tk.Frame(s.body, bg=PANEL, width=380); right.pack(side="right", fill="y", padx=(14, 0)); right.pack_propagate(False)
        left = tk.Frame(s.body, bg=BG); left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="✨ خلصت المونتاج", fg=FG, bg=BG, font=("Segoe UI Semibold", 18), anchor="e").pack(fill="x")
        s.info = tk.Label(left, fg=MUT, bg=BG, anchor="e", justify="right", wraplength=720); s.info.pack(fill="x", pady=(2, 12))
        row = tk.Frame(left, bg=BG); row.pack(fill="x")
        s.btn(row, "▶ معاينة", lambda: os.startfile(s.out), True).pack(side="right")
        s.rb = s.btn(row, "🔁 إعادة التصدير", s.rerender); s.rb.pack(side="right", padx=8)
        s.btn(row, "📁 المجلد", lambda: subprocess.Popen(["explorer", "/select,", os.path.abspath(s.out)])).pack(side="right")
        s.btn(row, "＋ مقطع جديد", lambda: s.switch(s.page_drop)).pack(side="left")
        s.capv = tk.BooleanVar(value=s.plan.get("captions", True))
        tk.Checkbutton(row, text="كابشن متحرك", variable=s.capv, command=s.cap_toggle, bg=BG, fg=FG, selectcolor=PANEL,
                       activebackground=BG, activeforeground=FG).pack(side="right", padx=12)
        tk.Label(left, text="التايملاين", fg=FG, bg=BG, font=("Segoe UI Semibold", 12), anchor="e").pack(fill="x", pady=(22, 4))
        s.tl = tk.Canvas(left, height=90, bg=PANEL, highlightthickness=0, cursor="hand2"); s.tl.pack(fill="x")
        tk.Label(left, text="كليك = تشيل/ترجع الجزء  •  كليك يمين = زوم  •  بنفسجي باقي، رمادي محذوف، برتقالي زوم", fg=MUT, bg=BG, anchor="e").pack(fill="x", pady=4)
        s.tip = tk.Label(left, text="", fg=ACC2, bg=BG, anchor="e"); s.tip.pack(fill="x")
        s.tl.bind("<Configure>", lambda e: s.draw_tl()); s.tl.bind("<Button-1>", lambda e: s.tl_click(e, 0))
        s.tl.bind("<Button-3>", lambda e: s.tl_click(e, 1)); s.tl.bind("<Motion>", s.tl_hover)
        # المساعد
        tk.Label(right, text="🤖 مساعد Legend", fg=FG, bg=PANEL, font=("Segoe UI Semibold", 13), anchor="e").pack(fill="x", padx=14, pady=(12, 4))
        s.chat = tk.Text(right, bg=PANEL, fg=FG, wrap="word", relief="flat", font=("Segoe UI", 10), padx=12, pady=6, state="disabled")
        s.chat.tag_config("me", justify="right", foreground=ACC2, spacing3=8); s.chat.tag_config("ai", justify="right", spacing3=8)
        ent_f = tk.Frame(right, bg=PANEL); ent_f.pack(side="bottom", fill="x", padx=10, pady=10)
        s.ent = tk.Entry(ent_f, bg=HOV, fg=FG, insertbackground=FG, relief="flat", font=("Segoe UI", 11), justify="right")
        s.btn(ent_f, "إرسال", s.send, True).pack(side="left"); s.ent.pack(side="right", fill="x", expand=True, ipady=7, padx=(6, 0))
        s.ent.bind("<Return>", lambda e: s.send()); s.chat.pack(fill="both", expand=True)
        s.say(s.plan.get("reply") or "خلصت! قولي وش تبي أعدل: أشيل جزء، أضيف عنوان، أغير اللون، زوم أكثر...", "ai")
        s.refresh()

    def segs(s):
        out, t, dur = [], 0, s.meta["dur"]
        for a, b, z in s.plan["keep"]:
            if a > t + .01: out.append([t, a, 0, 0])
            out.append([a, b, 1, z]); t = b
        if t < dur - .01: out.append([t, dur, 0, 0])
        return out
    def draw_tl(s):
        c = s.tl; c.delete("all"); w = c.winfo_width(); dur = s.meta["dur"] or 1
        for a, b, k, z in s.segs():
            c.create_rectangle(a / dur * w, 14, max(a / dur * w + 1, b / dur * w - 1), 76, width=0, fill=(ZOOM if z else ACC) if k else CUT)
        c.create_text(6, 6, text="0:00", fill=MUT, anchor="nw", font=("Segoe UI", 8))
        c.create_text(w - 6, 80, text=fmt(dur), fill=MUT, anchor="se", font=("Segoe UI", 8))
    def seg_at(s, x):
        t = x / max(1, s.tl.winfo_width()) * s.meta["dur"]
        for sg in s.segs():
            if sg[0] <= t <= sg[1]: return sg
    def tl_hover(s, e):
        sg = s.seg_at(e.x)
        if sg: s.tip.config(text=f"{fmt(sg[0])} → {fmt(sg[1])}  •  {'باقي' if sg[2] else 'محذوف'}{' • زوم' if sg[3] else ''}")
    def tl_click(s, e, right):
        sg = s.seg_at(e.x)
        if not sg or s.busy: return
        k = s.plan["keep"]
        if right and sg[2]: k[:] = [[a, b, 1 - z] if a == sg[0] else [a, b, z] for a, b, z in k]
        elif not right:
            k[:] = [x for x in k if x[0] != sg[0]] if sg[2] else clean(k + [[sg[0], sg[1], 0]], s.meta["dur"], 0)
        if not k: k.append([sg[0], sg[1], 0])
        s.mark_dirty()
    def cap_toggle(s): s.plan["captions"] = s.capv.get(); s.mark_dirty()
    def mark_dirty(s): s.dirty = True; s.save(); s.refresh(); s.rb.config(bg=ACC, fg="white")
    def refresh(s):
        tot = sum(b - a for a, b, _ in s.plan["keep"]); cuts = sum(1 for x in s.segs() if not x[2])
        s.info.config(text=f"الأصلي {fmt(s.meta['dur'])}  ←  بعد المونتاج {fmt(tot)}  •  {cuts} قصّة  •  "
                           f"{sum(z for *_, z in s.plan['keep'])} زوم  •  {len(s.plan.get('titles', []))} عنوان متحرك"
                           + ("  •  ⚠ فيه تعديلات ما تصدرت" if s.dirty else ""))
        s.draw_tl()

    def rerender(s, after=None):
        if s.busy: return
        s.busy = True; s.set_status("🎬 أصدّر النسخة الجديدة...")
        def job():
            try:
                s.do_render(lambda p: s.ui(s.set_status, f"🎬 أصدّر النسخة الجديدة... {int(p)}%"))
                s.ui(s.set_status, "✓ تصدرت — اضغط معاينة"); s.ui(s.refresh); s.ui(lambda: s.rb.config(bg=PANEL, fg=FG))
            except Exception as e: s.ui(messagebox.showerror, APP, str(e))
            finally: s.busy = False
        threading.Thread(target=job, daemon=True).start()

    def say(s, msg, tag):
        s.chat.config(state="normal"); s.chat.insert("end", ("انت: " if tag == "me" else "Legend: ") + msg + "\n", tag)
        s.chat.config(state="disabled"); s.chat.see("end")
    def send(s):
        msg = s.ent.get().strip()
        if not msg or s.busy: return
        s.ent.delete(0, "end"); s.say(msg, "me"); s.busy = True; s.set_status("🤖 Legend يفكر ويعدل...")
        threading.Thread(target=s.chat_job, args=(msg,), daemon=True).start()
    def chat_job(s, msg):
        try:
            cur = {k: s.plan.get(k) for k in ("keep", "titles", "captions", "cap_color")}
            hist = "\n".join(s.hist[-10:])
            p = jparse(ask_claude(f"{SYS_CHAT}\n\nمدة الأصلي: {s.meta['dur']:.1f} ثانية\nالخطة الحالية:\n{json.dumps(cur, ensure_ascii=False)}"
                                  f"\n\nالتفريغ:\n{tx(lines_of(s.words))}\n\nآخر المحادثة:\n{hist}\n\nطلب المستخدم: {msg}"))
            reply = p.pop("reply", "تم ✓"); s.hist += [f"المستخدم: {msg}", f"انت: {reply}"]
            if "keep" in p: p["keep"] = clean(p["keep"], s.meta["dur"], 0) or s.plan["keep"]
            changed = bool(p); s.plan.update(p); s.save()
            s.ui(s.say, reply, "ai")
            if changed:
                s.ui(lambda: s.capv.set(s.plan.get("captions", True))); s.ui(s.refresh)
                s.do_render(lambda x: s.ui(s.set_status, f"🎬 أطبّق التعديل... {int(x)}%"))
                s.ui(s.set_status, "✓ تعدّل المقطع — اضغط معاينة"); s.ui(s.refresh)
            else: s.ui(s.set_status, "")
        except Exception as e: s.ui(s.say, f"صار خطأ: {e}", "ai"); s.ui(s.set_status, "")
        finally: s.busy = False

def selftest():                                               # يشتغل وقت البناء: يتأكد إن كل شي داخل الـ exe سليم
    log = open(os.path.join(HOME, "selftest.log"), "w", encoding="utf-8")
    try:
        d = tempfile.mkdtemp(); v = os.path.join(d, "t.mp4"); o = os.path.join(d, "o.mp4")
        subprocess.run([FF(), "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=25:d=6", "-f", "lavfi",
                        "-i", "sine=d=6", "-shortest", v], check=True, creationflags=NOWIN)
        m = probe(v); log.write(f"probe ok {m}\nass={has_ass()}\n")
        from faster_whisper import WhisperModel
        segs, _ = WhisperModel("tiny", device="cpu", compute_type="int8").transcribe(load_audio(v), word_timestamps=True, vad_filter=True)
        list(segs); log.write("whisper ok\n")
        plan = {"keep": clean([[0, 2, 0], [3, 5, 1]], m["dur"]), "titles": [{"text": "تجربة", "at": 0.2, "dur": 1}], "captions": True}
        render(v, plan, m, [[0.3, 0.8, "هلا"]], o, lambda p: None)
        if probe(o)["dur"] < 3: raise RuntimeError("render length wrong")
        log.write("render ok\nALL OK\n"); log.close(); sys.exit(0)
    except SystemExit: raise
    except Exception as e:
        import traceback; log.write(traceback.format_exc()); log.close(); sys.exit(1)

if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest()
    if os.name == "nt":
        try: import ctypes; ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception: pass
    first_run(); App().root.mainloop()
