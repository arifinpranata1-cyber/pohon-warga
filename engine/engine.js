// Pohon Warga - simulation engine v0.1 (deterministic, no LLM). state' = step(state, input)
'use strict';
const CFG = {
  rtCapacity: 300, houseCap: 8, startEnergy: 100,
  stages: [[0, 30], [31, 100], [101, 200], [201, 300]], // stage 1..4 by RT population
  cost: { rumah: 4, warung: 6, balai: 8, sumur: 5, menara: 10, kebun: 4, jembatan: 6, lampion: 3 },
  buildDays: { rumah: 1, warung: 2, balai: 3, sumur: 2, menara: 3, kebun: 1, jembatan: 2, lampion: 1 },
  buildKeys: { rumah: ['rumah', 'tinggal'], warung: ['warung', 'makan'], balai: ['balai', 'kumpul'], sumur: ['sumur', 'air'],
    menara: ['menara'], kebun: ['kebun', 'taman'], jembatan: ['jembatan'], lampion: ['lampu', 'lampion'] },
  taskKeys: { RONDA: ['ronda', 'jaga', 'siaga'], MASAK: ['masak', 'dapur'], CARI: ['cari', 'kayu'], PERBAIKI: ['perbaiki', 'tukang'], RAWAT: ['rawat', 'siram'], TIDUR: ['tidur', 'istirahat'] },
  energyCost: { RONDA: 15, MASAK: 10, CARI: 12, PERBAIKI: 12, RAWAT: 10, TIDUR: -40 },
  banned: ['anjing', 'bangsat', 'kontol', 'memek', 'babi'],
};
function hash(str) { let h = 2166136261; for (const c of str) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }
function rng(seedStr) { let a = hash(seedStr); return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const addDays = (d, n) => new Date(Date.parse(d) + n * 864e5).toISOString().slice(0, 10);

function newWorld(startDate, worldId = 'pohon-warga') {
  return { worldId, day: 0, date: addDays(startDate, -1), population: 1, pools: { food: 50, wood: 12 },
    rts: [{ id: 'rt01', number: 1, stage: 1, treeHealth: 100, pop: 1 }],
    residents: { budi: { id: 'budi', username: 'Pak RT Budi', rt: 'rt01', house: 'balai', task: 'RAWAT', energy: 100, joinedDay: 0, optOut: false } },
    buildings: [{ id: 'b0', type: 'balai', rt: 'rt01', status: 'done', damage: 0, by: 'budi', comment: null, day: 0 }],
    queue: [], dragon: { lastAttackDay: -99, pendingAttack: false, warning: false }, log: [] };
}
const norm = s => s.toLowerCase();
const hasKey = (text, keys) => keys.some(k => norm(text).includes(k));
function parseTask(text) { for (const [t, ks] of Object.entries(CFG.taskKeys)) if (hasKey(text, ks)) return t; return null; }
function parseBuild(text) { for (const [t, ks] of Object.entries(CFG.buildKeys)) if (hasKey(text, ks)) return t; return null; }
const cleanName = u => CFG.banned.some(b => u.toLowerCase().includes(b)) ? 'warga' : u;

function step(prev, input) {
  const S = JSON.parse(JSON.stringify(prev));
  S.day += 1; S.date = addDays(prev.date, 1);
  const rand = rng(S.date + S.worldId);
  const log = { day: S.day, date: S.date, events: [], featured_comments: [], notes: [] };
  const named = () => Object.values(S.residents).filter(r => !r.optOut);

  // 1. comments (only those before the gate are passed in by the caller)
  const requests = [];
  for (const c of input.comments) {
    const key = c.user.toLowerCase();
    if (hasKey(c.text, ['keluar'])) { if (S.residents[key]) { S.residents[key].optOut = true; log.events.push({ type: 'opt_out', user: cleanName(c.user) }); } continue; }
    let r = S.residents[key];
    if (!r || r.optOut) {
      r = S.residents[key] = { id: key, username: cleanName(c.user), rt: null, house: null, task: 'CARI', energy: CFG.startEnergy, joinedDay: S.day, optOut: false };
      log.events.push({ type: 'join', user: r.username });
    }
    const t = parseTask(c.text); if (t) { r.task = t; r.explicit = S.day; }
    const b = parseBuild(c.text);
    if (b) requests.push({ type: b, user: key, username: r.username, text: c.text, likes: c.likes || 0, ts: c.ts || 0 });
    else if (!t) log.events.push({ type: 'unmatched', user: r.username });
  }
  // 2. population & RT assignment
  S.population = Math.max(input.followers, named().length);
  let left = S.population;
  for (const rt of S.rts) { rt.pop = Math.min(CFG.rtCapacity, left); left -= rt.pop; }
  const lastRt = S.rts[S.rts.length - 1];
  if (left > 0 && lastRt.pop >= CFG.rtCapacity && lastRt.stage === 4) {
    const n = S.rts.length + 1; S.rts.push({ id: 'rt' + String(n).padStart(2, '0'), number: n, stage: 1, treeHealth: 100, pop: 0 });
    log.events.push({ type: 'new_rt', rt: 'rt' + String(n).padStart(2, '0') });
    left = S.population; for (const rt of S.rts) { rt.pop = Math.min(CFG.rtCapacity, left); left -= rt.pop; }
  }
  for (const r of named()) if (!r.rt) r.rt = S.rts.find(x => x.pop > 0 && named().filter(n => n.rt === x.id).length < x.pop)?.id || S.rts[0].id;
  for (const rt of S.rts) rt.stage = 1 + CFG.stages.findIndex(([a, b]) => rt.pop >= a && rt.pop <= b) || 1;

  // 3. tasks, energy, production
  const unnamed = S.population - named().length;
  let food = 0, wood = 0, D = 0, repairers = 0, ronda = 0;
  const need = S.population * 0.5, warned = prev.dragon.pendingAttack;
  for (const r of named()) {
    if (r.explicit !== S.day && r.id !== 'budi') r.task = warned ? 'RONDA' : (S.pools.food < need * 0.5 ? 'MASAK' : 'CARI'); // auto-assign (kerja bakti) unless chosen today
    if (r.energy < 30) r.task = 'TIDUR';
    const t = r.task;
    if (t === 'TIDUR') r.energy = clamp(r.energy + 40, 0, 100);
    else {
      r.energy = clamp(r.energy - CFG.energyCost[t], 0, 100);
      if (t === 'MASAK') food += 8; if (t === 'CARI') wood += 2; if (t === 'PERBAIKI') repairers++;
      if (t === 'RONDA') { D += 3; ronda++; } if (t === 'RAWAT') D += 1;
    }
  }
  food += unnamed * 0.5; wood += Math.floor(unnamed / 20); D += unnamed * 0.1;
  S.pools.food += food; S.pools.wood += wood;
  S.pools.food = Math.round((S.pools.food - S.population * 0.5) * 10) / 10;
  if (S.pools.food < 0) { S.pools.food = 0; for (const r of named()) r.energy = clamp(r.energy - 10, 0, 100); log.events.push({ type: 'paceklik' }); }

  // 4. houses (auto) + building queue
  for (const rt of S.rts) {
    if (!S.buildings.some(x => x.rt === rt.id && x.type === 'balai')) S.buildings.push({ id: 'b' + S.buildings.length, type: 'balai', rt: rt.id, status: 'done', damage: 0, by: null, comment: null, day: S.day });
    const homes = S.buildings.filter(x => x.rt === rt.id && x.type === 'rumah' && x.status === 'done').length;
    const inRt = named().filter(r => r.rt === rt.id).length;
    if (inRt > homes * CFG.houseCap || homes < Math.min(6, Math.ceil(rt.pop / 40))) { S.buildings.push({ id: 'b' + S.buildings.length, type: 'rumah', rt: rt.id, status: 'done', damage: 0, by: null, comment: null, day: S.day }); log.events.push({ type: 'auto_house', rt: rt.id }); }
  }
  requests.sort((a, b) => b.likes - a.likes || a.ts - b.ts);
  S.queue = S.queue.filter(q => { if (S.day - q.day > 3) { log.events.push({ type: 'request_expired', user: q.username, building: q.type }); return false; } return true; });
  for (const q of requests) S.queue.push({ ...q, wait: 0, day: S.day });
  const cap = Math.min(5, 1 + Math.floor(S.population / 50));
  let started = 0;
  for (const b of S.buildings.filter(x => x.status === 'building')) { b.left -= 1 + (wood > 0 ? 1 : 0) * 0; if (b.left <= 0) { b.status = 'done'; log.events.push({ type: 'built', building: b.type, by: b.byName }); } }
  for (const q of [...S.queue]) {
    if (started >= cap) break; if (S.pools.wood < CFG.cost[q.type]) continue;
    S.pools.wood -= CFG.cost[q.type]; started++; S.queue.splice(S.queue.indexOf(q), 1);
    S.buildings.push({ id: 'b' + S.buildings.length, type: q.type, rt: (S.residents[q.user] && S.residents[q.user].rt) || 'rt01', status: 'building', left: CFG.buildDays[q.type], damage: 0, by: q.user, byName: q.username, comment: q.text, day: S.day });
    log.events.push({ type: 'build_start', building: q.type, by: q.username });
    if (log.featured_comments.length < 4) log.featured_comments.push({ user: q.username, text: q.text, likes: q.likes, building: q.type });
  }
  // repairs
  let rep = repairers * 1;
  for (const b of S.buildings) while (b.damage > 0 && rep > 0 && S.pools.wood > 0) { b.damage--; rep--; S.pools.wood--; }

  // 5. dragon: resolve today's pending attack, then roll for tomorrow
  const dr = S.dragon; dr.warning = false;
  const done = S.buildings.filter(b => b.status === 'done');
  if (dr.pendingAttack) {
    const pop = S.population, Sp = 10 + 0.2 * pop, tower = done.filter(b => b.type === 'menara').length * 5, Dt = D + tower;
    dr.pendingAttack = false; dr.lastAttackDay = S.day;
    if (Dt >= Sp) log.events.push({ type: 'dragon', result: 'driven_off', S: +Sp.toFixed(1), D: Dt });
    else {
      const dmg = Math.min(6, Math.ceil((Sp - Dt) / 5)); let hit = 0;
      for (const b of done) { if (hit >= dmg) break; if (b.type !== 'balai' && b.damage < 2) { b.damage++; hit++; } }
      for (const rt of S.rts) rt.treeHealth = clamp(rt.treeHealth - 10, 0, 100);
      log.events.push({ type: 'dragon', result: 'damage', S: +Sp.toFixed(1), D: Dt, houses_damaged: hit });
    }
    log.deaths = 0;
  } else {
    for (const rt of S.rts) rt.treeHealth = clamp(rt.treeHealth + named().filter(r => r.task === 'RAWAT').length, 0, 100);
  }
  const p = Math.min(0.35, 0.14 + 0.01 * S.population / 100);
  if (S.day >= 4 && S.day - dr.lastAttackDay >= 2 && !dr.pendingAttack && rand() < p) { dr.pendingAttack = true; dr.warning = true; log.events.push({ type: 'dragon_warning' }); }
  log.stats = { population: S.population, named: named().length, food: S.pools.food, wood: S.pools.wood, buildings: S.buildings.filter(b => b.status === 'done').length, queue: S.queue.length };
  S.log = undefined; return { state: S, log };
}
module.exports = { step, newWorld, CFG, rng, hash };
