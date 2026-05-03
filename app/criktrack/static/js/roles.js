/* Demo role switcher for checkpoint review.

   Real authorization is enforced by Flask; this utility only toggles the
   frontend demo persona (`organizer` / `user`) so reviewers can quickly check
   role-gated UI states without reloading fixture data.
*/

(function () {
  'use strict';

  const STORAGE_KEY = 'ctm_active_role';
  const ROLES = ['organizer', 'user'];

  function getStoredRole() {
    try {
      const role = localStorage.getItem(STORAGE_KEY);
      return ROLES.indexOf(role) !== -1 ? role : null;
    } catch (e) {
      return null;
    }
  }

  function setStoredRole(role) {
    try {
      localStorage.setItem(STORAGE_KEY, role);
    } catch (e) {
      // Ignore private mode or storage quota errors.
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

    document.dispatchEvent(new CustomEvent('ctm:rolechange', { detail: { role: role } }));
  }

  function currentRole() {
    return document.body.getAttribute('data-ctm-role') || 'organizer';
  }

  function updateSwitcherState() {
    const active = currentRole();
    document.querySelectorAll('.ctm-role-switcher button').forEach(function (btn) {
      const isActive = btn.getAttribute('data-role') === active;
      btn.classList.toggle('is-active', isActive);
      btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });
  }

  function renderSwitcher() {
    if (document.querySelector('.ctm-role-switcher')) return;

    const shell = document.createElement('div');
    shell.className = 'ctm-role-switcher';
    shell.setAttribute('role', 'group');
    shell.setAttribute('aria-label', 'Demo role switcher');
    shell.innerHTML =
      '<span class="ctm-role-label">Demo role</span>' +
      '<button type="button" data-role="organizer" aria-pressed="false">Organizer</button>' +
      '<button type="button" data-role="user" aria-pressed="false">User</button>';

    document.body.appendChild(shell);

    shell.querySelectorAll('button').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const role = btn.getAttribute('data-role');
        setStoredRole(role);
        applyRole(role);
        updateSwitcherState();
      });
    });

    updateSwitcherState();
  }

  function bootstrap() {
    if (!document.body) {
      document.addEventListener('DOMContentLoaded', bootstrap, { once: true });
      return;
    }

    const stored = getStoredRole();
    const fallback = (window.CTM_MOCK && window.CTM_MOCK.currentUser && window.CTM_MOCK.currentUser.role) || 'organizer';
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
