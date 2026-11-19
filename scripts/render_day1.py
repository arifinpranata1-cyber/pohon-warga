#!/usr/bin/env python3
"""Day 1 Pohon Warga (reset): "Aku bikin desa di langit." 25 detik, 9:16.

  python3 render_day1.py --preview      # 6 frame contoh
  python3 render_day1.py --out reel.mp4 # video penuh

Memakai salinan viewer di ../site_day1 (?empty&balai&notree&d1).
Teks berada di safe zone Reels: atas 260px, bawah 440px, kanan 160px kosong (ukuran 1080x1920).
"""
import argparse, functools, http.server, math, socketserver, subprocess, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
SITE = HERE.parent / "site"
OUT = HERE / "out"
W, H, FPS, DUR = 540, 960, 24, 25

# ---------- setup dunia: Budi diam di depan balai, kavling kosong, papan aturan ----------
SETUP_JS = r"""
() => {
  const T = window.THREE, S = window.__S;
  // Budi berdiri diam (dikeluarkan dari animasi jalan)
  const A = window.__ACT; for (let i = A.length - 1; i >= 0; i--) if (A[i].type === 'budi') A.splice(i, 1);
  // Balai menghadap keluar, tampil penuh
  const P = window.BALAI_POS; const len = Math.hypot(P.x, P.z); const dx = P.x / len, dz = P.z / len;
  window.BALAI.rotation.y += Math.PI; window.__balai(1);
  // jarum jam balai: 19:30 (jarum jam di antara 7 dan 8, jarum menit di 6)
  window.BALAI.traverse(o => { if (o.isMesh && o.material && o.material.color && o.material.color.getHex() === 0x1a1466 && o.geometry.type === 'CylinderGeometry') o.visible = false; });
  const hand = (len, wid, ang) => { const h = new T.Group(); h.position.set(0, 4.4, 2.44); h.rotation.z = -ang;
    const m = new T.Mesh(new T.BoxGeometry(wid, len, .04), new T.MeshBasicMaterial({ color: 0x1a1466 })); m.position.y = len / 2; h.add(m); window.BALAI.add(h); };
  hand(.27, .07, 7.5 / 12 * 2 * Math.PI); hand(.40, .05, Math.PI);
  const face = Math.atan2(dx, dz), px = dz, pz = -dx;
  const B = { x: dx * 16.8, z: dz * 16.8 };
  const bu = window.BUDI; bu.position.set(B.x, 0, B.z); bu.rotation.y = face;
  // kanvas -> tekstur
  const tex = (w, h, draw) => { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
    const t = new T.CanvasTexture(c); t.colorSpace = T.SRGBColorSpace; t.anisotropy = 8; return t; };
  // kavling kosong (garis putus-putus kuning)
  const L = { x: B.x + px * 4.6, z: B.z + pz * 4.6 };
  const plotT = tex(512, 512, (g, w, h) => { g.fillStyle = 'rgba(255,210,61,0.18)'; g.beginPath(); g.roundRect(24, 24, 464, 464, 60); g.fill();
    g.setLineDash([46, 30]); g.lineWidth = 26; g.strokeStyle = '#ffd23d'; g.beginPath(); g.roundRect(24, 24, 464, 464, 60); g.stroke(); });
  const plot = new T.Mesh(new T.PlaneGeometry(3.8, 3.8), new T.MeshBasicMaterial({ map: plotT, transparent: true, depthWrite: false }));
  plot.rotation.x = -Math.PI / 2; plot.rotation.z = face; plot.position.set(L.x, 0.96, L.z); plot.renderOrder = 5; S.add(plot);
  const kamuT = tex(640, 180, (g) => { g.fillStyle = '#17102b'; g.beginPath(); g.roundRect(14, 20, 612, 130, 65); g.fill();
    g.setLineDash([28, 18]); g.lineWidth = 12; g.strokeStyle = '#ffd23d'; g.stroke();
    g.font = '800 78px Poppins'; g.textBaseline = 'middle'; g.textAlign = 'left';
    const wa = g.measureText('@').width, wk = g.measureText('kamu?').width, x0 = 320 - (wa + wk) / 2;
    g.fillStyle = '#ffd23d'; g.fillText('@', x0, 88); g.fillStyle = '#ffffff'; g.fillText('kamu?', x0 + wa, 88); });
  const kamu = new T.Sprite(new T.SpriteMaterial({ map: kamuT, depthTest: false, transparent: true }));
  kamu.scale.set(3.4, 0.96, 1); kamu.position.set(L.x, 2.9, L.z); kamu.renderOrder = 20; S.add(kamu); window.__KAMU = kamu;
  // papan aturan kayu
  const Bd = { x: B.x + px * 10.2, z: B.z + pz * 10.2 };
  const board = new T.Group(); board.position.set(Bd.x, 0, Bd.z); board.rotation.y = face; S.add(board);
  const wood = new T.MeshStandardMaterial({ color: 0x8a5a34, roughness: .9, flatShading: true });
  for (const sx of [-1.55, 1.55]) { const p = new T.Mesh(new T.BoxGeometry(.22, 3.2, .22), wood); p.position.set(sx, 1.6, 0); p.castShadow = true; board.add(p); }
  const fr = new T.Mesh(new T.BoxGeometry(3.7, 2.3, .2), wood); fr.position.set(0, 2.25, 0); fr.castShadow = true; board.add(fr);
  const signT = tex(1024, 640, (g, w, h) => { g.fillStyle = '#FFF3C4'; g.beginPath(); g.roundRect(0, 0, w, h, 40); g.fill();
    g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = '#1A1466'; g.font = '800 92px Poppins';
    g.fillText('FOLLOW', w / 2, 120); g.font = '800 70px Poppins'; g.fillText('= JADI WARGA', w / 2, 210);
    g.fillStyle = '#D0127A'; g.font = '800 92px Poppins'; g.fillText('KOMEN', w / 2, 390); g.font = '800 64px Poppins'; g.fillText('= MINTA BANGUNAN', w / 2, 480); });
  const face2 = new T.Mesh(new T.PlaneGeometry(3.45, 2.1), new T.MeshBasicMaterial({ map: signT }));
  face2.position.set(0, 2.25, .111); board.add(face2);
  window.__D1 = { B, L, Bd, dir: [dx, dz], perp: [px, pz],
    clock: { x: P.x + dx * 2.35 * 1.45, y: 4.4 * 1.45, z: P.z + dz * 2.35 * 1.45 } };
  return window.__D1;
}
"""

