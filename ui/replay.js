// Проигрыватель прогона конвейера.
// Данные приходят из ui/data/engine-run.js (window.__ENGINE_RUN__),
// который генерирует `make trace` на реальном движке.

(function () {
  'use strict';

  var run = window.__ENGINE_RUN__;
  if (!run) return;

  // Состав фаз. Порядок и роли — из .ai/scripts/pipeline-watcher.go
  // (phaseOrder, phaseOrchestrators, andGates) и templates/ai/pipeline-state.json.
  var PHASES = [
    {
      id: 'business',
      orchestrator: 'product-manager',
      members: ['product-analyst', 'market-analyst', 'strategist', 'financier'],
      gate: 'AND: 4 аналитика'
    },
    {
      id: 'systemic',
      orchestrator: 'owner',
      members: ['analyst', 'architect'],
      gate: null
    },
    {
      id: 'development',
      orchestrator: 'dev-lead',
      members: ['backend', 'frontend', 'reviewers'],
      gate: 'AND: backend + frontend → reviewers'
    },
    {
      id: 'testing',
      orchestrator: 'qa-lead',
      members: ['qa', 'penetration'],
      gate: null
    }
  ];

  var events = run.events || [];

  // Пересобрать состояние конвейера на шаге index.
  function stateAt(index) {
    var agents = {};
    var phase = 'init';
    var complete = false;
    var gatesOpen = {};

    for (var i = 0; i <= index && i < events.length; i++) {
      var e = events[i];
      if (e.kind === 'phase_active' || e.kind === 'pipeline_start') {
        if (e.phase) phase = e.phase;
      } else if (e.kind === 'phase_advanced') {
        if (e.to) phase = e.to;
      } else if (e.kind === 'agent_triggered') {
        // "development/reviewers" — срабатывание AND-гейта фазы
        var parts = String(e.agent || '').split('/');
        if (parts.length === 2) gatesOpen[parts[0]] = true;
      } else if (e.kind === 'pipeline_complete') {
        complete = true;
      } else if (e.kind.indexOf('agent_') === 0) {
        var status = e.kind.slice('agent_'.length);
        if (e.agent && (status === 'done' || status === 'in-progress' || status === 'failed')) {
          agents[e.agent] = status;
        }
      }
      if (e.agents) {
        for (var k in e.agents) {
          if (e.agents[k] !== 'pending') agents[k] = e.agents[k];
        }
      }
    }
    return { agents: agents, phase: phase, complete: complete, gatesOpen: gatesOpen };
  }

  var phasesEl = document.getElementById('phases');
  var logEl = document.getElementById('log');
  var rangeEl = document.getElementById('range');
  var playEl = document.getElementById('play');
  var stepEl = document.getElementById('step');
  var resetEl = document.getElementById('reset');
  var counterEl = document.getElementById('counter');
  if (!phasesEl || !rangeEl) return;

  var cursor = 0;
  var timer = null;

  // Разметка фаз строится один раз, дальше меняются только классы.
  var agentNodes = {};
  PHASES.forEach(function (p) {
    var box = document.createElement('div');
    box.className = 'phase';
    box.dataset.phase = p.id;

    var head = document.createElement('div');
    head.className = 'phase-name';
    head.innerHTML = '<span>' + p.id + '</span>';
    box.appendChild(head);

    var list = document.createElement('div');
    list.className = 'agents';

    [p.orchestrator].concat(p.members).forEach(function (name, idx) {
      var row = document.createElement('div');
      row.className = 'agent' + (idx === 0 ? ' orchestrator' : '');
      row.innerHTML = '<span class="dot"></span><span>' + name + '</span>';
      list.appendChild(row);
      agentNodes[name] = row;
    });
    box.appendChild(list);

    if (p.gate) {
      var gate = document.createElement('div');
      gate.className = 'gate';
      gate.dataset.gate = p.id;
      gate.textContent = '⑂ ' + p.gate;
      box.appendChild(gate);
    }
    phasesEl.appendChild(box);
  });

  // Журнал событий
  events.forEach(function (e, i) {
    var row = document.createElement('div');
    row.className = 'log-row future k-' + e.kind;
    var label = e.agent || e.to || e.phase || '';
    var text = [label, e.note].filter(Boolean).join(' — ');
    row.innerHTML =
      '<span class="seq">' + e.seq + '</span>' +
      '<span class="kind">' + e.kind + '</span>' +
      '<span class="note">' + escapeHtml(text) + '</span>';
    row.addEventListener('click', function () { pause(); seek(i); });
    logEl.appendChild(row);
  });
  var logRows = logEl.querySelectorAll('.log-row');

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function render() {
    var st = stateAt(cursor);
    var activeIdx = PHASES.findIndex(function (p) { return p.id === st.phase; });

    PHASES.forEach(function (p, i) {
      var box = phasesEl.querySelector('[data-phase="' + p.id + '"]');
      var isActive = p.id === st.phase && !st.complete;
      var isComplete = st.complete || (activeIdx > -1 && i < activeIdx);
      box.classList.toggle('active', isActive);
      box.classList.toggle('complete', isComplete);

      var gate = box.querySelector('[data-gate]');
      if (gate) gate.classList.toggle('open', !!st.gatesOpen[p.id]);
    });

    Object.keys(agentNodes).forEach(function (name) {
      var node = agentNodes[name];
      node.classList.remove('in-progress', 'done', 'failed');
      var status = st.agents[name];
      if (status) node.classList.add(status);
    });

    for (var i = 0; i < logRows.length; i++) {
      logRows[i].classList.toggle('current', i === cursor);
      logRows[i].classList.toggle('future', i > cursor);
    }
    var cur = logRows[cursor];
    if (cur) {
      var top = cur.offsetTop - logEl.clientHeight / 2 + cur.clientHeight / 2;
      logEl.scrollTo({ top: top, behavior: 'smooth' });
    }

    rangeEl.value = String(cursor);
    counterEl.textContent = (cursor + 1) + ' / ' + events.length;
    stepEl.disabled = cursor >= events.length - 1;
  }

  function seek(i) {
    cursor = Math.max(0, Math.min(events.length - 1, i));
    render();
  }

  function pause() {
    if (timer) { clearInterval(timer); timer = null; }
    playEl.textContent = '▸ Играть';
  }

  function play() {
    if (cursor >= events.length - 1) cursor = 0;
    playEl.textContent = '❚❚ Пауза';
    timer = setInterval(function () {
      if (cursor >= events.length - 1) { pause(); render(); return; }
      cursor++;
      render();
    }, 320);
  }

  rangeEl.max = String(Math.max(0, events.length - 1));
  rangeEl.addEventListener('input', function () { pause(); seek(Number(rangeEl.value)); });
  playEl.addEventListener('click', function () { timer ? pause() : play(); });
  stepEl.addEventListener('click', function () { pause(); seek(cursor + 1); });
  resetEl.addEventListener('click', function () { pause(); seek(0); });

  document.addEventListener('keydown', function (e) {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === ' ') { e.preventDefault(); timer ? pause() : play(); }
    if (e.key === 'ArrowRight') { pause(); seek(cursor + 1); }
    if (e.key === 'ArrowLeft') { pause(); seek(cursor - 1); }
  });

  render();
})();
