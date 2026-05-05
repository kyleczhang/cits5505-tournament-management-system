/* Team picker for tournament create — search + checkbox list + selected chips.
   Mirrors state into the hidden <select multiple> which is the form source of truth. */
(function () {
  function init(root) {
    const select = root.querySelector('select[multiple]');
    const list = root.querySelector('[data-team-picker-list]');
    const search = root.querySelector('[data-team-picker-search]');
    const chips = root.querySelector('[data-team-picker-chips]');
    const countEl = root.querySelector('[data-team-picker-count]');
    const clearBtn = root.querySelector('[data-team-picker-clear]');
    const noResults = root.querySelector('[data-team-picker-no-results]');
    if (!select || !list) return;

    const checkboxes = Array.from(root.querySelectorAll('[data-team-picker-option]'));
    const labelByValue = new Map();
    checkboxes.forEach((cb) => {
      const span = cb.parentElement.querySelector('span');
      labelByValue.set(cb.value, span ? span.textContent : cb.value);
    });

    function syncSelectFromCheckboxes() {
      Array.from(select.options).forEach((opt) => {
        const cb = checkboxes.find((c) => c.value === opt.value);
        opt.selected = !!(cb && cb.checked);
      });
    }

    function renderChips() {
      chips.innerHTML = '';
      const selected = checkboxes.filter((c) => c.checked);
      countEl.textContent = selected.length + ' selected';
      selected.forEach((cb) => {
        const chip = document.createElement('span');
        chip.className = 'ctm-team-chip';
        chip.innerHTML =
          '<span></span>' +
          '<button type="button" aria-label="Remove team">' +
          '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>' +
          '</button>';
        chip.querySelector('span').textContent = labelByValue.get(cb.value) || cb.value;
        chip.querySelector('button').addEventListener('click', () => {
          cb.checked = false;
          onChange();
        });
        chips.appendChild(chip);
      });
    }

    function applySearch() {
      const q = (search.value || '').trim().toLowerCase();
      let visible = 0;
      list.querySelectorAll('.ctm-team-picker__item').forEach((li) => {
        const name = li.getAttribute('data-team-name') || '';
        const show = !q || name.indexOf(q) !== -1;
        li.hidden = !show;
        if (show) visible += 1;
      });
      if (noResults) noResults.hidden = visible !== 0 || checkboxes.length === 0;
    }

    function onChange() {
      syncSelectFromCheckboxes();
      renderChips();
    }

    checkboxes.forEach((cb) => cb.addEventListener('change', onChange));
    if (search) search.addEventListener('input', applySearch);
    if (clearBtn)
      clearBtn.addEventListener('click', () => {
        checkboxes.forEach((c) => (c.checked = false));
        onChange();
      });

    onChange();
    applySearch();
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-team-picker]').forEach(init);
  });
})();
