(function () {
  'use strict';

  const STORAGE_KEY = 'ctm_active_role';
  const ROLES = ['organizer', 'user'];

  function getStoredRole() {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      return ROLES.indexOf(value) !== -1 ? value : null;
    } catch (error) {
      return null;
    }
  }

  function setStoredRole(role) {
    try {
      localStorage.setItem(STORAGE_KEY, role);
    } catch (error) {
      // Ignore storage errors in private mode.
    }
  }

  function applyRole(role) {
    document.body.setAttribute('data-ctm-role', role);
    if (window.CTM_MOCK && window.CTM_MOCK.demoUsers && window.CTM_MOCK.demoUsers[role]) {
      window.CTM_MOCK.currentUser = window.CTM_MOCK.demoUsers[role];
    }
  }

  function currentRole() {
    return document.body.getAttribute('data-ctm-role') || 'organizer';
  }

  function updateButtons() {
    document.querySelectorAll('.ctm-role-switcher button').forEach(function (button) {
      button.classList.toggle('is-active', button.getAttribute('data-role') === currentRole());
    });
  }

  function renderSwitcher() {
    if (document.querySelector('.ctm-role-switcher')) return;
    const switcher = document.createElement('div');
    switcher.className = 'ctm-role-switcher';
    switcher.innerHTML =
      '<span class="ctm-role-label">Demo role</span>' +
      '<button type="button" data-role="organizer">Organizer</button>' +
      '<button type="button" data-role="user">User</button>';
    document.body.appendChild(switcher);

    switcher.querySelectorAll('button').forEach(function (button) {
      button.addEventListener('click', function () {
        const role = button.getAttribute('data-role');
        setStoredRole(role);
        applyRole(role);
        updateButtons();
      });
    });

    updateButtons();
  }

  function bootstrap() {
    if (!document.body) {
      document.addEventListener('DOMContentLoaded', bootstrap, { once: true });
      return;
    }

    const fallbackRole =
      window.CTM_MOCK && window.CTM_MOCK.currentUser && window.CTM_MOCK.currentUser.role
        ? window.CTM_MOCK.currentUser.role
        : 'organizer';
    applyRole(getStoredRole() || fallbackRole);
    renderSwitcher();
  }

  bootstrap();
})();
