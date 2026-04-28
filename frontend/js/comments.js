/* Match comments.

   Host a comments feed by dropping:
     <section class="ctm-comments" data-ctm-comments data-match-id="501"></section>
   into a page. The rest is built from window.CTM_MOCK.comments until the
   Flask endpoint lands in Checkpoint 3 (Section 14.2).

   Post flow is local-only for now: a new comment is prepended to the list and
   persisted in memory so the demo feels responsive. A real fetch() replaces
   this in the backend phase. */

(function () {
  'use strict';

  const MAX_LEN = 500;

  function allComments() {
    return (window.CTM_MOCK && window.CTM_MOCK.comments) || [];
  }

  function relativeTime(iso) {
    const then = new Date(iso);
    if (isNaN(then.getTime())) return '';
    const diff = (Date.now() - then.getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff / 60) + ' min ago';
    if (diff < 86400) return Math.floor(diff / 3600) + ' h ago';
    if (diff < 604800) return Math.floor(diff / 86400) + ' d ago';
    return then.toLocaleDateString(undefined, {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      }[c];
    });
  }

  function renderComment(c) {
    const li = document.createElement('li');
    li.className =
      'ctm-comment-card' + (c.role === 'organizer' ? ' is-organizer' : '');
    li.setAttribute('aria-label', 'Comment by ' + c.authorName);
    const initials =
      c.initials ||
      c.authorName
        .split(' ')
        .map(function (w) {
          return w[0];
        })
        .join('')
        .slice(0, 2)
        .toUpperCase();
    const badge =
      c.role === 'organizer'
        ? '<span class="ctm-badge-organizer" aria-label="Organizer role">Organizer</span>'
        : '';
    li.innerHTML =
      '<span class="avatar" aria-hidden="true">' +
      escapeHtml(initials) +
      '</span>' +
      '<div class="ctm-comment-body">' +
      '<div class="ctm-comment-head">' +
      '<span class="ctm-comment-author">' +
      escapeHtml(c.authorName) +
      '</span>' +
      badge +
      '<span class="ctm-comment-time" title="' +
      escapeHtml(c.createdAt) +
      '">' +
      escapeHtml(relativeTime(c.createdAt)) +
      '</span>' +
      '</div>' +
      '<p class="ctm-comment-text">' +
      escapeHtml(c.body) +
      '</p>' +
      '</div>';
    return li;
  }

  function renderList(section) {
    const matchId = parseInt(section.getAttribute('data-match-id'), 10);
    const tournamentId = parseInt(
      section.getAttribute('data-tournament-id'),
      10,
    );
    const list = section.querySelector('[data-ctm-comment-list]');
    const countEl = section.querySelector('[data-ctm-comment-count]');
    if (!list) return;
    const comments = allComments()
      .filter(function (c) {
        if (!isNaN(matchId)) return c.matchId === matchId;
        if (!isNaN(tournamentId)) return c.tournamentId === tournamentId;
        return true;
      })
      .sort(function (a, b) {
        return new Date(b.createdAt) - new Date(a.createdAt);
      });

    list.innerHTML = '';
    if (!comments.length) {
      list.innerHTML =
        '<li class="ctm-comment-empty">Be the first to comment.</li>';
    } else {
      comments.forEach(function (c) {
        list.appendChild(renderComment(c));
      });
    }
    if (countEl) countEl.textContent = '(' + comments.length + ')';
  }

  function wireForm(section) {
    const form = section.querySelector('[data-ctm-comment-form]');
    if (!form) return;
    const textarea = form.querySelector('textarea');
    const counter = form.querySelector('[data-ctm-comment-counter]');

    function updateCount() {
      if (!counter) return;
      const n = textarea.value.length;
      counter.textContent = n + ' / ' + MAX_LEN;
      counter.style.color = n > MAX_LEN ? 'var(--ctm-danger)' : '';
    }
    if (textarea) {
      textarea.setAttribute('maxlength', String(MAX_LEN));
      textarea.addEventListener('input', updateCount);
      updateCount();
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const body = (textarea.value || '').trim();
      if (!body) return;
      if (body.length > MAX_LEN) return;
      const user = (window.CTM_MOCK && window.CTM_MOCK.currentUser) || {
        id: 0,
        displayName: 'You',
        initials: 'YO',
        role: 'user',
      };
      const matchId = parseInt(section.getAttribute('data-match-id'), 10);
      const tournamentId = parseInt(
        section.getAttribute('data-tournament-id'),
        10,
      );
      const comment = {
        id: Date.now(),
        matchId: isNaN(matchId) ? null : matchId,
        tournamentId: isNaN(tournamentId) ? null : tournamentId,
        authorId: user.id,
        authorName: user.displayName,
        initials: user.initials,
        role: user.role,
        body: body,
        createdAt: new Date().toISOString(),
      };
      /* Prepend so the demo feels live. Real submit posts to Flask and reloads
         the list from the server response. */
      if (window.CTM_MOCK) {
        window.CTM_MOCK.comments = window.CTM_MOCK.comments || [];
        window.CTM_MOCK.comments.unshift(comment);
      }
      textarea.value = '';
      updateCount();
      renderList(section);
      if (window.ctmToast) window.ctmToast('Comment posted (mock).');
    });
  }

  function updateCurrentUserCard(section) {
    const user = (window.CTM_MOCK && window.CTM_MOCK.currentUser) || null;
    const avatar = section.querySelector('[data-ctm-current-avatar]');
    const name = section.querySelector('[data-ctm-current-name]');
    const badge = section.querySelector('[data-ctm-current-badge]');
    if (user) {
      if (avatar) avatar.textContent = user.initials || '';
      if (name) name.textContent = user.displayName || '';
      if (badge) badge.style.display = user.role === 'organizer' ? '' : 'none';
    }
  }

  function initAll() {
    document
      .querySelectorAll('[data-ctm-comments]')
      .forEach(function (section) {
        renderList(section);
        wireForm(section);
        updateCurrentUserCard(section);
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  /* Re-render "commenting as" header whenever the demo role switcher flips. */
  document.addEventListener('ctm:rolechange', function () {
    document
      .querySelectorAll('[data-ctm-comments]')
      .forEach(updateCurrentUserCard);
  });

  window.ctmComments = { render: initAll };
})();
