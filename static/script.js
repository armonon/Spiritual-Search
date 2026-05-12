const SOURCE_MAP = [
  { name: 'Open Library', badge: 'core', role: 'Book backbone', note: 'Works, editions, authors, subjects, ISBNs, covers, and Internet Archive read/borrow links.' },
  { name: 'Internet Archive', badge: 'full text', role: 'Scans + availability', note: 'Digitized books, public-domain downloads, borrowable scans, OCR text, and thumbnails.' },
  { name: 'Library of Congress', badge: 'authority', role: 'Catalog authority', note: 'Library-grade metadata, subjects, collection context, dates, names, and provenance.' },
  { name: 'Google Books', badge: 'coverage', role: 'Enrichment layer', note: 'Broad discovery coverage, previews, covers, publisher metadata, and commercial availability signals.' },
  { name: 'Project Gutenberg', badge: 'public domain', role: 'Free classics', note: 'Public-domain ebooks, formats, languages, subjects, and download signals.' },
  { name: 'Wikidata', badge: 'graph', role: 'Knowledge graph', note: 'Work/author identity, alternate titles, series, awards, adaptations, and external IDs.' },
  { name: 'HathiTrust', badge: 'preservation', role: 'Rights signal', note: 'Preservation records, full-view/limited-view signals, and institutional bibliographic data.' },
  { name: 'WorldCat', badge: 'future', role: 'Library network', note: 'Stubbed for now; ideal future layer through official OCLC/API access.' },
];

const FEATURES = [
  ['Wisdom-first discovery', 'Built for spiritual, herbal, historical, and philosophical research — but broad enough for any serious book hunt.'],
  ['Federated search engine', 'The backend fans one query across open catalogs, archives, public-domain sources, and enrichment APIs.'],
  ['Research-grade organization', 'Cards show provenance, metadata completeness, subjects, identifiers, and availability instead of just a title list.'],
  ['Spiritual Search + Librarian', 'Armon’s original backend depth blended with the polished book-atlas experience from Librarian.'],
  ['Local research stack', 'Save books in your browser while you explore, then come back to a working shelf.'],
  ['Expansion-ready architecture', 'The next step is an indexed book graph: Open Library dumps + IA + Wikidata + LOC + public-domain full text.'],
];

const SAMPLE_QUERIES = ['fasting', 'sufism', 'tantra', 'persian poetry', 'herbal medicine', 'comparative mysticism'];
const PLACEHOLDER = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22280%22 height=%22420%22 viewBox=%220 0 280 420%22%3E%3Cdefs%3E%3ClinearGradient id=%22g%22 x1=%220%22 x2=%221%22 y1=%220%22 y2=%221%22%3E%3Cstop stop-color=%22%238c6cff%22/%3E%3Cstop offset=%22.55%22 stop-color=%22%23f4c95d%22/%3E%3Cstop offset=%221%22 stop-color=%22%23ff6b9d%22/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width=%22280%22 height=%22420%22 rx=%2218%22 fill=%22url(%23g)%22 opacity=%22.9%22/%3E%3Ccircle cx=%22196%22 cy=%2290%22 r=%2260%22 fill=%22%23fff%22 opacity=%22.18%22/%3E%3Ctext x=%2250%25%22 y=%2251%25%22 text-anchor=%22middle%22 font-family=%22Georgia%22 font-size=%2240%22 fill=%22%2308070c%22%3ESS%3C/text%3E%3C/svg%3E';

const app = document.querySelector('#app');
const storeKey = 'spiritual-search.stack.v1';
const state = {
  query: '',
  mode: 'library',
  loading: false,
  searched: false,
  offset: 0,
  limit: 30,
  hasMore: false,
  allResults: [],
  error: '',
  saved: loadSaved(),
  selected: null,
  filters: { source: 'all', availability: 'all', yearFrom: '', yearTo: '', sort: 'relevance', exact: false, synonyms: true },
};

