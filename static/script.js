let query = '';
let loading = false;
let hasMore = true;
const LIMIT = 30;  // Increased for faster loading
let mode = 'library';
let allResults = [];
let filteredResults = [];

const resultsContainer = document.getElementById('results');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('search-btn');
const loadingEl = document.getElementById('loading');
const tabLibrary = document.getElementById('tab-library');
const tabOpenWeb = document.getElementById('tab-openweb');
const modeExplain = document.getElementById('mode-explain');
const sortSelect = document.getElementById('sort-select');
const yearFrom = document.getElementById('year-from');
const yearTo = document.getElementById('year-to');
const exactCheckbox = document.getElementById('exact-match');
const synonymsCheckbox = document.getElementById('include-synonyms');
const applyFiltersBtn = document.getElementById('apply-filters');
const loadMoreBtn = document.getElementById('load-more');
const PLACEHOLDER_THUMBNAIL = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22300%22%3E%3Crect fill=%22%23ddd%22 width=%22200%22 height=%22300%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22Arial%22 font-size=%2214%22 fill=%22%23666%22%3ENo Cover%3C/text%3E%3C/svg%3E';

function toHttps(url) {
  if (!url || typeof url !== 'string') return '';
  return url.startsWith('http://') ? `https://${url.slice(7)}` : url;
}

function extractYear(item) {
  const candidates = [item?.year, item?.date, item?.publishedDate, item?.raw?.date, item?.raw?.publishedDate];
  for (const candidate of candidates) {
    if (candidate === null || candidate === undefined) continue;
    const match = String(candidate).match(/\b(1[0-9]{3}|20[0-9]{2}|21[0-9]{2})\b/);
    if (match) return parseInt(match[1], 10);
  }
  return null;
}

function yearLabel(item) {
  return extractYear(item) || item?.year || item?.date || 'Year unknown';
}

function pickIsbn(item) {
  const isbnField = item?.isbn || item?.raw?.isbn || item?.raw?.volumeInfo?.industryIdentifiers;
  if (Array.isArray(isbnField)) {
    for (const entry of isbnField) {
      if (typeof entry === 'string' && entry.trim()) return entry.trim();
      if (entry?.identifier) return String(entry.identifier).trim();
    }
  }
  if (typeof isbnField === 'string' && isbnField.trim()) return isbnField.trim();
  return '';
}

function bestThumbnail(item) {
  const raw = item?.raw || {};
  const imageLinks = raw?.volumeInfo?.imageLinks || {};
  const coverId = raw?.cover_i || raw?.cover_id || item?.cover_i || item?.cover_id;
  const iaIdentifier = item?.id || raw?.identifier;
  const gutenCover = raw?.formats?.['image/jpeg'];

  const candidates = [
    item?.thumbnail,
    item?.cover_url,
    imageLinks?.thumbnail,
    imageLinks?.smallThumbnail,
    gutenCover,
    coverId ? `https://covers.openlibrary.org/b/id/${coverId}-M.jpg` : '',
    pickIsbn(item) ? `https://covers.openlibrary.org/b/isbn/${encodeURIComponent(pickIsbn(item))}-M.jpg` : '',
    iaIdentifier ? `https://archive.org/services/img/${encodeURIComponent(String(iaIdentifier))}` : '',
  ].map(toHttps).filter(Boolean);

  return candidates[0] || PLACEHOLDER_THUMBNAIL;
}

function showLoading(show) {
  if (!loadingEl) return;
  if (show) {
    loadingEl.classList.add('active');
  } else {
    loadingEl.classList.remove('active');
  }
}

function sortResults(results, sortBy) {
  const sorted = [...results];
  if (sortBy === 'newest') {
    sorted.sort((a, b) => (extractYear(b) || 0) - (extractYear(a) || 0));
  } else if (sortBy === 'oldest') {
    sorted.sort((a, b) => (extractYear(a) || 0) - (extractYear(b) || 0));
  } else if (sortBy === 'popularity') {
    // If results have a popularity/rating score, use it; otherwise by year (recent = popular)
    sorted.sort((a, b) => (b.rating || extractYear(b) || 0) - (a.rating || extractYear(a) || 0));
  }
  // 'relevance' keeps original order
  return sorted;
}

function applyLocalFilters() {
  let filtered = [...allResults];
  
  const fromYear = yearFrom.value ? parseInt(yearFrom.value) : null;
  const toYear = yearTo.value ? parseInt(yearTo.value) : null;
  const low = fromYear && toYear ? Math.min(fromYear, toYear) : fromYear;
  const high = fromYear && toYear ? Math.max(fromYear, toYear) : toYear;
  
  if (low || high) {
    filtered = filtered.filter(item => {
      const year = extractYear(item);
      if (year === null) return false;
      if (low && year < low) return false;
      if (high && year > high) return false;
      return true;
    });
  }
  
  const sortBy = sortSelect.value;
  filtered = sortResults(filtered, sortBy);
  
  filteredResults = filtered;
  displayResults();
}

