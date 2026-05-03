/* Live cricket feed widget backed by the Flask live-feed proxy. */

(function () {
  'use strict';

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

  function formatScore(match) {
    if (!match.score || !match.score.length) return 'Yet to start';
    return match.score
      .map(function (s) {
        const teamPrefix = s.inning
          ? s.inning.replace(/\s*Innings$/, '') + ': '
          : '';
        const overs = s.o != null ? ' (' + s.o + ' ov)' : '';
        return teamPrefix + s.r + '/' + s.w + overs;
      })
      .join(' · ');
  }

  function renderPayload(container, payload, meta) {
    const list = (payload && payload.data) || [];
    container.innerHTML = '';

    const head = document.createElement('div');
    head.className = 'ctm-live-head';
    const sourceLabel =
      meta.source === 'unavailable'
        ? '<em>temporarily unavailable</em>'
        : meta.source === 'mock'
          ? '<em>feed not configured</em>'
          : '<a href="https://cricketdata.org/" target="_blank" rel="noopener">CricketData.org</a>';
    const freshnessLabel =
      meta.source === 'stale' ? ' · showing cached data' : '';
    head.innerHTML =
      '<h3 class="ctm-live-title"><span class="ctm-live-dot" aria-hidden="true"></span>Live cricket</h3>' +
      '<span class="ctm-live-source">Data: ' +
      sourceLabel +
      freshnessLabel +
      (meta.updatedAt
        ? ' · updated ' + meta.updatedAt.toLocaleTimeString()
        : '') +
      '</span>';
    container.appendChild(head);

    if (!list.length) {
      const empty = document.createElement('div');
      empty.className = 'ctm-live-empty';
      empty.textContent = 'No live matches right now. Check back soon.';
      container.appendChild(empty);
      return;
    }

    const ul = document.createElement('ul');
    ul.className = 'ctm-live-list';
    list.slice(0, 6).forEach(function (m) {
      const li = document.createElement('li');
      li.className = 'ctm-live-card';
      const teams = (m.teamInfo || [])
        .map(function (t) {
          return t.shortname || t.name;
        })
        .join(' vs ');
      li.innerHTML =
        '<div class="ctm-live-teams">' +
        escapeHtml(teams || m.name || '') +
        '</div>' +
        '<div class="ctm-live-score">' +
        escapeHtml(formatScore(m)) +
        '</div>' +
        '<div class="ctm-live-status">' +
        escapeHtml(m.status || '') +
        '</div>';
      ul.appendChild(li);
    });
    container.appendChild(ul);
  }

  function fetchLive(endpoint) {
    if (!endpoint) return Promise.reject(new Error('no endpoint'));
    return fetch(endpoint, { headers: { Accept: 'application/json' } }).then(
      function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json().then(function (payload) {
          const source =
            r.headers.get('X-CTM-Stale') === '1'
              ? 'stale'
              : r.headers.get('X-CTM-Source') || 'live';
          return { payload: payload, source: source };
        });
      },
    );
  }

  function load(container) {
    const cfg = window.CTM_CONFIG || {};
    const endpoint = cfg.liveFeedEndpoint;
    fetchLive(endpoint)
      .then(function (result) {
        renderPayload(container, result.payload, {
          source: result.source,
          updatedAt: new Date(),
        });
      })
      .catch(function () {
        renderPayload(
          container,
          { data: [] },
          {
            source: 'unavailable',
            updatedAt: null,
          },
        );
      });
  }

  function initAll() {
    const containers = document.querySelectorAll('[data-ctm-livefeed]');
    if (!containers.length) return;
    const cfg = window.CTM_CONFIG || {};
    const interval = Math.max(5000, cfg.liveFeedPollMs || 30000);
    containers.forEach(function (c) {
      c.classList.add('ctm-live-widget');
      load(c);
      setInterval(function () {
        load(c);
      }, interval);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
