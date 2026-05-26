const statusEl = document.getElementById('status');
const digitsEl = document.getElementById('digits');
const resultEl = document.getElementById('result');
const startBtn = document.getElementById('startBtn');
const nextBtn = document.getElementById('nextBtn');

const map = L.map('map').setView([36.5, 138.5], 5);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors',
}).addTo(map);

let allRows = [];
let candidates = [];
let step = 0;
let chosenSuffix = '';
const markers = L.layerGroup().addTo(map);

function pickDigitFromCandidates(rows, currentSuffix) {
  const counts = new Array(10).fill(0);
  for (const r of rows) {
    const idx = r.zip7.length - currentSuffix.length - 1;
    if (idx >= 0) counts[Number(r.zip7[idx])] += 1;
  }
  const available = counts.map((c, d) => ({ d, c })).filter(x => x.c > 0);
  if (!available.length) return Math.floor(Math.random() * 10).toString();
  const pick = available[Math.floor(Math.random() * available.length)].d;
  return String(pick);
}

function renderMarkers(rows) {
  markers.clearLayers();
  const limit = Math.min(rows.length, 2000);
  for (let i = 0; i < limit; i++) {
    const r = rows[i];
    L.circleMarker([r.lat, r.lon], { radius: 4, opacity: 0.8 }).addTo(markers);
  }
}

function renderState() {
  digitsEl.textContent = `確定済み(下位から): ${chosenSuffix.padStart(7, '・')}`;
  statusEl.textContent = `step ${step}/7 | 残り ${candidates.length} 件`;
}

function showFinalResult() {
  nextBtn.disabled = true;
  if (candidates.length > 0) {
    const r = candidates[Math.floor(Math.random() * candidates.length)];
    resultEl.textContent = `結果: 〒${r.zip7} ${r.pref}${r.city}${r.town}`;
    map.setView([r.lat, r.lon], 11);
  } else {
    resultEl.textContent = '候補が0件になりました。再抽選してください。';
  }
}

function advance() {
  if (step >= 7 || !candidates.length) {
    showFinalResult();
    return;
  }

  step += 1;
  const digit = pickDigitFromCandidates(candidates, chosenSuffix);
  chosenSuffix = digit + chosenSuffix;
  candidates = candidates.filter(r => r.zip7.endsWith(chosenSuffix));

  renderMarkers(candidates);
  renderState();

  if (step === 7 || candidates.length <= 1) showFinalResult();
}

async function loadData() {
  const urls = ['../data/zip_geo.json', '../data/sample_zip_geo.json'];
  for (const url of urls) {
    try {
      const res = await fetch(url);
      if (!res.ok) continue;
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return data.filter(r => /^\d{7}$/.test(r.zip7) && Number.isFinite(Number(r.lat)) && Number.isFinite(Number(r.lon)));
      }
    } catch (_e) {
      // noop
    }
  }
  return [];
}

startBtn.addEventListener('click', () => {
  step = 0;
  chosenSuffix = '';
  candidates = [...allRows];
  resultEl.textContent = '';
  nextBtn.disabled = false;
  renderMarkers(candidates);
  renderState();
});

nextBtn.addEventListener('click', advance);

(async () => {
  allRows = await loadData();
  if (!allRows.length) {
    statusEl.textContent = 'データが見つかりません。data/sample_zip_geo.json を確認してください。';
    startBtn.disabled = true;
    nextBtn.disabled = true;
    return;
  }
  statusEl.textContent = `${allRows.length} 件を読み込みました。抽選スタートしてください。`;
  candidates = [...allRows];
  renderMarkers(candidates);
})();