function displayResults() {
  resultsContainer.innerHTML = '';

  if (filteredResults.length === 0) {
    resultsContainer.innerHTML = '<p>No results found.</p>';
    if (loadMoreBtn) loadMoreBtn.style.display = 'none';
    return;
  }

  filteredResults.forEach(item => {
    const div = document.createElement('div');
    div.className = 'result';

    if (item.source) {
      const authors = Array.isArray(item.authors) ? item.authors : (item.authors ? [item.authors] : []);
      const authorStr = authors.join(', ') || 'Unknown Author';
      const searchQuery = encodeURIComponent(`${item.title} ${authorStr}`);
      const imgSrc = bestThumbnail(item);
      
      div.innerHTML = `
        <img src="${imgSrc}" alt="${item.title}" onerror="this.onerror=null;this.src='${PLACEHOLDER_THUMBNAIL}'" />
        <div class="info">
          <h3>${item.title}</h3>
          <p><strong>${authorStr}</strong></p>
          <p>${yearLabel(item)}</p>
          <p><small><i>${item.source || ''}</i></small></p>
        </div>
        <div class="actions">
          <a href="https://openlibrary.org/search?q=${searchQuery}&mode=everything" target="_blank" rel="noopener noreferrer" class="btn btn-free">Free PDF</a>
        </div>
      `;
    } else {
      div.innerHTML = `
        <div class="info">
          <h3><a href="${item.url}" target="_blank" rel="nofollow noopener noreferrer">${item.title}</a></h3>
          <p class="meta">${item.source_type || ''} • ${item.date || ''}</p>
          <p class="excerpt">${item.excerpt || ''}</p>
        </div>
      `;
    }

    resultsContainer.appendChild(div);
  });

  if (loadMoreBtn) {
    loadMoreBtn.style.display = hasMore ? 'block' : 'none';
  }

  ensureContentFillsViewport();
}

function ensureContentFillsViewport() {
  if (!hasMore || loading) return;
  if (document.body.scrollHeight <= window.innerHeight + 120) {
    fetchResults(false);
  }
}

async function fetchResults(reset = false) {
  if (loading) return;
  loading = true;
  showLoading(true);

  if (reset) {
    allResults = [];
    filteredResults = [];
    hasMore = true;
  }

  const offset = allResults.length;
  const exact = exactCheckbox && exactCheckbox.checked;
  const syn = synonymsCheckbox && synonymsCheckbox.checked;
  try {
    const resp = await fetch(
      `/search?query=${encodeURIComponent(query)}` +
        `&mode=${encodeURIComponent(mode)}` +
        `&offset=${offset}&limit=${LIMIT}` +
        `&exact=${exact}&synonyms=${syn}`
    );
    const data = await resp.json();

    if (data.results && data.results.length > 0) {
      allResults = allResults.concat(data.results);
    }

    // Use backend pagination truth directly.
    if (typeof data.has_more === 'boolean') {
      hasMore = data.has_more;
    } else {
      hasMore = !!(data.results && data.results.length === LIMIT);
    }
  } catch (err) {
    console.error('Search request failed:', err);
    hasMore = false;
  } finally {
    loading = false;
    showLoading(false);
  }

  applyLocalFilters();
}

function setMode(m) {
  mode = m;
  if (mode === 'library') {
    tabLibrary.classList.add('active');
    tabOpenWeb.classList.remove('active');
    modeExplain.textContent = 'Library: search curated institutional and archival sources.';
  } else {
    tabOpenWeb.classList.add('active');
    tabLibrary.classList.remove('active');
    modeExplain.textContent = 'Open Web: surfaces curated, public pages from the open web (read-only).';
  }
}

if (tabLibrary) tabLibrary.addEventListener('click', () => setMode('library'));
if (tabOpenWeb) tabOpenWeb.addEventListener('click', () => setMode('open_web'));

if (searchBtn) {
  searchBtn.addEventListener('click', () => {
    query = searchInput.value.trim();
    if (!query) return;
    fetchResults(true);
  });
}

if (searchInput) {
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      query = searchInput.value.trim();
      if (!query) return;
      fetchResults(true);
    }
  });
}

if (sortSelect) sortSelect.addEventListener('change', () => applyLocalFilters());
if (applyFiltersBtn) applyFiltersBtn.addEventListener('click', () => {
  // when filters change, re-fetch from server with new flags
  allResults = [];
  fetchResults(true);
});
if (exactCheckbox) exactCheckbox.addEventListener('change', () => {
  // when exact/synonyms change, re-fetch from server
  allResults = [];
  fetchResults(true);
});
if (synonymsCheckbox) synonymsCheckbox.addEventListener('change', () => {
  // when exact/synonyms change, re-fetch from server
  allResults = [];
  fetchResults(true);
});
if (loadMoreBtn) loadMoreBtn.addEventListener('click', () => {
  // fallback manual pagination in addition to infinite scroll
  fetchResults(false);
});
window.addEventListener('scroll', () => {
  if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 500) {
    if (hasMore && !loading) {
      fetchResults(false);
    }
  }
});