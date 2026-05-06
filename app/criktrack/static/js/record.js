/* Match-record submission: gathers DOM rows into a JSON payload. */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('record-form');
    if (!form) return;
    const rosters = JSON.parse(form.getAttribute('data-rosters') || '{}');
    const teamAId = parseInt(form.getAttribute('data-team-a-id'), 10);
    const teamBId = parseInt(form.getAttribute('data-team-b-id'), 10);

    function firstBatTeamId() {
      const winner = parseInt(form.querySelector('#toss_winner').value, 10);
      const decision = form.querySelector('#toss_decision').value;
      if (!winner || !decision) return null;
      if (decision === 'bat') return winner;
      return winner === teamAId ? teamBId : teamAId;
    }

    function orderedPanes() {
      const panes = Array.from(form.querySelectorAll('[data-innings-pane]'));
      const firstId = firstBatTeamId();
      if (!firstId) return panes;
      const first = panes.find(function (p) {
        return parseInt(p.getAttribute('data-batting-team-id'), 10) === firstId;
      });
      if (!first) return panes;
      return [first].concat(panes.filter(function (p) { return p !== first; }));
    }

    function refreshInningsLabels() {
      const ordered = orderedPanes();
      const tabs = form.querySelectorAll('[data-innings-tab]');
      tabs.forEach(function (tab, idx) {
        const pane = ordered[idx];
        if (!pane) return;
        tab.setAttribute('data-bs-target', '#' + pane.id);
        tab.textContent =
          'Innings ' + (idx + 1) + ' — ' + pane.getAttribute('data-team-name');
      });
    }

    function clearAllFields() {
      form.querySelectorAll('[data-innings-pane]').forEach(function (pane) {
        pane.querySelectorAll(':scope > .row [data-field]').forEach(function (input) {
          input.value = 0;
        });
        const battingList = pane.querySelector('[data-batting-list]');
        if (battingList) {
          battingList.innerHTML = templateRow('batter', battingList.getAttribute('data-team-id'));
        }
        const bowlingList = pane.querySelector('[data-bowling-list]');
        if (bowlingList) {
          bowlingList.innerHTML = templateRow('bowler', bowlingList.getAttribute('data-team-id'));
        }
      });
      form.querySelector('#winner').value = '';
      form.querySelector('#result_text').value = '';
    }

    function onTossChange() {
      clearAllFields();
      refreshInningsLabels();
      refreshSummary();
    }
    form.querySelector('#toss_winner').addEventListener('change', onTossChange);
    form.querySelector('#toss_decision').addEventListener('change', onTossChange);

    function paneScore(pane) {
      const get = function (field) {
        const el = pane.querySelector(':scope > .row [data-field="' + field + '"]');
        return el ? parseFloat(el.value) || 0 : 0;
      };
      return {
        teamId: parseInt(pane.getAttribute('data-batting-team-id'), 10),
        teamName: pane.getAttribute('data-team-name'),
        runs: Math.floor(get('runs')),
        wickets: Math.floor(get('wickets')),
        overs: get('overs'),
      };
    }

    function refreshSummary() {
      const ordered = orderedPanes();
      ordered.forEach(function (pane, idx) {
        const hint = pane.querySelector('[data-chase-hint]');
        if (!hint) return;
        if (idx === 0) {
          hint.hidden = true;
          hint.textContent = '';
          return;
        }
        const first = paneScore(ordered[0]);
        const second = paneScore(pane);
        const target = first.runs + 1;
        let msg = 'Target: ' + target + ' (' + first.teamName + ' scored ' + first.runs + ').';
        if (second.runs >= target) {
          msg += ' ' + second.teamName + ' won by ' + (10 - second.wickets) + ' wickets.';
        } else if (second.wickets >= 10) {
          msg += ' ' + first.teamName + ' won by ' + (target - 1 - second.runs) + ' runs.';
        } else {
          msg += ' Needs ' + (target - second.runs) + ' more to win.';
        }
        hint.hidden = false;
        hint.textContent = msg;
      });

      const suggest = form.querySelector('[data-result-suggest]');
      const suggestText = form.querySelector('[data-result-suggest-text]');
      if (!suggest || !suggestText || ordered.length < 2) return;
      const first = paneScore(ordered[0]);
      const second = paneScore(ordered[1]);
      let winnerId = null;
      let resultText = '';
      if (second.runs >= first.runs + 1) {
        winnerId = second.teamId;
        resultText = second.teamName + ' won by ' + (10 - second.wickets) + ' wickets';
      } else if (second.wickets >= 10 && second.runs < first.runs) {
        winnerId = first.teamId;
        resultText = first.teamName + ' won by ' + (first.runs - second.runs) + ' runs';
      }
      if (!winnerId) {
        suggest.hidden = true;
        return;
      }
      suggest.hidden = false;
      suggest.dataset.winnerId = String(winnerId);
      suggest.dataset.resultText = resultText;
      suggestText.textContent = 'Suggested: ' + resultText + '.';
    }

    form.querySelectorAll('[data-innings-pane]').forEach(function (pane) {
      pane.querySelectorAll(':scope > .row [data-field]').forEach(function (input) {
        input.addEventListener('input', refreshSummary);
      });
    });

    const applyBtn = form.querySelector('[data-result-suggest-apply]');
    if (applyBtn) {
      applyBtn.addEventListener('click', function () {
        const suggest = form.querySelector('[data-result-suggest]');
        if (!suggest || !suggest.dataset.winnerId) return;
        form.querySelector('#winner').value = suggest.dataset.winnerId;
        form.querySelector('#result_text').value = suggest.dataset.resultText || '';
      });
    }

    refreshSummary();

    function playerSelect(teamId, placeholder) {
      const rows = rosters[String(teamId)] || [];
      const options = ['<option value="">' + placeholder + '</option>']
        .concat(rows.map(function (player) {
          return '<option value="' + player.id + '">' + player.name + '</option>';
        }))
        .join('');
      return '<select class="form-select" data-field="player_id">' + options + '</select>';
    }

    function templateRow(kind, teamId) {
      if (kind === 'batter') {
        return (
          '<div class="row g-2 align-items-center" data-row>' +
          '  <div class="col-md-4">' + playerSelect(teamId, 'Select batter') + '</div>' +
          '  <div class="col-md-3"><input type="text" class="form-control" data-field="dismissal" placeholder="Dismissal"></div>' +
          '  <div class="col-md-2"><input type="number" class="form-control" data-field="runs" placeholder="Runs"></div>' +
          '  <div class="col-md-2"><input type="number" class="form-control" data-field="balls" placeholder="Balls"></div>' +
          '  <div class="col-md-1"><button type="button" class="btn btn-ctm-ghost w-100" data-remove-row aria-label="Remove">×</button></div>' +
          '</div>'
        );
      }
      return (
        '<div class="row g-2 align-items-center" data-row>' +
        '  <div class="col-md-4">' + playerSelect(teamId, 'Select bowler') + '</div>' +
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
        list.insertAdjacentHTML('beforeend', templateRow('batter', list.getAttribute('data-team-id')));
        return;
      }
      const addBowler = e.target.closest('[data-add-bowler]');
      if (addBowler) {
        const list = addBowler.previousElementSibling;
        list.insertAdjacentHTML('beforeend', templateRow('bowler', list.getAttribute('data-team-id')));
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
        if ((obj.player_id || '').trim()) out.push(obj);
      });
      return out;
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const errBox = document.getElementById('record-errors');
      errBox.style.display = 'none';
      errBox.textContent = '';

      const innings = [];
      orderedPanes().forEach(function (pane) {
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
