// Рендер записанного прогона CLI.
// Данные — ui/data/cli-run.js (window.__CLI_RUN__), генерируются
// скриптом tools/trace-cli.py на настоящем CLI.

(function () {
  'use strict';

  var run = window.__CLI_RUN__;
  var host = document.getElementById('steps');
  if (!run || !host) return;

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function runtimeChips(rt) {
    if (!rt || !rt.stage) return '';
    var parts = [
      ['стадия', rt.stage],
      ['статус', rt.status],
      ['ревизия', rt.revision],
      ['артефактов', rt.artifacts],
      ['событий', rt.events]
    ];
    if (rt.owner) parts.splice(3, 0, ['владелец', rt.owner]);

    return '<div class="runtime">' + parts.filter(function (p) {
      return p[1] !== undefined && p[1] !== null && p[1] !== '';
    }).map(function (p) {
      return '<span class="kv">' + p[0] + ' <b>' + escapeHtml(p[1]) + '</b></span>';
    }).join('') + '</div>';
  }

  run.steps.forEach(function (step, i) {
    var blocked = !step.ok;

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'step' + (blocked ? ' blocked' : '');
    btn.setAttribute('aria-expanded', 'false');
    btn.id = 'step-btn-' + i;
    btn.innerHTML =
      '<span class="marker">' + (blocked ? '×' : '✓') + '</span>' +
      '<span>' +
        '<span class="cmd">' + escapeHtml(step.command) + '</span>' +
        '<span class="why">' + escapeHtml(step.note || '') + '</span>' +
      '</span>';

    var body = document.createElement('div');
    body.className = 'step-body';
    body.hidden = true;
    body.id = 'step-body-' + i;
    body.innerHTML =
      (step.output ? '<pre><code>' + escapeHtml(step.output) + '</code></pre>' : '') +
      runtimeChips(step.runtime);

    btn.setAttribute('aria-controls', body.id);
    btn.addEventListener('click', function () {
      var open = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', open ? 'false' : 'true');
      body.hidden = open;
    });

    host.appendChild(btn);
    host.appendChild(body);

    // Отказы интереснее успехов — их раскрываем сразу.
    if (blocked) {
      btn.setAttribute('aria-expanded', 'true');
      body.hidden = false;
    }
  });

  var expandAll = document.getElementById('expand-all');
  if (expandAll) {
    expandAll.addEventListener('click', function () {
      var buttons = host.querySelectorAll('.step');
      var anyClosed = Array.prototype.some.call(buttons, function (b) {
        return b.getAttribute('aria-expanded') === 'false';
      });
      Array.prototype.forEach.call(buttons, function (b) {
        b.setAttribute('aria-expanded', anyClosed ? 'true' : 'false');
        var body = document.getElementById(b.getAttribute('aria-controls'));
        if (body) body.hidden = !anyClosed;
      });
      expandAll.textContent = anyClosed ? 'Свернуть всё' : 'Развернуть всё';
    });
  }
})();
