/* Live cricket feed widget.

   Fetches from CTM_CONFIG.liveFeedEndpoint, which in Checkpoint 3 will be a
   Flask route that proxies https://api.cricapi.com/v1/currentMatches (see
   cricketdata.org). Until that backend exists the fetch fails and we fall
   back to the sample payload in CTM_MOCK.liveFeed so the widget still
   renders during frontend review.

   The widget polls every CTM_CONFIG.liveFeedPollMs. Consumers only need to
   place a container on the page:
     <div data-ctm-livefeed></div>
*/

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
    head.innerHTML =
      '<h3 class="ctm-live-title"><span class="ctm-live-dot" aria-hidden="true"></span>Live cricket</h3>' +
      '<span class="ctm-live-source">Data: ' +
      (meta.source === 'mock'
        ? '<em>sample — backend proxy pending</em>'
        : '<a href="https://cricketdata.org/" target="_blank" rel="noopener">CricketData.org</a>') +
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
        return r.json();
      },
    );
  }

  function load(container) {
    const cfg = window.CTM_CONFIG || {};
    const endpoint = cfg.liveFeedEndpoint;
    fetchLive(endpoint)
      .then(function (payload) {
        renderPayload(container, payload, {
          source: 'api',
          updatedAt: new Date(),
        });
      })
      .catch(function () {
        const fallback = (window.CTM_MOCK && window.CTM_MOCK.liveFeed) || {
          data: [],
        };
        renderPayload(container, fallback, {
          source: 'mock',
          updatedAt: new Date(),
        });
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
