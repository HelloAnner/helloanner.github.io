/* Shared article module behavior: theme toggle, back-to-top, TOC scroll-spy,
   code-block copy buttons. Loaded on every book/article page. */

/* theme toggle — localStorage key "theme", .dark class on <html> */
(() => {
  const root = document.documentElement;
  if (localStorage.getItem("theme") === "dark") root.classList.add("dark");
  const t = document.getElementById("theme-toggle");
  if (t) t.addEventListener("click", () => {
    root.classList.toggle("dark");
    localStorage.setItem("theme", root.classList.contains("dark") ? "dark" : "light");
  });
})();

/* back-to-top: appears after scrolling past ~1.2 viewports */
(() => {
  const btn = document.getElementById("to-top");
  if (!btn) return;
  const onScroll = () => btn.classList.toggle("show", window.scrollY > innerHeight * 1.2);
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  btn.addEventListener("click", () => scrollTo({ top: 0, behavior: "smooth" }));
})();

/* TOC rail: highlight the section currently in view. */
(() => {
  const toc = document.getElementById("page-toc");
  if (!toc) return;
  const links = Array.from(toc.querySelectorAll("a[href^='#']"));
  const map = new Map();               // section id -> link
  const targets = [];
  for (const a of links) {
    const id = a.getAttribute("href").slice(1);
    const el = document.getElementById(id);
    if (el) { map.set(id, a); targets.push(el); }
  }
  if (!targets.length) return;

  let activeId = null;
  const setActive = (id) => {
    if (id === activeId) return;
    if (activeId && map.get(activeId)) map.get(activeId).classList.remove("active");
    activeId = id;
    if (id && map.get(id)) map.get(id).classList.add("active");
  };
  const io = new IntersectionObserver((entries) => {
    // pick the entry nearest the top of the viewport that is intersecting
    const vis = entries.filter(e => e.isIntersecting)
                       .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
    if (vis.length) setActive(vis[0].target.id);
  }, { rootMargin: "-20% 0px -70% 0px", threshold: 0 });
  targets.forEach(t => io.observe(t));
})();

/* code blocks: copy-to-clipboard */
(() => {
  document.querySelectorAll(".codeblock .copy-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const code = btn.parentNode.querySelector("pre code");
      if (!code) return;
      navigator.clipboard.writeText(code.textContent).then(() => {
        const prev = btn.textContent;
        btn.textContent = "Copied";
        setTimeout(() => { btn.textContent = prev; }, 1500);
      });
    });
  });
})();
