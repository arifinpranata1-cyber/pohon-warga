// Uji: mock API Instagram (paging, duplikat, urutan) + 5 hari berturut-turut + determinisme.
const assert = require('assert'), fs = require('fs'), os = require('os'), path = require('path'), { execFileSync } = require('child_process');
const { fetchInput } = require('./ig');
const mk = (id, u, t, l, ts) => ({ id, username: u, text: t, like_count: l, timestamp: ts });
const pages = {
  '/me?': { username: 'pohonwarga', followers_count: 42 },
  '/me/media': { data: [{ id: 'm1' }, { id: 'm2' }] },
  'm1/comments': { data: [mk('c2', 'Budi_A', 'bikin warung', 3, '2026-11-19T01:00:00Z'), mk('c1', 'sari', 'halo', 0, '2026-11-19T00:00:00Z')], paging: { next: 'https://graph.instagram.com/page2?access_token=x' } },
  'page2': { data: [mk('c3', 'dewi', 'jembatan!', 9, '2026-11-19T02:00:00Z'), mk('c4', 'seen', 'sudah', 1, '2026-11-18T00:00:00Z')] },
  'm2/comments': { data: [{ id: 'c5', text: 'tanpa username' }] },
};
const fakeFetch = async url => { const k = Object.keys(pages).find(k => url.includes(k)); return { ok: !!k, status: k ? 200 : 404, json: async () => pages[k] || { error: { message: 'x', code: 1 } } }; };
(async () => {
  const r = await fetchInput({ token: 't', seen: new Set(['c4']), fetchFn: fakeFetch });
  assert.deepStrictEqual(r.comments.map(c => c.id), ['c1', 'c2', 'c3']);
  assert.strictEqual(r.comments[1].user, 'budi_a'); assert.strictEqual(r.followers, 42);
  console.log('ig.js OK: paging, duplikat, urutan, huruf kecil');
  const run = () => { const d = fs.mkdtempSync(path.join(os.tmpdir(), 'pw-')); for (let i = 0; i < 5; i++) execFileSync('node', [path.join(__dirname, 'daily.js'), '--fake'], { env: { ...process.env, DATA_DIR: d, IG_TOKEN: '' }, stdio: 'pipe' }); return fs.readFileSync(path.join(d, 'world.json'), 'utf8'); };
  const a = run(), b = run(); assert.strictEqual(a, b, 'tidak deterministik'); assert.ok(a.length > 100);
  const w = JSON.parse(a); console.log('5 hari OK: hari', w.day, '| populasi', w.population, '| RT', w.rts.length, '| bangunan', Object.keys(w.buildings).length);
})().catch(e => { console.error('GAGAL', e.message); process.exit(1); });
// Uji input manual
(() => {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'pwm-')), f = path.join(d, 'input.txt');
  fs.writeFileSync(f, '# contoh\nfollowers: 12\n@Sari bikin warung dong\nbudi_a jembatan!\nrusak\n');
  const env = { ...process.env, DATA_DIR: d, MANUAL_FILE: f, IG_TOKEN: '' };
  const out = execFileSync('node', [path.join(__dirname, 'daily.js')], { env }).toString();
  assert.ok(out.includes('Input manual: 12 followers, 2 komentar'), out);
  const w = JSON.parse(fs.readFileSync(path.join(d, 'world.json'), 'utf8'));
  assert.strictEqual(w.day, 1); assert.ok(w.residents.sari && w.residents.budi_a, 'warga manual tidak terdaftar');
  assert.ok(fs.readFileSync(f, 'utf8').includes('Sudah diproses'), 'file tidak dikosongkan');
  const out2 = execFileSync('node', [path.join(__dirname, 'daily.js')], { env }).toString();
  assert.ok(out2.includes('dilewati'), 'harus dilewati saat kosong');
  console.log('input manual OK: 2 komentar -> 2 warga, file dikosongkan, hari kosong dilewati');
})();
