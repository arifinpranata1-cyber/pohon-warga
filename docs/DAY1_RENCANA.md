# Day 1 Pohon Warga — Rencana Rombak (ditulis Opus, dikerjakan Sonnet)

Tujuan: satu Reel Day 1 (25–30 dtk, 9:16) yang membuat orang **follow dan komen**, dan situs yang **sama persis** dengan yang dilihat di video.

Aturan kerja (wajib, dari preferensi Arifin):
- Bahasa ke user: Indonesia, sebut diri "saya", jangan pernah "gue".
- **Jangan render video penuh** sebelum: (1) naskah disetujui, (2) 6 frame preview desain asli disetujui.
- Jangan commit/push perubahan viewer sebelum Arifin approve tampilannya (kirim screenshot dulu).
- Jangan pernah tandai konten sebagai AI.
- Teks penting harus di safe zone 1080x1920: atas 260 px, bawah 440 px, kanan 160 px kosong.
- Fakta di layar harus benar (jam, aturan, jumlah kavling) — cek ke data, bukan tebakan.
- Pilih jalur yang paling hemat kuota.

---

## 0. Admin (Arifin, sebelum apa pun)

1. **Batalkan / ganti jadwal post Day 1 lama (19:30 malam ini, 20 Nov)** di Meta Business Suite. Kalau tidak, video lama tetap tayang.
2. Tanggal baru: **Sabtu 21 Nov 19:30 WIB** (cukup waktu untuk approve). Komentar ditutup Minggu 22 Nov 19:00, update 19:30.
3. Workflow "Hari baru Pohon Warga" tetap **disabled** sampai post tayang. Aktifkan lagi setelah Day 1 tayang.
4. Ganti link bio ke `https://pohonwarga.github.io/pohon-warga/`.

---

## 1. Kenapa dirombak (diagnosis video v3)

| # | Masalah | Dampak |
|---|---|---|
| 1 | Video pakai dunia lama (Desa_v4: kuda goyang, pulau hijau), situs pakai Desa_v5 | Orang klik link, lihat desa lain → bingung, tidak percaya |
| 2 | Detik 2,5–6: close-up Budi diam, tanpa teks | Titik orang scroll pergi |
| 3 | Frame pertama tanpa kalimat hook | Hook hanya visual; referensi selalu punya klaim di frame 1 |
| 4 | Budi tidak bicara "aku → kamu" | Keputusan 19 Nov (gaya kreator, bukan narator trailer) belum diterapkan |
| 5 | Tidak ada penanda "WARGA: 1" dan aturan "komen paling banyak like dibangun" dan jam "besok 19:30" | Penonton tidak tahu kapan & kenapa harus komen sekarang |
| 6 | "LHO? KOSONG?!" di y≈1690 (zona caption IG) dan kecil | Tidak terbaca |
| 7 | Saat balai dibangun, topi Budi menutupi bangunan | Payoff hilang |
| 8 | End card: gaya flat lain, avatar Budi versi lain, "3 pengikut", tombol sudah "Mengikuti" | Bukti sosial lemah, logika tombol terbalik |
| 9 | 35 dtk | Blueprint: 20–30 dtk |

Yang **dipertahankan**: jatuh dari kuda + GUBRAK, kotak teks kuning/merah, "FOLLOW = JADI WARGA", balai dibangun sendiri dengan jam time-lapse, pilihan "1 RUMAH / 2 TAMAN / 3 PASAR atau usulmu sendiri", badge DAY 1 kiri atas, @pohonwarga kanan atas, end card berbentuk kartu profil IG.

---

## 2. Viewer dulu (situs = bukti; video direkam dari dunia yang sama)

File: `site/index.html`, `site/data/world.json`, `site/data/days.json`.

1. **Reset data ke kondisi Day 1** (setelah backup `site/data/*.json` ke `site/data/_backup_pre_day1/`):
   - `day: 1`, `population: 1`, residents hanya Budi, buildings hanya `b0 balai done`.
   - Hapus rumah contoh `b1` @odds.creativelab dari world.json **dan** dari `v5/labels.json` (Day 1 harus benar-benar kosong; video bilang kosong).
   - Jalankan `node scripts/test.js` setelah reset; pastikan daily.js masih lolos.
