// A related record picked by searching (wildline-ui#5): [data-wl-record-search] holds a hidden
// [data-wl-record-id] input, a search box and a results list. Typing asks the search URL for
// ?q=<text>, which answers {"results": [{"id", "label", "detail"}]}; choosing a result sets the
// ID and fires "wl:record-change" with it. Runs on page load and whenever htmx swaps in content.
(function () {
  function setUp(root) {
    if (root.dataset.wlReady) return;
    root.dataset.wlReady = "1";
    const id = root.querySelector("[data-wl-record-id]");
    const box = root.querySelector("[data-wl-record-query]");
    const list = root.querySelector("[data-wl-record-results]");
    const status = root.querySelector("[data-wl-record-status]");
    const chosen = box.value;
    let timer = null;
    let request = 0;
    let active = -1;

    function close() {
      list.hidden = true;
      box.setAttribute("aria-expanded", "false");
      active = -1;
    }

    function choose(result) {
      id.value = result.id;
      box.value = result.label;
      close();
      status.textContent = result.detail ? result.label + ", " + result.detail : result.label;
      root.dispatchEvent(new CustomEvent("wl:record-change", { bubbles: true, detail: result }));
    }

    function show(results) {
      list.replaceChildren();
      results.forEach(function (result, index) {
        const item = document.createElement("li");
        item.className = "wl-record-result";
        item.id = list.id + "_" + index;
        item.setAttribute("role", "option");
        const label = document.createElement("span");
        label.textContent = result.label;
        item.append(label);
        if (result.detail) {
          const detail = document.createElement("small");
          detail.textContent = result.detail;
          item.append(detail);
        }
        item.addEventListener("mousedown", function (event) { event.preventDefault(); choose(result); });
        list.append(item);
      });
      if (!results.length) {
        const none = document.createElement("li");
        none.className = "wl-record-none";
        none.textContent = "Nothing found.";
        list.append(none);
      }
      list.hidden = false;
      box.setAttribute("aria-expanded", "true");
      list.results = results;
    }

    function search() {
      const query = box.value.trim();
      if (!query) { close(); return; }
      const mine = ++request;
      const url = new URL(root.dataset.wlSearchUrl, window.location.href);
      url.searchParams.set("q", query);
      fetch(url, { headers: { Accept: "application/json" }, credentials: "same-origin" })
        .then(function (response) { return response.ok ? response.json() : { results: [] }; })
        .then(function (data) { if (mine === request) show(data.results || []); })
        .catch(function () { if (mine === request) status.textContent = "Couldn't search just now."; });
    }

    function highlight(index) {
      const items = list.querySelectorAll(".wl-record-result");
      if (!items.length) return;
      active = (index + items.length) % items.length;
      items.forEach(function (item, i) { item.classList.toggle("active", i === active); });
      box.setAttribute("aria-activedescendant", items[active].id);
    }

    box.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(search, 250); });
    box.addEventListener("keydown", function (event) {
      if (list.hidden) return;
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        highlight(active + (event.key === "ArrowDown" ? 1 : -1));
      } else if (event.key === "Enter" && active >= 0) {
        event.preventDefault();
        choose(list.results[active]);
      } else if (event.key === "Escape") {
        close();
      }
    });
    // Leaving the box without choosing puts back the record's name: the ID didn't change.
    box.addEventListener("blur", function () {
      close();
      if (!status.textContent && box.value !== chosen) box.value = chosen;
    });
  }

  function setUpAll(scope) {
    (scope || document).querySelectorAll("[data-wl-record-search]").forEach(setUp);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { setUpAll(); });
  } else {
    setUpAll();
  }
  document.addEventListener("htmx:load", function (event) { setUpAll(event.target); });
})();
