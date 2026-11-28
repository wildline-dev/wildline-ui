// The Media card's full-screen viewer (wildline-ui#6): a thumbnail ([data-wl-media-open], or
// any element with that attribute, such as a form answer's thumbnail) opens its <dialog>. The
// full-size photo loads only when it's opened, and a video stops when it closes. Without
// JavaScript, the thumbnail is a link to the original. Listens while the click is on its way
// down (capture), so it runs before htmx or other handlers on the link.
(function () {
  document.addEventListener("click", function (event) {
    const opener = event.target.closest("[data-wl-media-open]");
    if (opener) {
      const dialog = document.querySelector(opener.dataset.wlMediaOpen);
      if (!dialog || typeof dialog.showModal !== "function") return; // follow the link
      // Before anything else on the page acts on the click, such as htmx following a boosted link.
      event.preventDefault();
      event.stopPropagation();
      dialog.querySelectorAll("img[data-src]").forEach(function (img) {
        if (!img.getAttribute("src")) img.src = img.dataset.src;
      });
      dialog.showModal();
      return;
    }
    // A click on the dark area around the photo closes the viewer.
    const dialog = event.target.closest(".wl-media-dialog");
    if (dialog && (event.target === dialog || event.target.classList.contains("wl-media-dialog-body"))) dialog.close();
  }, true);
  document.addEventListener("close", function (event) {
    if (!event.target.classList || !event.target.classList.contains("wl-media-dialog")) return;
    event.target.querySelectorAll("video, audio").forEach(function (media) { media.pause(); });
  }, true);
})();
