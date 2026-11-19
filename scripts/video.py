#!/usr/bin/env python3
"""Reel harian Pohon Warga: rekam viewer 3D frame demi frame, lalu susun dengan ffmpeg.

Pakai:
  python3 scripts/video.py --preview            # 5 gambar contoh saja
  python3 scripts/video.py --out out/reel.mp4   # video penuh (20 detik, 9:16)

Viewer dirender di 540x960 (cepat di server tanpa GPU), lalu diperbesar ke 1080x1920.
Waktu animasi viewer dikendalikan lewat window.__tt dan kamera lewat window.__cam,
jadi hasilnya mulus walau tiap frame butuh beberapa detik.
"""
import argparse, functools, http.server, json, math, os, socketserver, subprocess, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
W, H, FPS, DUR = 540, 960, 24, 25
SPEED = 3.0  # animasi viewer berjalan 3x (efek time-lapse)

# (mulai, selesai, nama)
SCENES = [(0, 3, "hook"), (3, 9, "usul"), (9, 17, "bangun"), (17, 21, "statistik"), (21, 25, "ajakan")]

def load_day():
    if os.environ.get("PREVIEW_SAMPLE"):   # hanya untuk preview: komentar asli dari post Day 1
        return {"day": 2, "stats": {"population": 3, "buildings": 2, "kas": 29},
                "events": [{"type": "build", "name": "Rumah baru untuk @odds.creativelab"}],
                "usul_teratas": {"user": "odds.creativelab", "text": "Halo. Bangun rumah buat saya",
                                 "lain": [("stupidodds", "Bangun rumah dongss")]}}
    days = json.loads((SITE / "data" / "days.json").read_text(encoding="utf8"))
    return days[-1] if days else {"day": 1, "stats": {}, "events": [], "usul_teratas": None}

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def usul_text(d):
    u = d.get("usul_teratas")
    if isinstance(u, dict):
        user = u.get("user") or u.get("by") or ""
        text = u.get("text") or u.get("usul") or u.get("label") or ""
        if text:
            return (f"@{user}" if user else ""), text
    if isinstance(u, str) and u:
        return "", u
    return "", "Belum ada usul. Komen sekarang, Pak RT menunggu!"

def lain_html(d):
    u = d.get("usul_teratas")
    rows = u.get("lain", []) if isinstance(u, dict) else []
    return "".join(f'<div style="margin-top:12px;padding-top:10px;border-top:2px solid #eee;font-weight:500;font-size:20px;color:#241a5c">'
                   f'<b>@{esc(a)}</b> {esc(b)}</div>' for a, b in rows)

def selesai_text(d):
    for e in d.get("events", []):
        t = e.get("type", "")
        if t.startswith("build") or t == "auto_house" or t == "done":
            return e.get("name") or e.get("label") or "Rumah baru berdiri"
    return "Desa terus tumbuh"

def camera(t):
    """Kamera orbit satu putaran penuh. Pose di t=0 dan t=DUR identik supaya video bisa loop."""
    th = 0.4 + 2 * math.pi * t / DUR
    if t < 3:                               # hook: mulai jauh, mendekat cepat
        k = 1 - (1 - t / 3) ** 3
        r, y = 150 - 55 * k, 62 - 24 * k
    elif t > 18:                            # menjauh lagi ke pose awal
        k = (t - 18) / 2
        k = k * k * (3 - 2 * k)
        r, y = 95 + 55 * k, 38 + 24 * k
    else:
        r, y = 95, 38
    return [r * math.sin(th), y, r * math.cos(th), 0, 9, 0, 30]

