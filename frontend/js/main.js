(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    const currentFile = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
    document.querySelectorAll('.ctm-navbar .nav-link').forEach(function (link) {
      const page = (link.getAttribute('data-page') || '').toLowerCase();
      if (page && currentFile.startsWith(page)) {
        link.classList.add('active');
      }
    });
  });

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('form[data-ctm-validate]').forEach(function (form) {
      form.noValidate = true;

      form.querySelectorAll('input, select, textarea').forEach(function (field) {
        field.addEventListener('blur', function () {
          validateField(field);
        });
        field.addEventListener('input', function () {
          if (field.classList.contains('is-invalid')) {
            validateField(field);
          }
        });
      });

      form.addEventListener('submit', function (event) {
        let isValid = true;
        form.querySelectorAll('input, select, textarea').forEach(function (field) {
          if (!validateField(field)) {
            isValid = false;
          }
        });

        const password = form.querySelector('input[name="password"]');
        const confirmPassword = form.querySelector('input[name="confirm_password"]');
        if (password && confirmPassword && password.value !== confirmPassword.value) {
          setInvalid(confirmPassword, 'Passwords do not match.');
          isValid = false;
        }

        if (!isValid) {
          event.preventDefault();
          return;
        }

        event.preventDefault();
        const redirect = form.getAttribute('data-redirect');
        showToast('Form submitted successfully (mock).');
        if (redirect) {
          setTimeout(function () {
            location.href = redirect;
          }, 500);
        }
      });
    });
  });

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-share]').forEach(function (button) {
      button.addEventListener('click', function () {
        const url = button.getAttribute('data-share');
        if (!url) return;

        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(function () {
            showToast('Share link copied to clipboard');
          });
        } else {
          window.prompt('Copy this link:', url);
        }
      });
    });
  });

  function validateField(field) {
    if (field.disabled || field.type === 'hidden') return true;

    const value = field.value ? field.value.trim() : '';
    if (field.hasAttribute('required') && !value) {
      setInvalid(field, 'This field is required.');
      return false;
    }

    if (field.type === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      setInvalid(field, 'Please enter a valid email address.');
      return false;
    }

    if (field.name === 'password' && value && value.length < 8) {
      setInvalid(field, 'Password must be at least 8 characters.');
      return false;
    }

    setValid(field);
    return true;
  }

  function setInvalid(field, message) {
    field.classList.add('is-invalid');
    field.setAttribute('aria-invalid', 'true');
    const hint = field.parentElement && field.parentElement.querySelector('.form-hint-error');
    if (hint) {
      hint.textContent = message;
      hint.classList.add('show');
      hint.setAttribute('role', 'alert');
    }
  }

  function setValid(field) {
    field.classList.remove('is-invalid');
    field.removeAttribute('aria-invalid');
    const hint = field.parentElement && field.parentElement.querySelector('.form-hint-error');
    if (hint) {
      hint.textContent = '';
      hint.classList.remove('show');
    }
  }

  function showToast(message) {
    let container = document.getElementById('ctm-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'ctm-toast-container';
      container.style.cssText = 'position:fixed; bottom:24px; right:24px; z-index:9999; display:flex; flex-direction:column; gap:8px;';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.style.cssText = 'background:#0f766e; color:#fff; padding:0.75rem 1rem; border-radius:8px; box-shadow:0 8px 24px rgba(0,0,0,.2);';
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(function () {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 250ms ease';
    }, 2200);
    setTimeout(function () {
      toast.remove();
    }, 2500);
  }
})();
