const SCORE_NAMES = ["Zero", "One", "Two", "Three", "Four", "Five"];

const state = new Map();
const elements = {
  map: document.querySelector("#map"),
  statsList: document.querySelector("#stats-list"),
  total: document.querySelector("#total-count"),
  toastRegion: document.querySelector("#toast-region"),
  loading: document.querySelector("#loading-state"),
  connection: document.querySelector("#connection-label"),
  importInput: document.querySelector("#import-input"),
};

mapboxgl.accessToken = MAPBOX_TOKEN;
const map = new mapboxgl.Map({
  container: elements.map,
  style: "mapbox://styles/mapbox/dark-v11",
  center: [30.5234, 50.4501],
  zoom: 10.5,
  attributionControl: true,
});
map.addControl(new mapboxgl.NavigationControl(), "bottom-right");

function showToast(message, type = "error") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  elements.toastRegion.append(toast);
  window.setTimeout(() => toast.remove(), 3800);
}

async function request(url, options = {}) {
  const response = await fetch(url, { headers: { "Content-Type": "application/json", ...options.headers }, ...options });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { message = (await response.json()).detail || message; } catch (_) { /* keep fallback */ }
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function markerElement(score) {
  const element = document.createElement("div");
  element.className = `marker-pin score-${score}`;
  element.setAttribute("aria-label", `Score ${score} marker`);
  element.addEventListener("click", (event) => event.stopPropagation());
  return element;
}

function updateStats() {
  const counts = [0, 0, 0, 0, 0, 0];
  for (const { data } of state.values()) counts[data.score] += 1;
  elements.total.textContent = state.size;
  elements.statsList.innerHTML = counts.map((count, score) => `
    <div class="stat-row"><span class="legend-dot score-${score}"></span><span>${SCORE_NAMES[score]}</span><span class="stat-count">${count}</span></div>
  `).reverse().join("");
}

function updateMarkerVisual(entry) {
  entry.marker.getElement().className = `marker-pin score-${entry.data.score}`;
  entry.marker.getElement().setAttribute("aria-label", `Score ${entry.data.score} marker`);
}

function buildPopup(entry) {
  const form = document.createElement("div");
  form.className = "popup-form";
  form.innerHTML = `<p class="popup-title">Marker details</p><label class="popup-label" for="score-${entry.data.id}">SCORE</label>`;
  const select = document.createElement("select");
  select.id = `score-${entry.data.id}`;
  select.className = "popup-select";
  for (let score = 0; score <= 5; score += 1) {
    const option = new Option(`${score} · ${SCORE_NAMES[score]}`, score, false, score === entry.data.score);
    select.append(option);
  }
  select.addEventListener("change", async () => {
    const previous = entry.data.score;
    const score = Number(select.value);
    try {
      entry.data = await request(`/api/markers/${entry.data.id}`, { method: "PATCH", body: JSON.stringify({ score }) });
      updateMarkerVisual(entry); updateStats(); showToast("Marker score updated", "success");
    } catch (error) {
      select.value = previous; showToast(error.message);
    }
  });
  form.append(select);
  const deleteButton = document.createElement("button");
  deleteButton.className = "popup-delete";
  deleteButton.type = "button";
  deleteButton.textContent = "Remove marker";
  deleteButton.addEventListener("click", async () => {
    try {
      await request(`/api/markers/${entry.data.id}`, { method: "DELETE" });
      entry.marker.remove(); entry.popup.remove(); state.delete(entry.data.id); updateStats(); showToast("Marker removed", "success");
    } catch (error) { showToast(error.message); }
  });
  form.append(deleteButton);
  return form;
}

function addMarker(data) {
  const marker = new mapboxgl.Marker({ element: markerElement(data.score), draggable: true })
    .setLngLat([data.coordinates.lng, data.coordinates.lat]).addTo(map);
  const entry = { data, marker, popup: null };
  entry.popup = new mapboxgl.Popup({ offset: 22, closeButton: true, closeOnClick: false }).setDOMContent(buildPopup(entry));
  marker.setPopup(entry.popup);
  marker.on("dragend", async () => {
    const previous = { ...entry.data.coordinates };
    const position = marker.getLngLat();
    try {
      entry.data = await request(`/api/markers/${entry.data.id}`, { method: "PATCH", body: JSON.stringify({ coordinates: { lng: position.lng, lat: position.lat } }) });
      showToast("Marker position updated", "success");
    } catch (error) {
      marker.setLngLat([previous.lng, previous.lat]); showToast(error.message);
    }
  });
  state.set(data.id, entry); updateStats();
}

async function createMarker(lngLat, score = 0) {
  try { addMarker(await request("/api/markers", { method: "POST", body: JSON.stringify({ coordinates: { lng: lngLat.lng, lat: lngLat.lat }, score }) })); showToast("Marker placed", "success"); }
  catch (error) { showToast(`Could not place marker: ${error.message}`); }
}

async function loadMarkers() {
  try {
    const markers = await request("/api/markers");
    markers.forEach(addMarker); elements.connection.textContent = "Connected";
  } catch (error) {
    elements.connection.textContent = "Offline"; showToast(`Could not load markers: ${error.message}`);
  } finally { elements.loading.classList.add("hidden"); }
}

function exportMarkers() {
  const payload = { version: 1, exportedAt: new Date().toISOString(), markers: [...state.values()].map(({ data }) => data) };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob); const anchor = document.createElement("a");
  anchor.href = url; anchor.download = `pinboard-markers-${new Date().toISOString().slice(0, 10)}.json`; anchor.click(); URL.revokeObjectURL(url);
  showToast("Markers exported", "success");
}

async function importMarkers(file) {
  try {
    const payload = JSON.parse(await file.text());
    const markers = Array.isArray(payload) ? payload : payload.markers;
    if (!Array.isArray(markers)) throw new Error("JSON must contain a markers array");
    let added = 0;
    for (const marker of markers) {
      if (!marker?.coordinates || typeof marker.coordinates.lng !== "number" || typeof marker.coordinates.lat !== "number" || !Number.isInteger(marker.score) || marker.score < 0 || marker.score > 5) continue;
      try { addMarker(await request("/api/markers", { method: "POST", body: JSON.stringify({ coordinates: marker.coordinates, score: marker.score }) })); added += 1; } catch (_) { /* keep importing other records */ }
    }
    showToast(`Imported ${added} of ${markers.length} markers`, added === markers.length ? "success" : "error");
  } catch (error) { showToast(`Import failed: ${error.message}`); }
  elements.importInput.value = "";
}

map.on("click", (event) => createMarker(event.lngLat));
map.on("load", loadMarkers);
document.querySelector("#export-button").addEventListener("click", exportMarkers);
elements.importInput.addEventListener("change", (event) => { if (event.target.files[0]) importMarkers(event.target.files[0]); });
