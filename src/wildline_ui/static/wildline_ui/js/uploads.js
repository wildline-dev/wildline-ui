// Share my location (wildline-ui#8) and the photo/video/recording picker (#9). Small and
// dependency-free, so pages on a weak signal can inline it ({% inline_media form.media %}).
(function () {
  // --- Share my location: fill in the hidden position where the browser allows it.
  function shareLocation(box) {
    if (box.dataset.ready) return;
    box.dataset.ready = "1";
    const button = box.querySelector("[data-wl-share-location]");
    const status = box.querySelector("[data-wl-share-status]");
    if (!navigator.geolocation) return;
    button.hidden = false;
    const input = function (key) { return box.querySelector('[data-wl-input="' + key + '"]'); };
    if (!input("latitude").value) status.textContent = "";
    button.addEventListener("click", function () {
      status.textContent = "Finding you…";
      navigator.geolocation.getCurrentPosition(function (position) {
        const accuracy = Math.round(position.coords.accuracy);
        input("latitude").value = position.coords.latitude.toFixed(6);
        input("longitude").value = position.coords.longitude.toFixed(6);
        input("accuracy_m").value = accuracy;
        status.textContent = "Location shared (within about " + accuracy + " m).";
        box.classList.remove("is-invalid");
        box.parentNode.querySelectorAll(".invalid-feedback").forEach(function (e) { e.remove(); });
      }, function () {
        status.textContent = "Couldn't get your location. Check that location is allowed for this site, then try again.";
      }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
    });
  }

  // --- The file picker: list what's chosen, with previews, sizes and warnings.
  const WORDS = { photo: "photo", video: "video", audio: "recording" };

  function kindOf(file) {
    const type = file.type || "";
    if (type.indexOf("image/") === 0 || /\.(heic|heif)$/i.test(file.name)) return "photo";
    if (type.indexOf("video/") === 0) return "video";
    if (type.indexOf("audio/") === 0 || /\.m4a$/i.test(file.name)) return "audio";
    return "";
  }

  function size(bytes) {
    if (bytes >= 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1).replace(/\.0$/, "") + " MB";
    return Math.max(1, Math.round(bytes / 1024)) + " KB";
  }

  function mediaUploader(box) {
    if (box.dataset.ready) return;
    box.dataset.ready = "1";
    const input = box.querySelector("input[type=file]");
    const list = box.querySelector("[data-wl-upload-list]");
    const kinds = JSON.parse(box.dataset.kinds || "[]");
    const limits = JSON.parse(box.dataset.limits || "{}");
    const maxFiles = parseInt(box.dataset.maxFiles, 10) || 0;
    const canRemove = typeof DataTransfer === "function";
    let urls = [];

    function problem(file) {
      const kind = kindOf(file);
      if (kinds.indexOf(kind) < 0) {
        return "This form takes " + kinds.map(function (k) { return WORDS[k] + "s"; }).join(" and ") + ".";
      }
      if (limits[kind] && file.size > limits[kind]) {
        return "Too large: " + WORDS[kind] + "s can be up to " + size(limits[kind]) + ".";
      }
      return "";
    }

    function show() {
      urls.forEach(URL.revokeObjectURL);
      urls = [];
      list.textContent = "";
      const files = Array.from(input.files || []);
      list.hidden = !files.length;
      files.forEach(function (file, index) {
        const row = document.createElement("li");
        row.className = "wl-upload";
        const preview = document.createElement("span");
        preview.className = "wl-upload-preview";
        if (kindOf(file) === "photo" && /^image\/(jpeg|png|webp|gif)$/.test(file.type)) {
          const url = URL.createObjectURL(file);
          urls.push(url);
          const img = document.createElement("img");
          img.src = url;
          img.alt = "";
          preview.appendChild(img);
        } else {
          preview.textContent = { photo: "Photo", video: "Video", audio: "Audio" }[kindOf(file)] || "File";
        }
        const text = document.createElement("span");
        text.className = "wl-upload-text";
        const name = document.createElement("span");
        name.className = "wl-upload-name";
        name.textContent = file.name;
        const detail = document.createElement("span");
        const warning = problem(file);
        detail.className = warning ? "wl-upload-warning" : "wl-upload-size";
        detail.textContent = warning || size(file.size);
        text.append(name, detail);
        row.append(preview, text);
        if (canRemove) {
          const remove = document.createElement("button");
          remove.type = "button";
          remove.className = "btn btn-sm btn-link wl-upload-remove";
          remove.textContent = "Remove";
          remove.setAttribute("aria-label", "Remove " + file.name);
          remove.addEventListener("click", function () {
            const kept = new DataTransfer();
            Array.from(input.files).forEach(function (f, i) { if (i !== index) kept.items.add(f); });
            input.files = kept.files;
            show();
          });
          row.appendChild(remove);
        }
        list.appendChild(row);
      });
      if (maxFiles && files.length > maxFiles) {
        const row = document.createElement("li");
        row.className = "wl-upload-warning";
        row.textContent = "Send up to " + maxFiles + " files at a time.";
        list.appendChild(row);
      }
    }
    input.addEventListener("change", show);
    show();
  }

  function init(root) {
    root.querySelectorAll("[data-wl-location-uploader]").forEach(shareLocation);
    root.querySelectorAll("[data-wl-media-uploader]").forEach(mediaUploader);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { init(document); });
  else init(document);
  document.addEventListener("htmx:load", function (event) { init(event.target); });
})();