function loadSaved() {
  try { return JSON.parse(localStorage.getItem(storeKey) || '[]'); } catch { return []; }
}
function persist() { localStorage.setItem(storeKey, JSON.stringify(state.saved)); }
function esc(value = '') { return String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
function uniq(values = []) { return [...new Set(values.flat(Infinity).filter(Boolean).map(String))]; }
function cleanUrl(url) { return typeof url === 'string' && url.startsWith('http://') ? `https://${url.slice(7)}` : (url || ''); }
function compact(text = '', max = 190) { text = Array.isArray(text) ? text.join(', ') : String(text || ''); return text.length > max ? `${text.slice(0, max).trim()}…` : text; }
function extractYear(item = {}) {
  const candidates = [item.year, item.date, item.publishedDate, item.raw?.date, item.raw?.publishedDate, item.raw?.volumeInfo?.publishedDate, item.raw?.first_publish_year];
  for (const value of candidates) {
    const match = String(value || '').match(/\b(1[0-9]{3}|20[0-9]{2}|21[0-9]{2})\b/);
    if (match) return Number(match[1]);
  }
  return null;
}
function pickIsbn(item = {}) {
  const candidates = [item.isbn, item.raw?.isbn, item.raw?.volumeInfo?.industryIdentifiers].flat().filter(Boolean);
  for (const candidate of candidates) {
    if (typeof candidate === 'string' && candidate.trim()) return candidate.trim();
    if (candidate?.identifier) return String(candidate.identifier).trim();
  }
  return '';
}
function bestCover(item = {}) {
  const raw = item.raw || {};
  const imageLinks = raw.volumeInfo?.imageLinks || {};
  const coverId = raw.cover_i || raw.cover_id || item.cover_i || item.cover_id;
  const iaId = item.id || raw.identifier;
  const isbn = pickIsbn(item);
  return [
    item.thumbnail,
    item.cover_url,
    imageLinks.thumbnail,
    imageLinks.smallThumbnail,
    raw.formats?.['image/jpeg'],
    coverId ? `https://covers.openlibrary.org/b/id/${coverId}-L.jpg` : '',
    isbn ? `https://covers.openlibrary.org/b/isbn/${encodeURIComponent(isbn)}-L.jpg` : '',
    iaId && !String(iaId).startsWith('/works/') ? `https://archive.org/services/img/${encodeURIComponent(String(iaId))}` : '',
  ].map(cleanUrl).find(Boolean) || PLACEHOLDER;
}
function sourceName(item = {}) { return item.source || item.source_type || item.provider || 'unknown'; }
function normalized(item = {}, index = 0) {
  const raw = item.raw || {};
  const vi = raw.volumeInfo || {};
  const authors = Array.isArray(item.authors) ? item.authors : (item.authors ? [item.authors] : vi.authors || raw.author_name || []);
  const subjects = uniq([item.subjects, vi.categories, raw.subject, raw.subjects, item.matched_keywords]).slice(0, 14);
  const description = item.description || item.summary || item.excerpt || vi.description || raw.description || raw.summary || raw.first_sentence?.value || subjects.join(', ');
  const source = sourceName(item);
  const year = extractYear(item);
  const ids = uniq([pickIsbn(item), item.id, raw.key, raw.identifier]).slice(0, 8);
  const links = buildLinks(item, source);
  const book = {
    rawItem: item,
    id: `${source}:${item.id || item.title || index}`,
    title: item.title || vi.title || 'Untitled record',
    authors: uniq(authors).slice(0, 5),
    year,
    subjects,
    source,
    sources: uniq([source]),
    cover: bestCover(item),
    desc: compact(description || `${source} record`, 360),
    availability: inferAvailability(item, source),
    ids,
    links,
  };
  book.score = metadataScore(book);
  return book;
}
function buildLinks(item = {}, source = '') {
  const raw = item.raw || {};
  const vi = raw.volumeInfo || {};
  const isbn = pickIsbn(item);
  const titleAuthor = encodeURIComponent(`${item.title || vi.title || ''} ${(item.authors || vi.authors || []).join?.(' ') || ''}`.trim());
  const links = [];
  if (item.url) links.push({ label: 'Open result', url: item.url });
  if (vi.previewLink) links.push({ label: 'Google preview', url: vi.previewLink });
  if (vi.infoLink) links.push({ label: 'Google Books', url: vi.infoLink });
  if (raw.key || String(item.id || '').startsWith('/works/')) links.push({ label: 'Open Library', url: `https://openlibrary.org${raw.key || item.id}` });
  if (raw.identifier || (item.id && source.toLowerCase().includes('internet'))) links.push({ label: 'Internet Archive', url: `https://archive.org/details/${raw.identifier || item.id}` });
  if (raw.formats?.['text/html']) links.push({ label: 'Read HTML', url: raw.formats['text/html'] });
  if (raw.formats?.['application/epub+zip']) links.push({ label: 'Download EPUB', url: raw.formats['application/epub+zip'] });
  if (isbn) links.push({ label: 'ISBN lookup', url: `https://openlibrary.org/isbn/${encodeURIComponent(isbn)}` });
  if (titleAuthor) links.push({ label: 'Find free/readable copies', url: `https://openlibrary.org/search?q=${titleAuthor}&mode=everything` });
  return links.filter((l, i, all) => l.url && all.findIndex(x => x.url === l.url) === i).map(l => ({ ...l, url: cleanUrl(l.url) }));
}
function inferAvailability(item = {}, source = '') {
  const text = `${item.availability || ''} ${item.description || ''} ${item.summary || ''} ${item.excerpt || ''} ${source}`.toLowerCase();
  if (/gutenberg|public domain|epub|full view|free/.test(text)) return 'Free / public-domain likely';
  if (/internet|archive|borrow|readable/.test(text)) return 'Readable / borrowable';
  if (/google|preview/.test(text)) return 'Preview / enrichment';
  if (/open_web|archive/.test(text)) return 'Open web result';
  return 'Catalog record';
}
function metadataScore(book) {
  return Math.round(([book.title, book.authors?.length, book.cover && book.cover !== PLACEHOLDER, book.year, book.subjects?.length, book.ids?.length, book.desc, book.links?.length, !/catalog record/i.test(book.availability)].filter(Boolean).length / 9) * 100);
}
function key(book) {
  const isbn = (book.ids || []).find(id => /^97[89]/.test(String(id).replace(/[^0-9X]/gi, '')));
  return isbn ? `isbn:${isbn.replace(/[^0-9X]/gi, '').toUpperCase()}` : `${book.title}|${book.authors?.[0] || ''}`.toLowerCase().replace(/[^a-z0-9]+/g, '-');
}
function mergeBooks(items) {
  const map = new Map();
  items.forEach((item, index) => {
    const b = normalized(item, index);
    const k = key(b);
    const old = map.get(k);
    if (!old) { map.set(k, b); return; }
    const next = {
      ...old,
      cover: old.cover !== PLACEHOLDER ? old.cover : b.cover,
      desc: old.desc.length >= b.desc.length ? old.desc : b.desc,
      availability: /free|read|borrow/i.test(old.availability) ? old.availability : b.availability,
      authors: uniq([old.authors, b.authors]),
      subjects: uniq([old.subjects, b.subjects]).slice(0, 18),
      ids: uniq([old.ids, b.ids]).slice(0, 12),
      links: [...old.links, ...b.links].filter((l, i, all) => l.url && all.findIndex(x => x.url === l.url) === i),
      sources: uniq([old.sources, b.sources]),
    };
    next.source = next.sources.join(' + ');
    next.score = metadataScore(next);
    map.set(k, next);
  });
  return [...map.values()];
}
async function fetchJson(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 9000);
  try {
    const resp = await fetch(url, { signal: controller.signal });
    if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
    return await resp.json();
  } finally {
    clearTimeout(timeout);
  }
}
async function directOpenLibrary(q) {
  const data = await fetchJson(`https://openlibrary.org/search.json?q=${encodeURIComponent(q)}&limit=24&fields=key,title,author_name,first_publish_year,isbn,language,subject,cover_i,ia,ebook_access,ratings_average,edition_count`);
  return (data.docs || []).map(d => ({
    id: d.key,
    title: d.title,
    authors: d.author_name || [],
    year: d.first_publish_year,
    subjects: d.subject || [],
    isbn: d.isbn || [],
    source: 'Open Library',
    thumbnail: d.cover_i ? `https://covers.openlibrary.org/b/id/${d.cover_i}-L.jpg` : '',
    description: `${d.edition_count || 1} edition${d.edition_count === 1 ? '' : 's'} indexed by Open Library${d.ebook_access ? ` • ${d.ebook_access}` : ''}${d.ratings_average ? ` • rating ${Number(d.ratings_average).toFixed(1)}` : ''}`,
    raw: d,
  }));
}
async function directGoogleBooks(q) {
  const data = await fetchJson(`https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(q)}&maxResults=24&printType=books&projection=lite`);
  return (data.items || []).map(item => {
    const v = item.volumeInfo || {};
    return {
      id: item.id,
      title: v.title,
      authors: v.authors || [],
      year: extractYear({ publishedDate: v.publishedDate }),
      subjects: v.categories || [],
      isbn: (v.industryIdentifiers || []).map(x => x.identifier),
      source: 'Google Books',
      thumbnail: cleanUrl(v.imageLinks?.thumbnail || v.imageLinks?.smallThumbnail || ''),
      description: v.description || `${v.publisher || 'Publisher metadata'}${v.pageCount ? ` • ${v.pageCount} pages` : ''}`,
      raw: item,
    };
  });
}
async function directGutendex(q) {
  const data = await fetchJson(`https://gutendex.com/books?search=${encodeURIComponent(q.replace(/^isbn:/i, '').trim())}`);
  return (data.results || []).slice(0, 24).map(b => ({
    id: `gutenberg-${b.id}`,
    title: b.title,
    authors: (b.authors || []).map(a => a.name),
    year: b.authors?.[0]?.birth_year || '',
    subjects: uniq([b.subjects || [], b.bookshelves || []]),
    source: 'Project Gutenberg',
    thumbnail: b.formats?.['image/jpeg'] || '',
    description: `Public-domain ebook from Project Gutenberg • ${(b.download_count || 0).toLocaleString()} downloads.`,
    raw: { ...b, identifier: b.id },
  }));
}
async function directInternetArchive(q) {
  const fields = 'identifier,title,creator,year,subject,description';
  const url = `https://archive.org/advancedsearch.php?q=${encodeURIComponent(`title:(${q}) OR subject:(${q})`)}&fl[]=${fields.split(',').join('&fl[]=')}&rows=16&page=1&output=json`;
  const data = await fetchJson(url);
  return (data.response?.docs || []).map(d => ({
    id: d.identifier,
    title: d.title,
    authors: Array.isArray(d.creator) ? d.creator : (d.creator ? [d.creator] : []),
    year: d.year,
    subjects: Array.isArray(d.subject) ? d.subject : (d.subject ? [d.subject] : []),
    source: 'Internet Archive',
    thumbnail: `https://archive.org/services/img/${encodeURIComponent(d.identifier)}`,
    description: Array.isArray(d.description) ? d.description[0] : d.description,
    raw: d,
  }));
}
async function directStaticSearch(q) {
  const searches = state.mode === 'open_web'
    ? [directOpenLibrary(q), directInternetArchive(q), directGutendex(q)]
    : [directOpenLibrary(q), directGoogleBooks(q), directGutendex(q), directInternetArchive(q)];
  const settled = await Promise.allSettled(searches);
  return settled.flatMap(r => r.status === 'fulfilled' ? r.value : []);
}
async function fetchPage(reset = false) {
  if (state.loading || (!reset && !state.hasMore)) return;
  if (reset) Object.assign(state, { offset: 0, allResults: [], hasMore: true, error: '', searched: true });
  state.loading = true;
  render();
  const params = new URLSearchParams({
    query: state.query,
    mode: state.mode,
    offset: String(state.offset),
    limit: String(state.limit),
    exact: String(state.filters.exact),
    synonyms: String(state.filters.synonyms),
  });
  try {
    const resp = await fetch(`/search?${params.toString()}`);
    if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
    const data = await resp.json();
    state.allResults = reset ? (data.results || []) : state.allResults.concat(data.results || []);
    state.offset = state.allResults.length;
    state.hasMore = Boolean(data.has_more);
    state.error = state.allResults.length ? '' : 'No useful records came back. Try a broader phrase, title, author, or adjacent topic.';
  } catch (err) {
    const direct = await directStaticSearch(state.query);
    state.allResults = reset ? direct : state.allResults.concat(direct);
    state.offset = state.allResults.length;
    state.hasMore = false;
    state.error = state.allResults.length
      ? 'Using Netlify static search fallback while the Python backend is unavailable.'
      : `Search failed: ${err.message || err}`;
  } finally {
    state.loading = false;
    render();
    if (reset) document.querySelector('#results')?.scrollIntoView({ block: 'start' });
  }
}
function books() {
  let out = mergeBooks(state.allResults);
  if (state.filters.source !== 'all') out = out.filter(b => b.sources.includes(state.filters.source));
  if (state.filters.availability === 'free') out = out.filter(b => /free|public|read|borrow/i.test(b.availability));
  if (state.filters.availability === 'catalog') out = out.filter(b => /catalog|preview|enrichment|open web/i.test(b.availability));
  const from = Number(state.filters.yearFrom || 0);
  const to = Number(state.filters.yearTo || 0);
  if (from) out = out.filter(b => b.year && b.year >= from);
  if (to) out = out.filter(b => b.year && b.year <= to);
  if (state.filters.sort === 'newest') out.sort((a, b) => (b.year || 0) - (a.year || 0));
  else if (state.filters.sort === 'oldest') out.sort((a, b) => (a.year || 9999) - (b.year || 9999));
  else if (state.filters.sort === 'complete') out.sort((a, b) => b.score - a.score);
  else out.sort((a, b) => b.score - a.score || (b.year || 0) - (a.year || 0));
  return out;
}
function sourceOptions() { return uniq(mergeBooks(state.allResults).flatMap(b => b.sources)).sort(); }
function save(id) { const b = books().find(x => x.id === id); if (b && !state.saved.some(x => key(x) === key(b))) { state.saved.unshift(b); state.saved = state.saved.slice(0, 50); persist(); render(); } }
function removeSaved(id) { state.saved = state.saved.filter(b => b.id !== id); persist(); render(); }
function setMode(mode) { state.mode = mode; if (state.query) fetchPage(true); else render(); }

