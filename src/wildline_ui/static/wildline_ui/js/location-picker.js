// Maps for the location picker and Location card (wildline-ui#3). Load after Leaflet.
//   [data-wl-map]         a fixed map: the value's pin and the points' dots
//   [data-wl-map-picker]  inside [data-wl-location-picker]: click (or drag the pin) to set the
//                         picker's hidden latitude/longitude/accuracy inputs; a dot sets them
//                         to that point, with its accuracy
// Each map reads data-wl-map-options, -value ({latitude, longitude, accuracy_m} or null) and
// -points ([{latitude, longitude, accuracy_m, label}, ...]). Runs on page load and whenever
// htmx swaps in new content. A picker fires "wl:location-change" with the new value (or null).
(function () {
  // The marker images sit beside Leaflet; find them from this script's own URL so a hashed
  // static file name doesn't break Leaflet's own guess.
  const src = document.currentScript && document.currentScript.src;
  if (src) L.Icon.Default.imagePath = new URL("../vendor/leaflet/images/", src).href;

  function read(el, name) {
    try { return JSON.parse(el.dataset[name] || "null"); } catch (error) { return null; }
  }

  function latLng(value) { return L.latLng(value.latitude, value.longitude); }

  function setUp(el, interactive) {
    const options = read(el, "wlMapOptions") || {};
    const map = L.map(el, interactive ? {} : {
      zoomControl: false, dragging: false, scrollWheelZoom: false, doubleClickZoom: false,
      boxZoom: false, keyboard: false, touchZoom: false,
    });
    L.tileLayer(options.tile_url || "https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: options.max_zoom || 19,
      referrerPolicy: options.referrer_policy || "strict-origin-when-cross-origin",
      attribution: options.attribution || "",
    }).addTo(map);
    // Maps often start hidden (a collapsed box, a tab); size them once they show.
    if (window.ResizeObserver) new ResizeObserver(function () { map.invalidateSize(); }).observe(el);
    return { map: map, options: options };
  }

  function dots(map, points, onChoose) {
    const color = getComputedStyle(map.getContainer()).getPropertyValue("--bs-primary").trim() || "#0d6efd";
    return (points || []).map(function (point) {
      const at = latLng(point);
      const layers = [];
      if (point.accuracy_m) {
        layers.push(L.circle(at, { radius: point.accuracy_m, color: color, weight: 1, fillOpacity: 0.08, interactive: false }));
      }
      const dot = L.circleMarker(at, { radius: 7, color: "#fff", weight: 2, fillColor: color, fillOpacity: 0.9 });
      if (point.label) dot.bindTooltip(onChoose ? "Use " + point.label : point.label);
      if (onChoose) dot.on("click", function (event) { L.DomEvent.stop(event); onChoose(point); });
      layers.push(dot);
      return L.featureGroup(layers).addTo(map);
    });
  }

  function fit(map, options, value, layers) {
    if (value) map.setView(latLng(value), options.pin_zoom || 15);
    else if (layers.length) map.fitBounds(L.featureGroup(layers).getBounds(), { padding: [30, 30], maxZoom: options.pin_zoom || 15 });
    else map.setView(options.center || [39.5, -98.35], options.zoom || 4);
  }

  function pin(map, value, draggable) {
    const at = latLng(value);
    const marker = L.marker(at, { draggable: !!draggable, keyboard: !!draggable, title: "The location's pin" }).addTo(map);
    const circle = L.circle(at, { radius: value.accuracy_m || 0, weight: 1, fillOpacity: 0.1, interactive: false });
    if (value.accuracy_m) circle.addTo(map);
    return { marker: marker, circle: circle };
  }

  function showMap(el) {
    const setup = setUp(el, false);
    const value = read(el, "wlMapValue");
    if (value) pin(setup.map, value, false);
    fit(setup.map, setup.options, value, dots(setup.map, read(el, "wlMapPoints")));
  }

  function pickerMap(el) {
    const box = el.closest("[data-wl-location-picker]");
    const inputs = {};
    ["latitude", "longitude", "accuracy_m"].forEach(function (key) {
      inputs[key] = box.querySelector('[data-wl-input="' + key + '"]');
    });
    const status = box.querySelector("[data-wl-location-status]");
    const setup = setUp(el, true);
    const map = setup.map;
    let shown = null;

    function draw(value) {
      if (shown) { map.removeLayer(shown.marker); map.removeLayer(shown.circle); shown = null; }
      if (!value) return;
      shown = pin(map, value, true);
      shown.marker.on("dragend", function () {
        const at = shown.marker.getLatLng();
        set({ latitude: at.lat, longitude: at.lng, accuracy_m: null });
      });
    }

    function set(value) {
      inputs.latitude.value = value ? value.latitude.toFixed(6) : "";
      inputs.longitude.value = value ? value.longitude.toFixed(6) : "";
      inputs.accuracy_m.value = value && value.accuracy_m != null ? Math.round(value.accuracy_m) : "";
      draw(value);
      if (status) status.textContent = value ? "Pin placed." : "Pin removed.";
      Object.values(inputs).forEach(function (input) { input.dispatchEvent(new Event("change", { bubbles: true })); });
      box.dispatchEvent(new CustomEvent("wl:location-change", { bubbles: true, detail: value }));
    }

    const value = inputs.latitude.value && inputs.longitude.value ? {
      latitude: parseFloat(inputs.latitude.value),
      longitude: parseFloat(inputs.longitude.value),
      accuracy_m: inputs.accuracy_m.value ? parseFloat(inputs.accuracy_m.value) : null,
    } : null;
    draw(value);
    // A dot sets the pin to that point, with its accuracy; a click is a guess, without one.
    fit(map, setup.options, value, dots(map, read(el, "wlMapPoints"), function (point) {
      set(point);
      if (status && point.label) status.textContent = "Pin placed at " + point.label + ".";
    }));
    map.on("click", function (event) { set({ latitude: event.latlng.lat, longitude: event.latlng.lng, accuracy_m: null }); });

    box.querySelector("[data-wl-location-clear]")?.addEventListener("click", function () { set(null); });
    box.querySelector("[data-wl-location-locate]")?.addEventListener("click", function () {
      if (!navigator.geolocation) { status.textContent = "This device can't share its location."; return; }
      status.textContent = "Finding your location…";
      navigator.geolocation.getCurrentPosition(function (position) {
        const here = { latitude: position.coords.latitude, longitude: position.coords.longitude, accuracy_m: position.coords.accuracy };
        set(here);
        map.setView(latLng(here), setup.options.pin_zoom || 15);
      }, function () {
        status.textContent = "Couldn't get your location. Place the pin on the map instead.";
      }, { enableHighAccuracy: true, timeout: 15000 });
    });
  }

  function init(root) {
    root.querySelectorAll("[data-wl-map]:not(.leaflet-container)").forEach(showMap);
    root.querySelectorAll("[data-wl-map-picker]:not(.leaflet-container)").forEach(pickerMap);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { init(document); });
  else init(document);
  document.addEventListener("htmx:load", function (event) { init(event.target); });
})();