# ---------- kamera ----------
def lerp(a, b, k): return [x + (y - x) * k for x, y in zip(a, b)]
def ease(k): k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)

def keyframes(d):
    dx, dz = d["dir"]; px, pz = d["perp"]; B, L, Bd, C = d["B"], d["L"], d["Bd"], d["clock"]
    a = math.atan2(dx, dz) - 0.45                       # sedikit menyamping supaya pulau terlihat 3D
    wide = [math.sin(a) * 125, 26, math.cos(a) * 125, 0, 9, 0, 30]
    budi = [B["x"] + dx * 11 + px * 1.5, 9.0, B["z"] + dz * 11 + pz * 1.5, B["x"], 1.4, B["z"], 32]
    mx, mz = B["x"] + px * 3.4, B["z"] + pz * 3.4
    plot = [mx + dx * 24, 13.0, mz + dz * 24, mx, 1.6, mz, 34]
    board = [Bd["x"] + dx * 10, 6.0, Bd["z"] + dz * 10, Bd["x"], 2.7, Bd["z"], 34]
    clock = [C["x"] + dx * 24 + px * 2, 9.0, C["z"] + dz * 24 + pz * 2, C["x"] - dx * 1, 5.6, C["z"] - dz * 1, 34]
    # (waktu, pose) — tahan, lalu berpindah halus
    return [(0, wide), (2, lerp(wide, budi, .08)), (6, budi), (8, budi), (9.5, plot), (11, plot),
            (12.5, board), (16, board), (17.5, clock), (21, clock), (24, wide), (25, wide)]

def camera(t, K):
    for (t0, p0), (t1, p1) in zip(K, K[1:]):
        if t0 <= t <= t1:
            return lerp(p0, p1, ease((t - t0) / (t1 - t0)) if t1 > t0 else 1)
    return K[-1][1]

# ---------- teks (safe zone: top >= 13.6%, bottom <= 77%, kanan 15% kosong) ----------
SAFE = "position:absolute;left:5%;right:16%;display:flex;flex-direction:column;align-items:center;gap:14px;font-family:Poppins;text-align:center;"
BOX = "background:rgba(28,18,80,.78);color:#fff;border-radius:22px;padding:12px 22px;font-weight:700;text-shadow:0 2px 0 rgba(0,0,0,.35);"
YEL = "background:#ffd23d;color:#1a1466;border-radius:18px;padding:8px 26px;font-weight:800;box-shadow:0 6px 0 rgba(0,0,0,.22);"