2. **Penduduk mengikuti data.** Jumlah penduduk jalan = `population - 1` (Budi tidak dihitung), maks 12. Day 1 → 0 penduduk, hanya Budi. (Sekarang 3 penduduk di-hardcode di baris `[[0,16.5,200…]]` → ubah jadi loop dari jumlah warga, varian `i % 8`.) Hewan boleh tetap ada (lihat langkah 6).
3. **HUD Day 1**: chip "WARGA: 1" (ganti format "N warga" → "WARGA: N"), chip "HARI KE-1".
4. **Kavling kosong terbaca "tersedia"**: di atas setiap kavling kosong cincin dalam (sektor terdekat balai, maks 12 kavling) tampilkan papan kecil "KOSONG" atau "+". Cukup sprite/plane sederhana, satu material bersama (hemat).
5. **Pola rumput kotak-kotak**: turunkan kontras ±40% (cari material rumput checker di `pw_desa_static.glb` lewat nama material, lerp warnanya ke rata-rata).
6. **Hewan** (permintaan lama, setelah poin 1–5 di-approve): buat di Blender (scene Desa_v5_approved, collection `PW_animals`) gaya sama dengan penduduk: 4 ayam, 1 anjing, 1 kucing, 3 burung terbang. Ukuran: ayam/kucing ≈ setinggi lutut penduduk, anjing ≈ pinggang. Pivot kaki terpisah. Ekspor `site/v5/pw_hewan.glb` (< 600 KB, decimate). Pasang di sistem agent yang sudah ada (`agent(...,'wander')`, `'follow'` untuk anjing → ikut Budi). Ini **bukan syarat** untuk Day 1 — kerjakan kalau waktu cukup.
7. **Kamera pembuka situs**: 2 dtk mulai dekat Budi (pos ±12 unit), lalu mundur mulus ke HOME. Skip kalau ada `?m=` atau `?cam=` di URL.
8. Tes: Playwright `?m=pagi|siang|sore|malam`, ukuran 1100x700 dan 390x844. Nol error konsol. Kirim 2 screenshot ke Arifin → **tunggu approve** → commit + push → cek Pages deploy sukses → buka `?v=N`.

---

## 3. Naskah Day 1 baru (±28 dtk) — **perlu approve Arifin**

Suara: Budi bicara sebagai "aku" ke "kamu" lewat teks gelembung + kotak kinetik. Tanpa VO default (opsional, lihat §5).

| Dtk | Visual (Desa_v5, Blender) | Teks layar |
|---|---|---|
| 0.0–1.0 | Kamera menukik dari atas pohon besar langsung ke wajah Budi (signature shot) | **"AKU BIKIN DESA."** (kuning, besar) |
| 1.0–3.0 | Budi naik kuda goyang di depan pohon → jatuh, GUBRAK, topi terbang | "GUBRAK!" lalu **"...TAPI WARGANYA CUMA AKU."** |
| 3.0–5.0 | Budi bangun, kamera mundur cepat: semua cincin kavling kosong | Gelembung Budi: "Lho? Kok sepi?" + chip **WARGA: 1** |
| 5.0–9.0 | Terbang rendah di atas cincin dalam: 16 rumah sudah jadi, atap abu, label kecil "kosong" | **"16 RUMAH SUDAH JADI."** → **"SEMUANYA KOSONG."** |
| 9.0–12.5 | Satu rumah "hidup": atap abu → ungu, lampu menyala, label "@namamu" muncul, karakter kecil keluar pintu | **"FOLLOW = RUMAH INI JADI MILIKMU"** + kecil: "cari namamu di link bio, lalu jalan-jalan" |
| 12.5–17.0 | Gelembung komentar palsu-jelas (avatar abu, "@contoh") "bangun kolam lele dong" → kolam muncul, Budi kaget (lompat, topi naik) | **"KOMEN = AKU BANGUNIN"** + kecil: "komen paling banyak ❤️ dibangun duluan" |
| 17.0–21.5 | Time-lapse balai: jam 08:00 → 17:00, kamera samping 3/4 (Budi di kiri frame, **tidak menutupi** bangunan), topi Budi terbang saat balai selesai | Gelembung: "Sambil nunggu, aku bangun balai dulu." |
| 21.5–26.0 | Wide desa senja, lampu menyala | **"BESOK 19:30 AKU BANGUN USULAN TERATAS"** → "1 RUMAH / 2 TAMAN / 3 PASAR / atau usulmu sendiri" |
| 26.0–28.5 | End card versi 3D: render Budi 3D (bukan avatar 2D lama) di kartu profil; tombol **"Ikuti"** biru → jari tap → berubah **"Mengikuti ✓"**; counter **WARGA: 1 → 2** | "Cari rumahmu di peta → link di bio" |

