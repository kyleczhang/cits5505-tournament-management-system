/* Match-record submission: gathers DOM rows into a JSON payload. */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('record-form');
    if (!form) return;

    function templateRow(kind) {
      if (kind === 'batter') {
        return (
          '<div class="row g-2 align-items-center" data-row>' +
          '  <div class="col-md-4"><input type="text" class="form-control" data-field="player_name" placeholder="Batter name"></div>' +
          '  <div class="col-md-3"><input type="text" class="form-control" data-field="dismissal" placeholder="Dismissal"></div>' +
          '  <div class="col-md-2"><input type="number" class="form-control" data-field="runs" placeholder="Runs"></div>' +
          '  <div class="col-md-2"><input type="number" class="form-control" data-field="balls" placeholder="Balls"></div>' +
          '  <div class="col-md-1"><button type="button" class="btn btn-ctm-ghost w-100" data-remove-row aria-label="Remove">×</button></div>' +
          '</div>'
        );
      }
      return (
        '<div class="row g-2 align-items-center" data-row>' +
        '  <div class="col-md-4"><input type="text" class="form-control" data-field="player_name" placeholder="Bowler"></div>' +
        '  <div class="col-md-2"><input type="number" step="0.1" class="form-control" data-field="overs" placeholder="Overs"></div>' +
        '  <div class="col-md-2"><input type="number" class="form-control" data-field="runs" placeholder="Runs"></div>' +
        '  <div class="col-md-2"><input type="number" class="form-control" data-field="wickets" placeholder="Wkts"></div>' +
        '  <div class="col-md-2"><button type="button" class="btn btn-ctm-ghost w-100" data-remove-row aria-label="Remove">Remove</button></div>' +
        '</div>'
      );
    }

    form.addEventListener('click', function (e) {
      const target = e.target.closest('[data-remove-row]');
      if (target) {
        const row = target.closest('[data-row]');
        if (row) row.remove();
        return;
      }
      const addBatter = e.target.closest('[data-add-batter]');
      if (addBatter) {
        const list = addBatter.previousElementSibling;
        list.insertAdjacentHTML('beforeend', templateRow('batter'));
        return;
      }
      const addBowler = e.target.closest('[data-add-bowler]');
      if (addBowler) {
        const list = addBowler.previousElementSibling;
        list.insertAdjacentHTML('beforeend', templateRow('bowler'));
      }
    });

    function gatherRows(list) {
      const rows = list.querySelectorAll('[data-row]');
      const out = [];
      rows.forEach(function (row) {
        const obj = {};
        row.querySelectorAll('[data-field]').forEach(function (f) {
          const key = f.getAttribute('data-field');
          obj[key] = f.value;
        });
        if ((obj.player_name || '').trim()) out.push(obj);
      });
      return out;
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const errBox = document.getElementById('record-errors');
      errBox.style.display = 'none';
      errBox.textContent = '';

      const innings = [];
      form.querySelectorAll('[data-innings-pane]').forEach(function (pane) {
        const battingTeamId = parseInt(pane.getAttribute('data-batting-team-id'), 10);
        const meta = {};
        pane.querySelectorAll(':scope > .row [data-field]').forEach(function (f) {
          meta[f.getAttribute('data-field')] = f.value;
        });
        innings.push({
          batting_team_id: battingTeamId,
          runs: meta.runs,
          wickets: meta.wickets,
          overs: meta.overs,
          batting: gatherRows(pane.querySelector('[data-batting-list]')),
          bowling: gatherRows(pane.querySelector('[data-bowling-list]')),
        });
      });

      const payload = {
        toss: {
          winner_team_id: form.querySelector('#toss_winner').value,
          decision: form.querySelector('#toss_decision').value,
        },
        result: {
          winner_team_id: form.querySelector('#winner').value,
          result_text: form.querySelector('#result_text').value,
        },
        innings: innings,
      };

      const submitBtn = form.querySelector('button[type="submit"]');
      const original = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving…';

      const csrfToken =
        document.querySelector('meta[name="csrf-token"]') &&
        document.querySelector('meta[name="csrf-token"]').getAttribute('content');

      fetch(form.getAttribute('data-record-url'), {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken || '',
          'Accept': 'application/json',
        },
        body: JSON.stringify(payload),
      })
        .then(function (r) {
          return r.json().then(function (data) { return { status: r.status, data: data }; });
        })
        .then(function (res) {
          if (res.status === 200 && res.data.redirect) {
            location.href = res.data.redirect;
            return;
          }
          submitBtn.disabled = false;
          submitBtn.innerHTML = original;
          const errs = (res.data && res.data.errors) || { _: 'Could not save result.' };
          errBox.style.display = '';
          errBox.innerHTML = Object.keys(errs)
            .map(function (k) { return '<div><strong>' + k + ':</strong> ' + errs[k] + '</div>'; })
            .join('');
        })
        .catch(function () {
          submitBtn.disabled = false;
          submitBtn.innerHTML = original;
          errBox.style.display = '';
          errBox.textContent = 'Network error — please try again.';
        });
    });
  });
})();
