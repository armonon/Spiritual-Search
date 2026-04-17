let currentPage = 1;
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
    sorted.sort((a, b) => (b.year || 0) - (a.year || 0));
  } else if (sortBy === 'oldest') {
    sorted.sort((a, b) => (a.year || 0) - (b.year || 0));
  } else if (sortBy === 'popularity') {
    // If results have a popularity/rating score, use it; otherwise by year (recent = popular)
    sorted.sort((a, b) => (b.rating || b.year || 0) - (a.rating || a.year || 0));
  }
  // 'relevance' keeps original order
  return sorted;
}

function applyLocalFilters() {
  let filtered = [...allResults];
  
  const fromYear = yearFrom.value ? parseInt(yearFrom.value) : null;
  const toYear = yearTo.value ? parseInt(yearTo.value) : null;
  
  if (fromYear || toYear) {
    filtered = filtered.filter(item => {
      const year = item.year || 0;
      if (fromYear && year < fromYear) return false;
      if (toYear && year > toYear) return false;
      return true;
    });
  }
  
  const sortBy = sortSelect.value;
  filtered = sortResults(filtered, sortBy);
  
  filteredResults = filtered;
  currentPage = 1;
  displayResults();
}

function displayResults() {
  resultsContainer.innerHTML = '';
  const startIdx = (currentPage - 1) * LIMIT;
  const endIdx = startIdx + LIMIT;
  const pageResults = filteredResults.slice(startIdx, endIdx);
  
  if (pageResults.length === 0 && currentPage === 1) {
    resultsContainer.innerHTML = '<p>No results found.</p>';
    loadMoreBtn.style.display = 'none';
    return;
  }
  
  pageResults.forEach(item => {
    const div = document.createElement('div');
    div.className = 'result';

    if (item.source) {
      const authors = Array.isArray(item.authors) ? item.authors : (item.authors ? [item.authors] : []);
      const authorStr = authors.join(', ') || 'Unknown Author';
      const searchQuery = encodeURIComponent(`${item.title} ${authorStr}`);
      const imgSrc = item.thumbnail && item.thumbnail.startsWith('http') ? item.thumbnail : 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22300%22%3E%3Crect fill=%22%23ddd%22 width=%22200%22 height=%22300%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22Arial%22 font-size=%2214%22 fill=%22%23666%22%3ENo Cover%3C/text%3E%3C/svg%3E';
      
      div.innerHTML = `
        <img src="${imgSrc}" alt="${item.title}" />
        <div class="info">
          <h3>${item.title}</h3>
          <p><strong>${authorStr}</strong></p>
          <p>${item.year || 'Year unknown'}</p>
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
  
  hasMore = endIdx < filteredResults.length;
  if (loadMoreBtn) {
    loadMoreBtn.style.display = hasMore ? 'block' : 'none';
  }
}

async function fetchResults(reset = false) {
  if (loading) return;
  loading = true;
  showLoading(true);

  if (reset) {
    allResults = [];
    currentPage = 1;
  }

  const offset = allResults.length;
  const exact = exactCheckbox && exactCheckbox.checked;
  const syn = synonymsCheckbox && synonymsCheckbox.checked;
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

  loading = false;
  
  if (reset) {
    applyLocalFilters();
  } else {
    displayResults();
  }
  
  showLoading(false);
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
  // load more results from server (not just paginate local slice)
  fetchResults(false);
});
window.addEventListener('scroll', () => {
  if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 500) {
    if (hasMore && !loading) {
      fetchResults(false);
    }
  }
});