Catatan fakta: angka 78 = jumlah slot di `site/v5/pw_slots.json` (cek ulang sebelum render; kalau berubah, ganti teks). Jam 19:30 = jadwal workflow (cek `.github/workflows/daily.yml`).

---

## 4. Produksi video (Blender, file `Desa_v5_approved.blend` di `Downloads\pw_prev`)

1. **Jangan ubah file approved.** Simpan salinan `Desa_v5_day1.blend` dan kerja di situ.
2. Ambil dari `Desa_v4_backup_sebelum_retime.blend` (append): `KudaRoll`, aksi/animasi Budi (jatuh, kaget, topi), properti palu. Budi di v5 = `Budi_v4.001` — samakan rig.
3. Kosongkan semua kavling (Day 1). Rumah demo (shot 9–12.5) dan kolam (shot 12.5–17) dianimasikan scale 0→1 dengan overshoot 1.15.
4. Kamera: satu kamera per shot, potong keras antar shot (bukan satu kamera panjang). Lensa 35–50 mm untuk close-up, 24 mm untuk wide. Gerak cepat di 0–1 dtk dan 3–5 dtk (ease-out), lainnya pelan.
5. Render Eevee 1080x1920, 24 fps. Pencahayaan pakai preset "sore/senja" yang sudah approved (ungu-pink), shot 21.5–26 malam dengan lampu.
6. **Preview dulu**: render 6 still (dtk 0.5, 2.0, 6.0, 10.0, 15.0, 27.0) **dengan teks overlay final** → kirim ke Arifin → tunggu approve.
7. Setelah approve: render frame penuh → overlay teks & end card dengan pipeline overlay yang dipakai v3 (lihat `scripts/render_day1.py` untuk gaya kotak teks; font Inter Display Black caps) → ffmpeg encode H.264 CRF 18 preset veryfast, AAC 192k.
8. Audio: musik ceria pelan + SFX (whoosh di tukikan kamera, GUBRAK, pop saat rumah/kolam muncul, ting saat "Mengikuti"). Loudness −14 LUFS, puncak ≤ −1 dB.
9. Cek akhir: tonton ulang per detik; semua teks di safe zone; durasi 26–30 dtk; tidak ada frame hitam di akhir.

---

## 5. Paket posting

- **VO opsional**: kalau Arifin mau VO, dia buat sendiri di ElevenLabs dari teks §3 (suara Budi). Default: tanpa VO.
- **Cover**: still dari dtk 6 (desa kosong + "SATU BUAT KAMU"), badge DAY 1, tanpa poster.
- **Caption** (draf, perlu approve):
  ```
  DAY 1. Aku bikin desa, tapi warganya baru aku 🥲
  
  🏠 Follow = rumahmu muncul di desa (cari namamu di link bio)
  💬 Komen = usul bangunan. Komen dengan ❤️ terbanyak aku bangun besok 19:30 WIB
  
  Mau bangun apa duluan? Rumah, taman, pasar… atau usul gilamu sendiri 👇
  
  #pohonwarga #desaonline #game #lowpoly
  ```