function hero() {
  return `<section class="hero"><div><p class="eyebrow">Spiritual Search × Librarian</p><h1>A beautiful research engine for books, wisdom, and open knowledge.</h1><p class="lede">Search spiritual traditions, herbal texts, philosophy, classics, archives, and academic catalogs from one place. Built from Armon’s original federated backend plus Joey’s book-atlas organization layer.</p><form class="search" data-search><input name="q" value="${esc(state.query)}" placeholder="Search fasting, Sufism, tantra, herbal medicine, ISBN…" /><button>${state.loading ? 'Searching…' : 'Search'}</button></form><div class="samples">${SAMPLE_QUERIES.map(q => `<button data-query="${esc(q)}">${esc(q)}</button>`).join('')}</div></div><aside class="heroPanel"><div class="orb"></div><div class="stat"><b>${SOURCE_MAP.length}</b><span>source layers mapped</span></div><div class="stat"><b>${state.allResults.length || '∞'}</b><span>${state.allResults.length ? 'raw records loaded' : 'federated discovery'}</span></div><div class="stat"><b>${state.saved.length}</b><span>saved in your local stack</span></div><p>Designed to become a spiritual + scholarly book graph: source provenance, availability, editions, identifiers, and eventually semantic exploration.</p></aside></section>`;
}
function controls() {
  return `<section class="toolbar"><div class="tabs"><button class="${state.mode === 'library' ? 'active' : ''}" data-mode="library">Library atlas</button><button class="${state.mode === 'open_web' ? 'active' : ''}" data-mode="open_web">Open web</button></div><p>${state.mode === 'library' ? 'Library atlas searches curated institutional, archival, and bibliographic sources.' : 'Open web surfaces curated public pages and archive-like resources when the book catalogs are not enough.'}</p><div class="advanced"><label><input type="checkbox" data-check="exact" ${state.filters.exact ? 'checked' : ''}> exact match</label><label><input type="checkbox" data-check="synonyms" ${state.filters.synonyms ? 'checked' : ''}> include synonyms</label></div></section>`;
}
function features() {
  return `<section class="section"><div class="heading"><p class="eyebrow">The blend</p><h2>Spiritual Search now feels like a real product, not a raw prototype.</h2></div><div class="grid features">${FEATURES.map(([h, p]) => `<article><i></i><h3>${esc(h)}</h3><p>${esc(p)}</p></article>`).join('')}</div></section>`;
}
function resultsSection() {
  if (!state.searched) return '';
  const out = books();
  return `<section class="section" id="results"><div class="heading row"><div><p class="eyebrow">Live results</p><h2>${state.loading ? 'Asking the libraries…' : `${out.length} organized result${out.length === 1 ? '' : 's'}`}</h2></div><div class="filters"><select data-filter="source"><option value="all">All sources</option>${sourceOptions().map(s => `<option value="${esc(s)}" ${state.filters.source === s ? 'selected' : ''}>${esc(s)}</option>`).join('')}</select><select data-filter="availability"><option value="all">All availability</option><option value="free" ${state.filters.availability === 'free' ? 'selected' : ''}>Readable/free</option><option value="catalog" ${state.filters.availability === 'catalog' ? 'selected' : ''}>Preview/catalog/web</option></select><select data-filter="sort"><option value="relevance" ${state.filters.sort === 'relevance' ? 'selected' : ''}>Best metadata</option><option value="newest" ${state.filters.sort === 'newest' ? 'selected' : ''}>Newest</option><option value="oldest" ${state.filters.sort === 'oldest' ? 'selected' : ''}>Oldest</option><option value="complete" ${state.filters.sort === 'complete' ? 'selected' : ''}>Most complete</option></select><input data-year="from" type="number" placeholder="From" value="${esc(state.filters.yearFrom)}"><input data-year="to" type="number" placeholder="To" value="${esc(state.filters.yearTo)}"></div></div>${state.error ? `<p class="notice">${esc(state.error)}</p>` : ''}${state.loading && !out.length ? `<div class="grid books">${Array.from({ length: 6 }, () => '<article class="book skeleton"></article>').join('')}</div>` : `<div class="grid books">${out.map(bookCard).join('') || '<p class="notice">No matches after filters. Widen the lens.</p>'}</div>`}<div class="loadRow">${state.hasMore ? `<button data-load-more>${state.loading ? 'Loading…' : 'Load more records'}</button>` : state.allResults.length ? '<span>End of current source results.</span>' : ''}</div></section>`;
}
function bookCard(b) {
  const saved = state.saved.some(x => key(x) === key(b));
  return `<article class="book"><div class="cover"><img src="${esc(b.cover)}" alt="Cover for ${esc(b.title)}" loading="lazy" onerror="this.onerror=null;this.src='${PLACEHOLDER}'"></div><div class="body"><div class="meta"><span>${esc(b.availability)}</span><span>${b.score}% complete</span></div><h3>${esc(b.title)}</h3><p class="by">${esc(b.authors.join(', ') || 'Unknown author')}${b.year ? ` • ${b.year}` : ''}</p><p>${esc(compact(b.desc, 155))}</p><div class="chips">${b.sources.map(s => `<span>${esc(s)}</span>`).join('')}${b.subjects.slice(0, 3).map(s => `<span>${esc(s)}</span>`).join('')}</div><div class="actions"><button data-select="${esc(b.id)}">Details</button><button data-save="${esc(b.id)}" ${saved ? 'disabled' : ''}>${saved ? 'Saved' : 'Save stack'}</button>${b.links[0] ? `<a href="${esc(b.links[0].url)}" target="_blank" rel="noreferrer">Open source</a>` : ''}</div></div></article>`;
}
function stack() {
  return `<section class="section"><div class="heading row"><div><p class="eyebrow">Your research stack</p><h2>Keep the gems while you explore.</h2></div><p>${state.saved.length ? `${state.saved.length} saved locally in this browser` : 'Search, inspect, and save books into a working shelf.'}</p></div><div class="saved">${state.saved.map(b => `<article><strong>${esc(b.title)}</strong><span>${esc(b.authors?.[0] || 'Unknown')}${b.year ? ` • ${b.year}` : ''}</span><button data-remove="${esc(b.id)}">Remove</button></article>`).join('') || '<p class="notice">No saved books yet.</p>'}</div></section>`;
}
function sourceMap() {
  return `<section class="section"><div class="heading"><p class="eyebrow">Source map</p><h2>The source strategy behind the superb version.</h2><p>Production path: cache politely, dedupe by ISBN/OCLC/LCCN/OpenLibrary/Wikidata IDs, rank by provenance and availability, then add semantic exploration over public-domain text.</p></div><div class="grid sources">${SOURCE_MAP.map(s => `<article><div class="top"><span>${esc(s.badge)}</span><b>${esc(s.role)}</b></div><h3>${esc(s.name)}</h3><p>${esc(s.note)}</p></article>`).join('')}</div></section>`;
}
function blueprint() {
  return `<section class="section blueprint"><div><p class="eyebrow">Next build</p><h2>How it becomes genuinely unmatched.</h2></div><div class="steps"><article><b>1. Ingest</b><p>Hydrate Open Library dumps, Gutenberg, IA metadata, Wikidata IDs, and LOC enrichment into a persistent backend.</p></article><article><b>2. Resolve</b><p>Cluster works/editions by ISBN, LCCN, OCLC, OLID, DOI, title-author fingerprints, and Wikidata QIDs.</p></article><article><b>3. Explore</b><p>Add author maps, tradition/topic paths, reading orders, public-domain finder, herbal/spiritual collections, and semantic search.</p></article><article><b>4. Preserve provenance</b><p>Every claim keeps source, timestamp, confidence, rights/availability, and a link back to the original record.</p></article></div></section>`;
}
function modal() {
  const b = state.selected;
  if (!b) return '';
  return `<div class="backdrop" data-close><article class="modal"><button class="x" data-close>×</button><div class="modalGrid"><div class="cover big"><img src="${esc(b.cover)}" alt="Cover for ${esc(b.title)}" onerror="this.onerror=null;this.src='${PLACEHOLDER}'"></div><div><p class="eyebrow">${esc(b.sources.join(' + '))}</p><h2>${esc(b.title)}</h2><p class="by">${esc(b.authors.join(', ') || 'Unknown author')}${b.year ? ` • ${b.year}` : ''}</p><p>${esc(b.desc)}</p><dl><dt>Availability</dt><dd>${esc(b.availability)}</dd><dt>Identifiers</dt><dd>${esc(b.ids.join(', ') || 'None surfaced')}</dd><dt>Subjects</dt><dd>${esc(b.subjects.slice(0, 12).join(', ') || 'None surfaced')}</dd><dt>Metadata score</dt><dd>${b.score}% complete</dd></dl><div class="actions links">${b.links.map(l => `<a href="${esc(l.url)}" target="_blank" rel="noreferrer">${esc(l.label)}</a>`).join('')}</div></div></div></article></div>`;
}
function render() {
  app.innerHTML = `<main>${hero()}${controls()}${features()}${resultsSection()}${stack()}${sourceMap()}${blueprint()}</main>${modal()}`;
  bind();
}
function bind() {
  document.querySelector('[data-search]')?.addEventListener('submit', event => {
    event.preventDefault();
    state.query = new FormData(event.currentTarget).get('q').trim();
    if (state.query) fetchPage(true);
  });
  document.querySelectorAll('[data-query]').forEach(el => el.onclick = () => { state.query = el.dataset.query; fetchPage(true); });
  document.querySelectorAll('[data-mode]').forEach(el => el.onclick = () => setMode(el.dataset.mode));
  document.querySelectorAll('[data-filter]').forEach(el => el.onchange = () => { state.filters[el.dataset.filter] = el.value; render(); });
  document.querySelectorAll('[data-year]').forEach(el => el.oninput = () => { state.filters[el.dataset.year === 'from' ? 'yearFrom' : 'yearTo'] = el.value; render(); });
  document.querySelectorAll('[data-check]').forEach(el => el.onchange = () => { state.filters[el.dataset.check] = el.checked; if (state.query) fetchPage(true); else render(); });
  document.querySelectorAll('[data-save]').forEach(el => el.onclick = () => save(el.dataset.save));
  document.querySelectorAll('[data-remove]').forEach(el => el.onclick = () => removeSaved(el.dataset.remove));
  document.querySelectorAll('[data-select]').forEach(el => el.onclick = () => { state.selected = books().find(b => b.id === el.dataset.select); render(); });
  document.querySelector('[data-load-more]')?.addEventListener('click', () => fetchPage(false));
  document.querySelectorAll('[data-close]').forEach(el => el.onclick = event => { if (event.target.closest('.modal') && !event.target.matches('.x')) return; state.selected = null; render(); });
}
render();
