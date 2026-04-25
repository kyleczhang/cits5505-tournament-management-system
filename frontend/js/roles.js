/* Role management for the static prototype.

   Real authz lives in Flask (Section 14 of IMPLEMENTATION-PLAN.md). Here we
   just flip a body attribute so CSS can hide organizer-only UI and write the
   active role back onto window.CTM_MOCK.currentUser so other scripts see a
   consistent view.

   A floating demo switcher in the bottom-right lets graders flip between
   roles on any page — it is deleted in Checkpoint 3. */

(function () {
  'use strict';

  const STORAGE_KEY = 'ctm_active_role';
  const ROLES = ['organizer', 'user'];

  function getStoredRole() {
    try {
      const v = localStorage.getItem(STORAGE_KEY);
      return ROLES.indexOf(v) !== -1 ? v : null;
    } catch (e) {
      return null;
    }
  }

  function setStoredRole(role) {
    try {
      localStorage.setItem(STORAGE_KEY, role);
    } catch (e) {
      /* ignore quota / private-mode errors */
    }
  }

  function applyRole(role) {
    document.body.setAttribute('data-ctm-role', role);
    const mock = window.CTM_MOCK;
    if (mock && mock.demoUsers && mock.demoUsers[role]) {
      mock.currentUser = mock.demoUsers[role];
    } else if (mock && mock.currentUser) {
      mock.currentUser.role = role;
    }
    document.dispatchEvent(
      new CustomEvent('ctm:rolechange', { detail: { role: role } }),
    );
  }

  function currentRole() {
    return document.body.getAttribute('data-ctm-role') || 'organizer';
  }

  function renderSwitcher() {
    if (document.querySelector('.ctm-role-switcher')) return;
    const wrap = document.createElement('div');
    wrap.className = 'ctm-role-switcher';
    wrap.setAttribute('role', 'group');
    wrap.setAttribute('aria-label', 'Demo role (checkpoint 2 only)');
    wrap.innerHTML =
      '<span class="ctm-role-label">Demo role</span>' +
      '<button type="button" data-role="organizer">Organizer</button>' +
      '<button type="button" data-role="user">User</button>';
    document.body.appendChild(wrap);
    wrap.querySelectorAll('button').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const role = btn.getAttribute('data-role');
        setStoredRole(role);
        applyRole(role);
        updateSwitcherState();
      });
    });
    updateSwitcherState();
  }

  function updateSwitcherState() {
    const active = currentRole();
    document
      .querySelectorAll('.ctm-role-switcher button')
      .forEach(function (b) {
        b.classList.toggle('is-active', b.getAttribute('data-role') === active);
      });
  }

  /* Apply stored role (or the mock default) as early as possible so CSS gating
     does not flash wrong UI. We set the body attribute synchronously once the
     body element is available. */
  function bootstrap() {
    if (!document.body) {
      document.addEventListener('DOMContentLoaded', bootstrap, { once: true });
      return;
    }
    const stored = getStoredRole();
    const fallback =
      (window.CTM_MOCK &&
        window.CTM_MOCK.currentUser &&
        window.CTM_MOCK.currentUser.role) ||
      'organizer';
    applyRole(stored || fallback);
    renderSwitcher();
  }

  bootstrap();

  window.ctmRoles = {
    current: currentRole,
    set: function (role) {
      if (ROLES.indexOf(role) === -1) return;
      setStoredRole(role);
      applyRole(role);
      updateSwitcherState();
    },
  };
})();
