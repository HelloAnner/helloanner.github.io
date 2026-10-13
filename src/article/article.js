/* Shared article module behavior (simonwillison.net style):
   three-state theme toggle (auto -> light -> dark) and heading permalinks. */

/* theme — default "auto" follows the OS via prefers-color-scheme (handled in
   CSS); choosing light/dark stores an override on <html data-theme>. */
(function () {
  const toggle = document.getElementById('theme-toggle');
  if (!toggle) return;
  const iconAuto = document.getElementById('icon-auto');
  const iconLight = document.getElementById('icon-light');
  const iconDark = document.getElementById('icon-dark');

  function getTheme() {
    return localStorage.getItem('theme') || 'auto';
  }
  function setTheme(theme) {
    if (theme === 'auto') {
      localStorage.removeItem('theme');
      document.documentElement.removeAttribute('data-theme');
    } else {
      localStorage.setItem('theme', theme);
      document.documentElement.setAttribute('data-theme', theme);
    }
    updateIcon(theme);
  }
  function updateIcon(theme) {
    iconAuto.style.display = theme === 'auto' ? 'block' : 'none';
    iconLight.style.display = theme === 'light' ? 'block' : 'none';
    iconDark.style.display = theme === 'dark' ? 'block' : 'none';
    const labels = {
      'auto': 'Theme: Auto (system preference). Click to switch to light.',
      'light': 'Theme: Light. Click to switch to dark.',
      'dark': 'Theme: Dark. Click to switch to auto.'
    };
    toggle.setAttribute('aria-label', labels[theme]);
  }
  function cycleTheme() {
    const current = getTheme();
    const next = current === 'auto' ? 'light' : current === 'light' ? 'dark' : 'auto';
    setTheme(next);
  }
  updateIcon(getTheme());
  toggle.addEventListener('click', cycleTheme);
})();

/* append "#" permalink anchors to content headings */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.note h2[id], .note h3[id], .note h4[id]').forEach(el => {
    const id = el.getAttribute('id');
    const hashLink = document.createElement('a');
    hashLink.className = 'heading-permalink';
    hashLink.setAttribute('href', '#' + id);
    hashLink.innerText = '#';
    el.appendChild(document.createTextNode('\u00A0'));
    el.appendChild(hashLink);
  });
});
