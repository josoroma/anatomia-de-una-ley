/* ==========================================================================
   Anatomía de una Ley — lógica de la aplicación
   Lector SPA: índice, navegación, progreso, tema, continuidad y audio.
   ========================================================================== */
(function () {
  "use strict";

  const LIBRO = window.LIBRO;
  if (!LIBRO || !Array.isArray(LIBRO.chapters)) return;

  const chapters = LIBRO.chapters;
  const bySlug = {};
  chapters.forEach((c) => (bySlug[c.slug] = c));

  const $ = (sel) => document.querySelector(sel);
  const elIndice = $("#indice");
  const elCapitulo = $("#capitulo");
  const elNavegacion = $("#navegacion");
  const elBarraRelleno = $("#barra-relleno");
  const elLateral = $("#lateral");
  const elVelo = $("#velo");

  const STORE = "anatomia.progreso";

  // ── Estado persistente ─────────────────────────────────────────────────
  function leerEstado() {
    try { return JSON.parse(localStorage.getItem(STORE)) || {}; }
    catch { return {}; }
  }
  function escribirEstado(s) {
    try { localStorage.setItem(STORE, JSON.stringify(s)); } catch {}
  }

  // ── Tema ───────────────────────────────────────────────────────────────
  function aplicarTema(t) {
    document.documentElement.dataset.tema = t;
    const oscuro = t === "oscuro";
    $("#tema-icono").textContent = oscuro ? "☾" : "☀";
    $("#tema-texto").textContent = oscuro ? "Tema oscuro" : "Tema claro";
    try { localStorage.setItem("anatomia.tema", t); } catch {}
  }
  $("#boton-tema").addEventListener("click", () => {
    aplicarTema(document.documentElement.dataset.tema === "oscuro" ? "claro" : "oscuro");
  });

  // ── Índice ─────────────────────────────────────────────────────────────
  function construirIndice() {
    let parteActual = null;
    let fragmento = document.createDocumentFragment();
    chapters.forEach((c) => {
      if (c.parte !== parteActual) {
        parteActual = c.parte;
        const h = document.createElement("div");
        h.className = "indice__parte";
        h.textContent = c.parte;
        fragmento.appendChild(h);
      }
      const a = document.createElement("a");
      a.className = "indice__item";
      a.href = "#" + c.slug;
      a.dataset.slug = c.slug;
      const num = document.createElement("span");
      num.className = "indice__num";
      num.textContent = String(c.numero).padStart(2, "0");
      const t = document.createElement("span");
      t.textContent = c.titulo;
      a.appendChild(num);
      a.appendChild(t);
      fragmento.appendChild(a);
    });
    elIndice.appendChild(fragmento);
  }

  function marcarActivo(slug) {
    elIndice.querySelectorAll(".indice__item").forEach((a) => {
      a.classList.toggle("activo", a.dataset.slug === slug);
    });
  }

  // ── Render de capítulo ─────────────────────────────────────────────────
  function renderCapitulo(slug) {
    const c = bySlug[slug] || chapters[0];

    elCapitulo.innerHTML = "";
    const parte = document.createElement("p");
    parte.className = "capitulo__parte";
    parte.textContent = c.parte;
    const titulo = document.createElement("h1");
    titulo.className = "capitulo__titulo";
    titulo.textContent = c.titulo;
    const resumen = document.createElement("p");
    resumen.className = "capitulo__resumen";
    resumen.textContent = c.resumen;
    const cuerpo = document.createElement("div");
    cuerpo.className = "capitulo__cuerpo";
    cuerpo.innerHTML = c.html;

    elCapitulo.append(parte, titulo, resumen, cuerpo);

    marcarActivo(c.slug);
    document.title = c.titulo + " · Anatomía de una Ley";
    renderNavegacion(c);
    prepararAudio(c);
    enlazarInternos();

    // posición guardada
    const estado = leerEstado();
    const pct = estado.posiciones && estado.posiciones[c.slug];
    if (pct != null && !sessionStorage.getItem("anatomia.saltar-scroll")) {
      requestAnimationFrame(() => {
        const max = document.documentElement.scrollHeight - window.innerHeight;
        window.scrollTo(0, (pct / 100) * max);
      });
    }
    sessionStorage.removeItem("anatomia.saltar-scroll");
  }

  function renderNavegacion(c) {
    elNavegacion.innerHTML = "";
    if (c.prev) {
      elNavegacion.appendChild(crearNav(c.prev, "prev", "← Anterior"));
    } else {
      elNavegacion.appendChild(document.createElement("span"));
    }
    if (c.next) {
      elNavegacion.appendChild(crearNav(c.next, "next", "Siguiente →"));
    }
  }

  function crearNav(slug, dir, rotulo) {
    const c = bySlug[slug];
    const a = document.createElement("a");
    a.className = "nav-enlace nav-enlace--" + (dir === "next" ? "siguiente" : "anterior");
    a.href = "#" + slug;
    const r = document.createElement("span");
    r.className = "nav-enlace__rotulo";
    r.textContent = rotulo;
    const t = document.createElement("span");
    t.className = "nav-enlace__titulo";
    t.textContent = c.titulo;
    a.append(r, t);
    return a;
  }

  function enlazarInternos() {
    // enlaces a otros capítulos del libro por slug
    elCapitulo.querySelectorAll('a[href^="#"]').forEach((a) => {
      const slug = a.getAttribute("href").slice(1);
      if (bySlug[slug]) {
        a.addEventListener("click", (ev) => {
          ev.preventDefault();
          location.hash = slug;
        });
      }
    });
  }

  // ── Router ─────────────────────────────────────────────────────────────
  function slugActual() {
    const h = location.hash.replace(/^#\/?/, "");
    return bySlug[h] ? h : null;
  }

  function navegar(slug, saltarScroll) {
    if (saltarScroll) sessionStorage.setItem("anatomia.saltar-scroll", "1");
    if (location.hash !== "#" + slug) {
      location.hash = slug;
    } else {
      renderCapitulo(slug);
    }
    cerrarMenu();
  }

  function onHash() {
    const s = slugActual();
    if (s) renderCapitulo(s);
  }

  // ── Progreso de lectura ────────────────────────────────────────────────
  let raf = null;
  function actualizarProgreso() {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const pct = max > 0 ? Math.min(100, Math.max(0, (window.scrollY / max) * 100)) : 0;
    elBarraRelleno.style.width = pct + "%";

    const s = slugActual();
    if (s) {
      const estado = leerEstado();
      estado.ultimo = s;
      estado.posiciones = estado.posiciones || {};
      estado.posiciones[s] = pct;
      escribirEstado(estado);
    }
    raf = null;
  }
  window.addEventListener("scroll", () => {
    if (!raf) raf = requestAnimationFrame(actualizarProgreso);
  }, { passive: true });

  // ── Menú móvil ─────────────────────────────────────────────────────────
  function abrirMenu() { document.body.classList.add("menu-abierto"); elVelo.hidden = false; }
  function cerrarMenu() { document.body.classList.remove("menu-abierto"); elVelo.hidden = true; }
  $("#boton-menu").addEventListener("click", abrirMenu);
  elVelo.addEventListener("click", cerrarMenu);

  // ── Audio ──────────────────────────────────────────────────────────────
  const elReproductor = $("#reproductor");
  const elAudio = $("#audio");
  const elAudioPlay = $("#audio-play");
  const elAudioBarra = $("#audio-barra");
  const elAudioActual = $("#audio-actual");
  const elAudioTotal = $("#audio-total");
  const elAudioVelocidad = $("#audio-velocidad");
  const elAudioTitulo = $("#audio-titulo");
  let audioFallido = false;

  function prepararAudio(c) {
    const src = "assets/audio/" + String(c.numero).padStart(2, "0") + "-" + c.slug + ".mp3";
    audioFallido = false;
    elAudioTitulo.textContent = c.titulo;
    elAudio.src = src;
    elAudio.load();
    elAudioPlay.textContent = "▶";
    elAudioBarra.value = 0;
    elAudioActual.textContent = "0:00";
    elAudioTotal.textContent = "0:00";
    elReproductor.hidden = false;
  }

  function fmt(t) {
    if (!isFinite(t) || t < 0) return "0:00";
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return m + ":" + String(s).padStart(2, "0");
  }

  elAudio.addEventListener("loadedmetadata", () => {
    elAudioTotal.textContent = fmt(elAudio.duration);
    elAudioBarra.max = 100;
  });
  elAudio.addEventListener("timeupdate", () => {
    if (elAudio.duration) {
      elAudioBarra.value = (elAudio.currentTime / elAudio.duration) * 100;
      elAudioActual.textContent = fmt(elAudio.currentTime);
    }
  });
  elAudio.addEventListener("ended", () => {
    // continuidad entre capítulos
    const s = slugActual();
    const c = bySlug[s];
    if (c && c.next) navegar(c.next);
  });
  elAudio.addEventListener("play", () => { elAudioPlay.textContent = "❚❚"; });
  elAudio.addEventListener("pause", () => { elAudioPlay.textContent = "▶"; });
  elAudio.addEventListener("error", () => {
    audioFallido = true;
    elReproductor.hidden = true;
    elAudio.pause();
  });

  elAudioPlay.addEventListener("click", () => {
    if (elAudio.paused) elAudio.play().catch(() => {}); else elAudio.pause();
  });
  elAudioBarra.addEventListener("input", () => {
    if (elAudio.duration) {
      elAudio.currentTime = (elAudioBarra.value / 100) * elAudio.duration;
    }
  });
  elAudioVelocidad.addEventListener("change", () => {
    elAudio.playbackRate = parseFloat(elAudioVelocidad.value);
  });
  $("#audio-retro").addEventListener("click", () => {
    elAudio.currentTime = Math.max(0, elAudio.currentTime - 15);
  });
  $("#audio-adelante").addEventListener("click", () => {
    elAudio.currentTime = Math.min(elAudio.duration || 0, elAudio.currentTime + 15);
  });

  // ── Inicio ─────────────────────────────────────────────────────────────
  construirIndice();
  aplicarTema(document.documentElement.dataset.tema);
  window.addEventListener("hashchange", onHash);

  const inicial = slugActual();
  if (inicial) {
    renderCapitulo(inicial);
  } else {
    const estado = leerEstado();
    const ultimo = estado.ultimo && bySlug[estado.ultimo] ? estado.ultimo : chapters[0].slug;
    navegar(ultimo);
  }
})();
