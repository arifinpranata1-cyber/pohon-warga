// Jalankan satu hari simulasi: node scripts/daily.js [--fake] [--dry]
// Tanpa IG_TOKEN (atau dengan --fake) memakai komentar palsu agar bisa diuji.
const fs = require('fs'), path = require('path');
const { step, newWorld, rng } = require('../engine/engine');
const { fetchInput } = require('./ig');

const DATA = process.env.DATA_DIR || path.join(__dirname, '..', 'site', 'data');
const KEEP_DAYS = 30;
const args = process.argv.slice(2);
const read = (f, d) => { try { return JSON.parse(fs.readFileSync(path.join(DATA, f), 'utf8')); } catch { return d; } };
const write = (f, v) => fs.writeFileSync(path.join(DATA, f), JSON.stringify(v));
const todayWIB = () => new Date(Date.now() + 7 * 3600e3).toISOString().slice(0, 10);

function fakeInput(day) {
  const r = rng('fake-' + day), words = ['bikin warung dong', 'jembatan!', 'rumah kecil', 'sumur', 'menara ronda', 'kebun bunga', 'lampion', 'balai warga', 'halo semua'];
  const followers = 1 + day * 3 + Math.floor(r() * 5), comments = [];
  for (let i = 0; i < 2 + Math.floor(r() * 4); i++) comments.push({ id: `f${day}-${i}`, user: 'warga' + Math.floor(r() * (followers + 5)), text: words[Math.floor(r() * words.length)], likes: Math.floor(r() * 20), ts: i });
  return { followers, comments, newIds: comments.map(c => c.id) };
}

(async () => {
  fs.mkdirSync(DATA, { recursive: true });
  let world = read('world.json', null) || newWorld(todayWIB());
  const cursor = read('cursor.json', { seen: [] });
  const useFake = args.includes('--fake') || !process.env.IG_TOKEN;
  const input = useFake ? fakeInput(world.day + 1) : await fetchInput({ token: process.env.IG_TOKEN, seen: new Set(cursor.seen) });
  console.log(`${useFake ? 'DATA PALSU' : 'Instagram'}: ${input.followers} followers, ${input.comments.length} komentar baru`);

  const out = step(world, { followers: input.followers, comments: input.comments });
  if (args.includes('--dry')) { console.log(JSON.stringify(out.log.stats)); return; }

  const days = read('days.json', []); days.push(out.log);
  write('world.json', out.state);
  write('days.json', days.slice(-KEEP_DAYS));
  write('cursor.json', { seen: [...cursor.seen, ...input.newIds].slice(-5000) });
  console.log(`Hari ${out.log.day}:`, JSON.stringify(out.log.stats));
})().catch(e => { console.error(e.message); process.exit(1); });