def overlay(scene):
    if scene == "hook":
        return (f'<div style="{SAFE}top:15%"><div class="pp" style="{YEL}font-size:72px;line-height:1.05">DAY 1</div>'
                f'<div class="pp" style="{BOX}font-size:34px">Aku bikin desa di langit.</div></div>')
    if scene == "warga":
        return (f'<div style="{SAFE}top:15%"><div class="pp" style="{YEL}font-size:46px">WARGA: 1</div>'
                f'<div class="pp" style="{BOX}font-size:32px">Warganya baru satu.</div></div>')
    if scene == "kamu":
        return f'<div style="{SAFE}top:15%"><div class="pp" style="{BOX}font-size:34px">Kamu bisa tinggal di sini.</div></div>'
    if scene == "aturan":
        return f'<div style="{SAFE}top:15%"><div class="pp" style="{BOX}font-size:34px">Aturannya cuma dua.</div></div>'
    if scene == "jam":
        return (f'<div style="{SAFE}top:15%"><div class="pp" style="{YEL}font-size:40px">19:30 WIB</div>'
                f'<div class="pp" style="{BOX}font-size:25px;line-height:1.3">Komen sebelum 19:00.<br>Jam 19:30 aku bangun.</div></div>')
    return (f'<div style="{SAFE}top:15%"><div class="pp" style="{BOX}font-size:40px;line-height:1.2">Mau dibangun<br>apa dulu?</div>'
            f'<div class="pp" style="{YEL}font-size:28px">Komen di bawah</div></div>')

SCENES = [(0, 2, "hook"), (2, 6, "warga"), (6, 11, "kamu"), (11, 16, "aturan"), (16, 21, "jam"), (21, 25, "end")]

def scene_at(t):
    for a, b, n in SCENES:
        if a <= t < b: return n, t - a
    return SCENES[-1][2], t - SCENES[-1][0]

def pop(dt):
    """easeOutBack 0.35 detik, lalu diam."""
    k = min(1.0, dt / 0.35); c = 1.70158
    return 1 + (c + 1) * (k - 1) ** 3 + c * (k - 1) ** 2

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--out", default=str(OUT / "day1.mp4"))
    args = ap.parse_args()
    frames = OUT / ("preview" if args.preview else "frames"); frames.mkdir(parents=True, exist_ok=True)
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(SITE)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    times = [1.0, 5.6, 10.2, 14.5, 19.5, 24.6] if args.preview else [i / FPS for i in range(DUR * FPS)]
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/index.html?m=senja&empty&balai&notree&d1&nosnd", wait_until="load")
        pg.wait_for_function("window.__done===true", timeout=120000)
        pg.add_style_tag(content=".top,.pill,.card,#ui{display:none!important}"
                         "@font-face{font-family:Poppins;src:url('fonts/Poppins-Bold.ttf');font-weight:700 800}")
        pg.evaluate("()=>document.fonts.load('800 40px Poppins')")
        d = pg.evaluate(SETUP_JS)
        K = keyframes(d)
        pg.evaluate("()=>{const o=document.createElement('div');o.id='ov';o.style.cssText='position:fixed;inset:0;pointer-events:none;z-index:99';document.body.appendChild(o)}")
        last = None
        for i, t in enumerate(times):
            sc, dt = scene_at(t)
            if sc != last:
                pg.evaluate("h=>{document.getElementById('ov').innerHTML=h}", overlay(sc)); last = sc
                pg.evaluate("v=>{window.__KAMU.visible=v}", sc in ("kamu", "aturan"))
            s = pop(dt) if not args.preview else 1.0
            pg.evaluate("s=>document.querySelectorAll('#ov .pp').forEach(e=>e.style.transform='scale('+s+')')", s)
            pg.evaluate("([c,tt])=>{window.__tt=tt;window.__cam(c)}", [camera(t, K), 10 + t])
            pg.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
            pg.screenshot(path=str(frames / (f"p{i}.png" if args.preview else f"f{i:04d}.png")))
            if not args.preview and i % 48 == 0: print(f"frame {i}/{len(times)}", flush=True)
        b.close()
    srv.shutdown()
    if args.preview:
        print("preview:", frames); return
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "f%04d.png"),
                    "-vf", "scale=1080:1920:flags=lanczos", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-r", "30", args.out], check=True)
    print("video:", args.out)

if __name__ == "__main__":
    main()
