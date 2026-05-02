/* Shared client-side interactivity used across the live app. */

(function () {
  'use strict';

  // Lightweight toast for small client-side actions.
  function showToast(message) {
    let container = document.getElementById('ctm-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'ctm-toast-container';
      container.style.cssText =
        'position:fixed; bottom:24px; right:24px; z-index:9999; display:flex; flex-direction:column; gap:8px;';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.setAttribute('role', 'status');
    toast.style.cssText =
      'background:#0F766E; color:#fff; padding:0.75rem 1.1rem; border-radius:8px; box-shadow:0 8px 24px rgba(0,0,0,0.18); font-weight:500;';
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(function () {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 300ms';
    }, 2500);
    setTimeout(function () {
      toast.remove();
    }, 3000);
  }
  window.ctmToast = showToast;

  // Dynamic player-row adder on the record-results page (AJAX-style DOM manipulation).
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-add-row]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const target = document.querySelector(btn.getAttribute('data-target'));
        if (!target) return;
        const template = target.querySelector('[data-row-template]');
        if (!template) return;
        const clone = template.cloneNode(true);
        clone.removeAttribute('data-row-template');
        clone.style.display = '';
        clone.querySelectorAll('input').forEach(function (i) {
          i.value = '';
        });
        const removeBtn = clone.querySelector('[data-remove-row]');
        if (removeBtn)
          removeBtn.addEventListener('click', function () {
            clone.remove();
          });
        target.appendChild(clone);
      });
    });
  });

  // Share button (public tournament link).
  document.addEventListener('DOMContentLoaded', function () {
    const shareBtns = document.querySelectorAll('[data-share]');
    shareBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        const url = btn.getAttribute('data-share');
        if (navigator.clipboard) {
          navigator.clipboard.writeText(url).then(function () {
            showToast('Share link copied to clipboard');
          });
        } else {
          prompt('Copy this link:', url);
        }
      });
    });
  });
})();
