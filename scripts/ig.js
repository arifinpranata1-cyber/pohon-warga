// Pembaca Instagram (API with Instagram Login). Tanpa dependensi, Node 18+.
const BASE = 'https://graph.instagram.com/v21.0';

async function getJson(url, fetchFn) {
  const res = await fetchFn(url);
  const body = await res.json();
  if (!res.ok || body.error) {
    const e = body.error || {};
    throw new Error(`IG API ${res.status}: ${e.message || 'unknown'} (code ${e.code || '-'})`);
  }
  return body;
}

// Ambil followers_count + komentar baru dari beberapa post terakhir.
// seen: Set id komentar yang sudah diproses. Mengembalikan input untuk step() dan id baru.
async function fetchInput({ token, seen, maxPosts = 12, maxPages = 5, fetchFn = fetch }) {
  const q = (p, extra = '') => `${BASE}${p}${p.includes('?') ? '&' : '?'}access_token=${encodeURIComponent(token)}${extra}`;
  const me = await getJson(q('/me?fields=username,followers_count'), fetchFn);
  const media = await getJson(q(`/me/media?fields=id,timestamp&limit=${maxPosts}`), fetchFn);
  const fresh = [];
  for (const m of media.data || []) {
    let url = q(`/${m.id}/comments?fields=id,text,username,like_count,timestamp&limit=50`);
    for (let page = 0; url && page < maxPages; page++) {
      const r = await getJson(url, fetchFn);
      for (const c of r.data || []) {
        if (!c.id || seen.has(c.id) || !c.username || !c.text) continue;
        fresh.push({ id: c.id, user: c.username.toLowerCase(), text: c.text, likes: c.like_count || 0, ts: Date.parse(c.timestamp) || 0 });
      }
      url = r.paging && r.paging.next ? r.paging.next : null;
    }
  }
  fresh.sort((a, b) => a.ts - b.ts || (a.id < b.id ? -1 : 1)); // urutan stabil = hasil deterministik
  return { followers: me.followers_count || 0, comments: fresh, newIds: fresh.map(c => c.id), username: me.username };
}

module.exports = { fetchInput };
