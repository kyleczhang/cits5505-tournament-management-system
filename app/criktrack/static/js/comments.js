/* Match / tournament comments — backed by /api/{matches|tournaments}/<id>/comments. */
(function () {
  'use strict';

  const MAX_LEN = 500;

  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  function endpoint(section) {
    const matchId = section.getAttribute('data-match-id');
    const tournamentId = section.getAttribute('data-tournament-id');
    if (matchId) return '/api/matches/' + encodeURIComponent(matchId) + '/comments';
    if (tournamentId) return '/api/tournaments/' + encodeURIComponent(tournamentId) + '/comments';
    return null;
  }

  function relativeTime(iso) {
    const then = new Date(iso);
    if (isNaN(then.getTime())) return '';
    const diff = (Date.now() - then.getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff / 60) + ' min ago';
    if (diff < 86400) return Math.floor(diff / 3600) + ' h ago';
    if (diff < 604800) return Math.floor(diff / 86400) + ' d ago';
    return then.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c];
    });
  }

  function renderComment(c) {
    const li = document.createElement('li');
    li.className = 'ctm-comment-card' + (c.role === 'organizer' ? ' is-organizer' : '');
    li.setAttribute('aria-label', 'Comment by ' + c.authorName);
    const initials = c.initials || (c.authorName || '').split(' ').map(function (w) { return w[0]; }).join('').slice(0, 2).toUpperCase();
    const badge = c.role === 'organizer'
      ? '<span class="ctm-badge-organizer" aria-label="Organizer role">Organizer</span>'
      : '';
    li.innerHTML =
      '<span class="avatar" aria-hidden="true">' + escapeHtml(initials) + '</span>' +
      '<div class="ctm-comment-body">' +
        '<div class="ctm-comment-head">' +
          '<span class="ctm-comment-author">' + escapeHtml(c.authorName) + '</span>' +
          badge +
          '<span class="ctm-comment-time" title="' + escapeHtml(c.createdAt) + '">' + escapeHtml(relativeTime(c.createdAt)) + '</span>' +
        '</div>' +
        '<p class="ctm-comment-text">' + escapeHtml(c.body) + '</p>' +
      '</div>';
    return li;
  }

  function renderList(section, comments) {
    const list = section.querySelector('[data-ctm-comment-list]');
    const countEl = section.querySelector('[data-ctm-comment-count]');
    if (!list) return;
    list.innerHTML = '';
    if (!comments.length) {
      list.innerHTML = '<li class="ctm-comment-empty">Be the first to comment.</li>';
    } else {
      comments.forEach(function (c) { list.appendChild(renderComment(c)); });
    }
    if (countEl) countEl.textContent = '(' + comments.length + ')';
  }

  function loadComments(section) {
    const url = endpoint(section);
    if (!url) return;
    fetch(url, { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (comments) { renderList(section, comments); })
      .catch(function () { renderList(section, []); });
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
      if (!body || body.length > MAX_LEN) return;
      const url = endpoint(section);
      if (!url) return;
      const submit = form.querySelector('button[type="submit"]');
      if (submit) submit.disabled = true;
      fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken(),
          'Accept': 'application/json',
        },
        body: JSON.stringify({ body: body }),
      })
        .then(function (r) {
          if (!r.ok) throw new Error('post failed');
          return r.json();
        })
        .then(function () {
          textarea.value = '';
          updateCount();
          loadComments(section);
          if (window.ctmToast) window.ctmToast('Comment posted.');
        })
        .catch(function () {
          if (window.ctmToast) window.ctmToast('Could not post comment.');
        })
        .then(function () {
          if (submit) submit.disabled = false;
        });
    });
  }

  function initAll() {
    document.querySelectorAll('[data-ctm-comments]').forEach(function (section) {
      loadComments(section);
      wireForm(section);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  window.ctmComments = { render: initAll };
})();
