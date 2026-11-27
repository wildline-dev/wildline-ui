// Players for voicemails and recordings (wildline-ui#7, from wildline-dispatch#122):
// play/pause, the waveform, and the time, drawn by wavesurfer.js. Load after it. Without it,
// the browser's own player shows. Runs on page load and whenever htmx swaps in new content.
(function () {
  // Drawing a waveform downloads the whole file, so longer audio gets a plain progress bar and
  // only downloads when it's played.
  const WAVEFORM_MAX_SECONDS = 600;
  const players = new Set();

  function themeColor(el, name, fallback) {
    return getComputedStyle(el).getPropertyValue(name).trim() || fallback;
  }

  function clock(seconds) {
    const whole = Math.max(0, Math.floor(seconds || 0));
    const minutes = Math.floor(whole / 60);
    return minutes + ":" + String(whole % 60).padStart(2, "0");
  }

  function build(box) {
    if (box.dataset.ready || typeof WaveSurfer === "undefined") return;
    box.dataset.ready = "1";
    const audio = box.querySelector("audio");
    const player = box.querySelector(".wl-audio-player");
    const button = player.querySelector(".wl-audio-play");
    const playIcon = button.querySelector('[data-wl-audio-icon="play"]');
    const pauseIcon = button.querySelector('[data-wl-audio-icon="pause"]');
    const label = button.dataset.label ? " " + button.dataset.label : "";
    const time = player.querySelector(".wl-audio-time");
    const error = box.querySelector(".wl-audio-error");
    const duration = parseFloat(box.dataset.duration) || 0;
    const drawWave = !duration || duration <= WAVEFORM_MAX_SECONDS;

    audio.removeAttribute("controls");
    audio.hidden = true;
    player.hidden = false;

    const options = {
      container: player.querySelector(".wl-audio-wave"),
      media: audio,
      height: 40,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      cursorWidth: 0,
      waveColor: themeColor(box, "--bs-secondary-color", "#adb5bd"),
      progressColor: themeColor(box, "--bs-primary", "#0d6efd"),
    };
    if (drawWave) {
      options.url = box.dataset.src;
      options.normalize = true; // phone audio is quiet: scale the loudest part to full height
    } else {
      // A thin band the length of the audio: a progress bar that seeks like the waveform.
      options.peaks = [Array(200).fill(0.1)];
      options.duration = duration;
      options.barWidth = undefined;
      options.barGap = undefined;
      options.barRadius = undefined;
      audio.src = box.dataset.src;
      audio.preload = "none";
    }
    const wave = WaveSurfer.create(options);
    players.add(wave);

    function showTime() {
      const total = wave.getDuration() || duration;
      time.textContent = clock(wave.getCurrentTime()) + (total ? " / " + clock(total) : "");
    }
    function showFailure() {
      error.hidden = false;
      button.disabled = true;
    }
    function showPlaying(playing) {
      playIcon.hidden = playing;
      pauseIcon.hidden = !playing;
      button.setAttribute("aria-label", (playing ? "Pause" : "Play") + label);
    }
    showTime();
    wave.on("ready", showTime);
    wave.on("timeupdate", showTime);
    wave.on("error", showFailure);
    audio.addEventListener("error", showFailure);
    wave.on("play", function () {
      players.forEach(function (other) { if (other !== wave) other.pause(); });
      showPlaying(true);
    });
    wave.on("pause", function () { showPlaying(false); });
    wave.on("finish", function () { wave.setTime(0); });
    button.addEventListener("click", function () { wave.playPause(); });
    box.wlAudio = wave;
  }

  function buildAll(root) {
    root.querySelectorAll("[data-wl-audio]").forEach(build);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { buildAll(document); });
  else buildAll(document);
  document.addEventListener("htmx:load", function (event) { buildAll(event.target); });
  // Swapping content out (such as opening another record in a pane) stops what was playing in it.
  document.addEventListener("htmx:beforeSwap", function (event) {
    event.detail.target.querySelectorAll("[data-wl-audio]").forEach(function (box) {
      if (box.wlAudio) {
        players.delete(box.wlAudio);
        box.wlAudio.destroy();
      }
    });
  });
})();
