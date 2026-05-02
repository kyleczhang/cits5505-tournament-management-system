/* Follow / unfollow toggle for tournament, team and player targets.
   Uses a button element with data attributes:
     <button data-ctm-follow data-target-type="tournament" data-target-id="42"
             data-following="0">Follow</button>
   Backed by /api/follow (POST/DELETE) and /api/follow/status. */
(function () {
  'use strict';

  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  function applyState(btn, following) {
    btn.setAttribute('data-following', following ? '1' : '0');
    btn.classList.toggle('is-following', !!following);
    btn.setAttribute('aria-pressed', following ? 'true' : 'false');
    const label = btn.querySelector('[data-ctm-follow-label]');
    if (label) {
      label.textContent = following ? 'Following' : 'Follow';
    } else {
      btn.setAttribute(
        'aria-label', following ? 'Unfollow' : 'Follow'
      );
      btn.setAttribute('title', following ? 'Unfollow' : 'Follow');
    }
  }

  function toggle(btn) {
    if (btn.disabled) return;
    const following = btn.getAttribute('data-following') === '1';
    const method = following ? 'DELETE' : 'POST';
    btn.disabled = true;
    fetch('/api/follow', {
      method: method,
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken(),
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        targetType: btn.getAttribute('data-target-type'),
        targetId: Number(btn.getAttribute('data-target-id')),
      }),
    })
      .then(function (r) {
        if (r.status === 401) {
          window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
          throw new Error('auth');
        }
        if (!r.ok) throw new Error('toggle failed');
        return r.json();
      })
      .then(function (data) {
        applyState(btn, !!data.following);
        if (window.ctmToast) {
          window.ctmToast(data.following ? 'Following.' : 'Unfollowed.');
        }
      })
      .catch(function () {
        if (window.ctmToast) window.ctmToast('Could not update follow.');
      })
      .then(function () {
        btn.disabled = false;
      });
  }

  function initAll() {
    document.querySelectorAll('[data-ctm-follow]').forEach(function (btn) {
      applyState(btn, btn.getAttribute('data-following') === '1');
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        toggle(btn);
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