def overlay_html(scene, d, t):
    st = d.get("stats", {})
    day = d.get("day", 1)
    user, text = usul_text(d)
    base = ("position:absolute;left:6%;right:6%;font-family:Poppins;text-align:center;color:#fff;"
            "background:rgba(36,26,92,.62);border-radius:22px;padding:12px 16px;"
            "text-shadow:0 2px 0 rgba(0,0,0,.35);")
    if scene == "hook":
        return (f'<div style="{base}top:7%;font-size:78px;font-weight:700;line-height:1">DAY {day}</div>'
                f'<div style="{base}top:21%;font-size:28px;font-weight:700">Desa ini dibangun oleh komentarmu</div>')
    if scene == "usul":
        return (f'<div style="position:absolute;left:6%;right:6%;top:8%;background:#fff;border-radius:22px;padding:22px 26px;'
                f'font-family:Poppins;box-shadow:0 8px 0 rgba(0,0,0,.18)">'
                f'<div style="display:inline-block;background:#ff3d6e;color:#fff;font-weight:700;font-size:20px;padding:4px 14px;border-radius:12px">USUL TERATAS</div>'
                f'<div style="font-weight:700;font-size:34px;color:#241a5c;margin-top:12px;line-height:1.15">{esc(text)}</div>'
                f'<div style="font-weight:500;font-size:22px;color:#6b6b88;margin-top:6px">{esc(user)}</div>{lain_html(d)}</div>')
    if scene == "bangun":
        clock = f"x{int(SPEED * 8)}"
        return (f'<div style="position:absolute;left:6%;top:8%;background:#ffd23d;color:#241a5c;font-family:Poppins;font-weight:700;font-size:34px;padding:8px 20px;border-radius:16px;box-shadow:0 5px 0 rgba(0,0,0,.2)">{clock}</div>'
                f'<div style="{base}top:22%;font-size:32px;font-weight:700">{esc(selesai_text(d))}</div>')
    if scene == "statistik":
        def chip(lbl, val):
            return (f'<div style="background:#fff;border-radius:18px;padding:12px 20px;font-family:Poppins;font-weight:700;color:#241a5c;'
                    f'box-shadow:0 5px 0 rgba(0,0,0,.18);text-align:center"><div style="font-size:38px">{val}</div>'
                    f'<div style="font-size:16px;color:#6b6b88;font-weight:500">{lbl}</div></div>')
        return (f'<div style="position:absolute;left:5%;right:5%;top:15%;display:flex;gap:14px;justify-content:center">'
                f'{chip("WARGA", st.get("population", 0))}{chip("BANGUNAN", st.get("buildings", 0))}{chip("KAS", st.get("kas", 0))}</div>')
    return (f'<div style="{base}top:7%;font-size:40px;font-weight:700;line-height:1.1">FOLLOW = JADI WARGA</div>'
            f'<div style="{base}top:19%;font-size:40px;font-weight:700;line-height:1.1;color:#ffd23d">KOMEN = MINTA BANGUNAN</div>')

def scene_at(t):
    for a, b, n in SCENES:
        if a <= t < b:
            return n
    return SCENES[-1][2]

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

def serve():
    handler = functools.partial(Quiet, directory=str(SITE))
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--out", default="out/reel.mp4")
    ap.add_argument("--mood", default="senja")
    args = ap.parse_args()
    d = load_day()
    outdir = Path(args.out).parent
    outdir.mkdir(parents=True, exist_ok=True)
    frames = ROOT / "out" / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    srv, port = serve()
    times = [1.5, 5.5, 11, 16.5, 19.5] if args.preview else [i / FPS for i in range(DUR * FPS)]
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto(f"http://127.0.0.1:{port}/index.html?m={args.mood}", wait_until="load")
        pg.wait_for_timeout(5000)
        pg.add_style_tag(content=".top,.pill,.card,#ui{display:none!important}")
        pg.add_style_tag(content="@font-face{font-family:Poppins;src:url('fonts/Poppins-Bold.ttf');font-weight:700}"
                                 "@font-face{font-family:Poppins;src:url('fonts/Poppins-Medium.ttf');font-weight:500}")
        pg.evaluate("""()=>{const o=document.createElement('div');o.id='ov';o.style.cssText='position:fixed;inset:0;pointer-events:none;z-index:99';document.body.appendChild(o)}""")
        last = None
        for i, t in enumerate(times):
            sc = scene_at(t)
            if sc != last:
                pg.evaluate("h=>{document.getElementById('ov').innerHTML=h}", overlay_html(sc, d, t))
                last = sc
            pg.evaluate("([c,tt])=>{window.__tt=tt;window.__cam(c)}", [camera(t), 10 + t * SPEED])
            pg.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
            name = f"p{i}.png" if args.preview else f"f{i:04d}.png"
            pg.screenshot(path=str(frames / name))
            if not args.preview and i % 24 == 0:
                print(f"frame {i}/{len(times)}", flush=True)
        b.close()
    srv.shutdown()
    if args.preview:
        print("preview di", frames)
        return
    music = ("sine=f=261.63:d=20[a];sine=f=329.63:d=20[b];sine=f=392.0:d=20[c];sine=f=130.81:d=20[d];"
             "[a][b][c][d]amix=inputs=4:normalize=0,tremolo=f=0.4:d=0.35,volume=0.16,"
             "afade=t=in:d=1,afade=t=out:st=18.5:d=1.5[m]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(frames / "f%04d.png"),
                    "-filter_complex", "[0:v]scale=1080:1920:flags=lanczos,unsharp=5:5:0.8[v];" + music,
                    "-map", "[v]", "-map", "[m]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-c:a", "aac", "-b:a", "128k", "-t", str(DUR), "-movflags", "+faststart", args.out], check=True)
    print("selesai:", args.out)

if __name__ == "__main__":
    sys.exit(main())