- **Komentar pertama (pin)**: "Contoh: 'bangun warung bakso' 😄 Komen sebelum Minggu 19:00 WIB ya!"
- **Satu jam pertama**: balas semua komentar sebagai Budi ("Siap, dicatat! 📝").
- Label AI: **OFF**.

---

## 6. Ide tambahan (Opus) — pilih yang mau dipakai

1. **Warga Pendiri**: 20 follower pertama dapat label emas "Pendiri" di peta selamanya. Sebut di caption Day 2 → alasan follow sekarang, bukan nanti.
2. **Kavling bernama**: tiap kavling punya nomor; komen "ambil kavling 7" = rumahmu di situ. Interaksi sederhana, bikin orang buka situs.
3. **Seri "Budi gagal lagi"**: tiap episode Budi celaka kecil saat membangun (komedi berulang = alasan nonton besok).
4. **Usulan aneh dibangun harfiah** (gaya Desa Ase Jaya) sejak Day 2, dengan label "Usulan @nama".
5. **Peta = bukti**: tiap video Day N ditutup screenshot situs dengan rumah follower baru ber-label → orang ingin melihat namanya sendiri.

---

## 7. Urutan kerja Sonnet (checklist)

- [ ] 0. Ingatkan Arifin soal jadwal post lama (§0) — tunggu konfirmasi tanggal baru
- [ ] 1. Naskah §3 + caption §5 → kirim → **approve**
- [ ] 2. Viewer §2 poin 1–5, 7 → screenshot → **approve** → push
- [ ] 3. Blender §4 langkah 1–5 → 6 still → **approve**
- [ ] 4. Render penuh + audio §4 langkah 7–9 → kirim MP4
- [ ] 5. Hewan §2 poin 6 (kalau waktu cukup, setelah Day 1 terkirim)
- [ ] 6. Setelah tayang: aktifkan workflow, pantau run pertama

---

## 8. Keputusan 20 Nov sore (Arifin) — sudah masuk viewer lokal, BELUM di-push

- Postingan lama dibatalkan. Day 1 baru tayang kalau semuanya siap (tidak harus Sabtu).
- **Rumah dibangun dulu**: 16 rumah netral (atap abu, label "kosong") di cincin dalam; saat ada follower, rumah itu berganti atap sesuai sektor + label @nama. Minimal 8 rumah kosong selalu tersedia (konstanta `PRE=16`, `VAC=8` di `site/index.html`). Kavling luar tetap tanah kosong berpagar.
- **Cari & main**: cari @username → kartu info → tombol "Main sebagai @username" → karakter berdiri di depan rumahnya, bisa dijalankan (WASD/panah/joystick), kamera ikut dan bisa diputar, tabrakan dengan rumah/pohon/batu/penduduk, tidak bisa masuk sungai (jembatan bisa dilewati). Karakter dipilih deterministik dari username (8 varian).
- **Day 1 = data bersih**: `day 0`, warga 1, hanya balai. HUD "WARGA: 1" + "HARI KE-1". Cadangan data lama di `data_backup/`.
- **Penduduk berjalan mengikuti data** (maks 12). Day 1: hanya Budi.
- **Parameter uji**: `?demo=N` mengisi N rumah palsu (hanya untuk tes/preview), `?nointro=1` melewati kamera pembuka.
- **Semua 5 ide Opus disetujui** (§6). Status: (1) label ★ Pendiri untuk 20 warga pertama — sudah di viewer; (2) "ambil kavling N" — tugas engine Day 2 (`scripts/daily.js` parse kata kunci, klaim slot tertentu); (3) seri "Budi gagal lagi" — konten, mulai Day 2; (4) usulan aneh dibangun apa adanya dengan label "Usulan @nama" — tugas engine+viewer Day 2 (tipe bangunan `usulan`, papan generik + label); (5) penutup video berupa peta dengan rumah follower baru — mulai Day 2.
