/* Shared client-side interactivity. In the real app this file would also
   handle AJAX calls to the Flask backend — for now it just wires up form
   validation, highlights the active nav link, and renders any mock data. */

(function () {
  'use strict';

  function closeMobileNav() {
    const collapse = document.querySelector('.navbar-collapse');
    if (collapse && collapse.classList.contains('show')) {
      collapse.classList.remove('show');
      const toggler = document.querySelector('.navbar-toggler');
      if (toggler) toggler.setAttribute('aria-expanded', 'false');
    }
  }

  // Highlight the current nav link based on the page filename.
  document.addEventListener('DOMContentLoaded', function () {
    const path = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
    document.querySelectorAll('.ctm-navbar .nav-link').forEach(function (link) {
      const href = (link.getAttribute('href') || '').split('/').pop().toLowerCase();
      const target = (link.getAttribute('data-page') || '').toLowerCase();
      if ((target && path.startsWith(target)) || (href && path.startsWith(href))) link.classList.add('active');

      // Close mobile nav after selecting a link.
      link.addEventListener('click', function () {
        closeMobileNav();
      });
    });
  });

  // Generic blur-validation for forms marked with data-ctm-validate.
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('form[data-ctm-validate]').forEach(function (form) {
      form.noValidate = true;
      form.querySelectorAll('input, select, textarea').forEach(function (field) {
        field.addEventListener('blur', function () { validateField(field); });
        field.addEventListener('input', function () {
          if (field.classList.contains('is-invalid')) validateField(field);
        });
      });
      form.addEventListener('submit', function (e) {
        let ok = true;
        form.querySelectorAll('input, select, textarea').forEach(function (f) {
          if (!validateField(f)) ok = false;
        });
        // Password confirm check.
        const pwd = form.querySelector('input[name="password"]');
        const cf  = form.querySelector('input[name="confirm_password"]');
        if (pwd && cf && pwd.value !== cf.value) {
          setInvalid(cf, 'Passwords do not match.');
          ok = false;
        }
        if (!ok) { e.preventDefault(); return; }
        // Simulate async submit (no real backend yet).
        e.preventDefault();
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.disabled = true;
          const original = submitBtn.innerHTML;
          submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Submitting…';
          setTimeout(function () {
            submitBtn.disabled = false;
            submitBtn.innerHTML = original;
            showToast('Form submitted successfully (mock).');
            const redirect = form.getAttribute('data-redirect');
            if (redirect) setTimeout(function () { location.href = redirect; }, 600);
          }, 800);
        }
      });
    });
  });

  function validateField(field) {
    if (field.type === 'hidden' || field.disabled) return true;
    if (field.hasAttribute('required') && !field.value.trim()) {
      setInvalid(field, field.dataset.msgRequired || 'This field is required.');
      return false;
    }
    if (field.type === 'email' && field.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(field.value)) {
      setInvalid(field, 'Please enter a valid email address.');
      return false;
    }
    if (field.name === 'password' && field.value && field.value.length < 8) {
      setInvalid(field, 'Password must be at least 8 characters.');
      return false;
    }
    setValid(field);
    return true;
  }

  function setInvalid(field, msg) {
    field.classList.add('is-invalid');
    field.setAttribute('aria-invalid', 'true');
    const hint = field.parentElement.querySelector('.form-hint-error');
    if (hint) { hint.textContent = msg; hint.classList.add('show'); hint.setAttribute('role', 'alert'); }
  }
  function setValid(field) {
    field.classList.remove('is-invalid');
    field.removeAttribute('aria-invalid');
    const hint = field.parentElement.querySelector('.form-hint-error');
    if (hint) { hint.classList.remove('show'); hint.textContent = ''; }
  }

  // Lightweight toast shown for mock submissions.
  function showToast(message) {
    let container = document.getElementById('ctm-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'ctm-toast-container';
      container.style.cssText = 'position:fixed; bottom:24px; right:24px; z-index:9999; display:flex; flex-direction:column; gap:8px;';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.setAttribute('role', 'status');
    toast.style.cssText = 'background:#0F766E; color:#fff; padding:0.75rem 1.1rem; border-radius:8px; box-shadow:0 8px 24px rgba(0,0,0,0.18); font-weight:500;';
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(function () { toast.style.opacity = '0'; toast.style.transition = 'opacity 300ms'; }, 2500);
    setTimeout(function () { toast.remove(); }, 3000);
  }
  window.ctmToast = showToast;

  // Tournament status filter (search tournaments page).
  document.addEventListener('DOMContentLoaded', function () {
    const filters = document.querySelectorAll('[data-filter-status]');
    const cards = document.querySelectorAll('[data-card-status]');
    const searchInput = document.getElementById('tournament-search');
    let currentStatus = 'all';
    function apply() {
      const q = (searchInput && searchInput.value || '').toLowerCase().trim();
      cards.forEach(function (card) {
        const status = card.getAttribute('data-card-status');
        const name = (card.getAttribute('data-card-name') || '').toLowerCase();
        const match = (currentStatus === 'all' || status === currentStatus) && (!q || name.includes(q));
        card.style.display = match ? '' : 'none';
      });
    }
    filters.forEach(function (btn) {
      btn.addEventListener('click', function () {
        filters.forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        currentStatus = btn.getAttribute('data-filter-status');
        apply();
      });
    });
    if (searchInput) searchInput.addEventListener('input', apply);
  });

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
        clone.querySelectorAll('input').forEach(function (i) { i.value = ''; });
        const removeBtn = clone.querySelector('[data-remove-row]');
        if (removeBtn) removeBtn.addEventListener('click', function () { clone.remove(); });
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

    // Expose minimal design tokens and helpers to other scripts.
    try {
      const styles = getComputedStyle(document.documentElement);
      window.ctmConfig = {
        colors: {
          primary: styles.getPropertyValue('--ctm-primary').trim(),
          accent: styles.getPropertyValue('--ctm-accent').trim(),
        },
        tokens: {
          gap: styles.getPropertyValue('--ctm-gap').trim() || '1rem'
        }
      };
    } catch (e) {
      window.ctmConfig = {};
    }

    // Keyboard helper: close mobile nav on Escape and allow quick focus to main.
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape') {
        closeMobileNav();

        const activeModal = document.querySelector('.modal.show');
        if (activeModal && window.bootstrap && window.bootstrap.Modal) {
          const modal = window.bootstrap.Modal.getOrCreateInstance(activeModal);
          modal.hide();
        }
      }

      // Keep keyboard focus inside the active modal while tabbing.
      if (ev.key === 'Tab') {
        const activeModal = document.querySelector('.modal.show');
        if (!activeModal) return;

        const focusables = activeModal.querySelectorAll(
          'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        if (!focusables.length) return;

        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (ev.shiftKey && document.activeElement === first) {
          ev.preventDefault();
          last.focus();
        } else if (!ev.shiftKey && document.activeElement === last) {
          ev.preventDefault();
          first.focus();
        }
      }

      // Make custom role="button" elements keyboard-activatable with Enter.
      if (ev.key === 'Enter') {
        const el = document.activeElement;
        if (
          el &&
          el.getAttribute &&
          el.getAttribute('role') === 'button' &&
          !el.hasAttribute('disabled')
        ) {
          ev.preventDefault();
          el.click();
        }
      }
    });
  });
})();
