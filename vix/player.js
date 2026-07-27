// ============================================================
//  Nova — player (video.js + HLS)
// ============================================================

let player = null;

export function disposePlayer() {
  if (player) {
    try {
      player.dispose();
    } catch {}
    player = null;
  }
}

// Crea il player su un <video> e carica la sorgente HLS (m3u8 già proxata).
export function mountPlayer(videoEl, src, { startAt = 0, onTime } = {}) {
  disposePlayer();

player = videojs(videoEl, {
    controls: true,
    fluid: true,
    preload: "auto",
    playsinline: true,
    playbackRates: [],
    html5: {
      vhs: { overrideNative: true, useDevicePixelRatio: true },
      nativeAudioTracks: false,
      nativeVideoTracks: false,
      nativeTextTracks: false,
    },
    controlBar: {
      children: [
        "playToggle",
        "currentTimeDisplay",
        "timeDivider",
        "durationDisplay",
        "progressControl",
        "subsCapsButton",
        "audioTrackButton",
        "volumePanel",
        "fullscreenToggle",
      ],
    },
  });

  player.src({ src, type: "application/x-mpegURL" });

  player.ready(() => {
    // Selettore qualità (richiede videojs-contrib-quality-levels + plugin)
    if (typeof player.hlsQualitySelector === "function") {
      player.hlsQualitySelector({ displayCurrentQuality: true });
    }
    const vol = parseFloat(localStorage.getItem("nv_volume"));
    if (!isNaN(vol)) player.volume(vol);

    if (startAt && startAt > 5) {
      player.one("loadedmetadata", () => player.currentTime(startAt));
    }
    player.play().catch(() => {});
  });

  player.on("volumechange", () =>
    localStorage.setItem("nv_volume", player.volume())
  );

  // Auto-fullscreen: TV sempre, Android/orientato → fullscreen
  const isMobileOrTv = () => {
    const html = document.documentElement;
    return html.classList.contains("is-tv") || html.classList.contains("is-touch") || /android/i.test(navigator.userAgent);
  };
  player.one("play", () => {
    if (isMobileOrTv()) {
      try { player.requestFullscreen(); } catch {}
    }
  });

  // Quando esce dal fullscreen su mobile/TV → torna alla descrizione
  const onFsChange = () => {
    if (!document.fullscreenElement && !player.isFullscreen?.() && isMobileOrTv()) {
      window.dispatchEvent(new CustomEvent("nova:exitfullscreen"));
    }
  };
  document.addEventListener("fullscreenchange", onFsChange);
  player.on("dispose", () => document.removeEventListener("fullscreenchange", onFsChange));

  if (onTime) {
    let last = 0;
    player.on("timeupdate", () => {
      const now = player.currentTime();
      if (Math.abs(now - last) >= 5) {
        last = now;
        onTime(now, player.duration());
      }
    });
  }

  // Scorciatoie tastiera
  const keys = (e) => {
    if (!player) return;
    const tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea") return;
    switch (e.key.toLowerCase()) {
      case " ": e.preventDefault(); player.paused() ? player.play() : player.pause(); break;
      case "arrowright": player.currentTime(player.currentTime() + 10); break;
      case "arrowleft": player.currentTime(player.currentTime() - 10); break;
      case "arrowup": e.preventDefault(); player.volume(Math.min(1, player.volume() + 0.1)); break;
      case "arrowdown": e.preventDefault(); player.volume(Math.max(0, player.volume() - 0.1)); break;
      case "f": player.isFullscreen() ? player.exitFullscreen() : player.requestFullscreen(); break;
      case "m": player.muted(!player.muted()); break;
    }
  };
  document.addEventListener("keydown", keys);
  player.on("dispose", () => document.removeEventListener("keydown", keys));

  return player;
}


