/* Trắc nghiệm tiếng Hàn v1.4 — ES5 strict cho WebView cũ */
(function () {
'use strict';

var $ = function (id) { return document.getElementById(id); };
var TICKER_URL = 'https://notepad.pw/fetch/tracnghiemhan';
var ZALO_URL = 'https://zalo.me/0345140889';

var LEVELS = [
  { id: 1, badge: 'SƠ CẤP 1', name: 'Nhập môn', desc: 'Chào hỏi, gia đình, số đếm, thời gian. Ngữ pháp cơ bản nhất.', color: '#4f6df5' },
  { id: 2, badge: 'SƠ CẤP 2', name: 'Căn bản', desc: 'Du lịch, mua sắm, thời tiết, công việc. Câu dài hơn.', color: '#0ea5e9' },
  { id: 3, badge: 'TRUNG CẤP 1', name: 'Giao tiếp', desc: 'Văn hóa, môi trường, sức khỏe. Hội thoại tự nhiên.', color: '#10b981' },
  { id: 4, badge: 'TRUNG CẤP 2', name: 'Thành thạo', desc: 'Kinh tế, xã hội, tin tức. Tranh luận & ý kiến.', color: '#f59e0b' },
  { id: 5, badge: 'CAO CẤP 1', name: 'Học thuật', desc: 'Từ Hán-Hàn, bài giảng, phỏng vấn chuyên gia.', color: '#a855f7' },
  { id: 6, badge: 'CAO CẤP 2', name: 'Bản xứ', desc: 'Thành ngữ, tục ngữ, xã luận. Đỉnh cao TOPIK 6.', color: '#ef4444' }
];
var SKILL_NAME = { nghe: '🎧 Nghe', doc: '📖 Đọc', both: '🎲 Cả hai' };
var SUB_NAME = { tuvung: 'Từ vựng', hoithoai: 'Hội thoại', doanvan: 'Đoạn văn', nguphap: 'Ngữ pháp', dochieu: 'Đọc hiểu' };

/* ---------- dữ liệu ---------- */
var DBKEY = 'kortest_v1';
var DB = { settings: { theme: false, autoplay: true, sound: true, ui: { layout: 'list', style: 'default', color: 'blue' } }, best: {}, stats: { tests: 0, answered: 0, correct: 0 }, wrong: [] };
try {
  var raw = localStorage.getItem(DBKEY);
  if (raw) { var d = JSON.parse(raw); if (d && d.settings) DB = d; }
} catch (e) {}
DB.best = DB.best || {};
DB.stats = DB.stats || { tests: 0, answered: 0, correct: 0 };
DB.stats.tests = DB.stats.tests || 0; DB.stats.answered = DB.stats.answered || 0; DB.stats.correct = DB.stats.correct || 0;
DB.wrong = DB.wrong || [];
function saveDB() { try { localStorage.setItem(DBKEY, JSON.stringify(DB)); } catch (e) {} }

/* ---------- giao diện v1.3: layout / style / color, lưu 1 key JSON ---------- */
var UI_LAYOUTS = [
  { id: 'list', name: '📋 Danh sách', desc: 'Mỗi câu một hàng đầy đủ, dễ đọc nhất' },
  { id: 'grid', name: '🔲 Dạng lưới', desc: 'Các câu xếp ô vuông cạnh nhau' },
  { id: 'compact', name: '🗜️ Compact', desc: 'Hàng gọn, chữ nhỏ, xem được nhiều câu' }
];
var UI_STYLES = [
  { id: 'default', name: '🎨 Mặc định', desc: 'Giữ nguyên phong cách hiện tại của app' },
  { id: 'ios', name: '🍎 iOS', desc: 'Bo tròn lớn, bóng đổ nhẹ, màu tươi' },
  { id: 'android', name: '🤖 Android', desc: 'Material Design, nút ấn có phản hồi' }
];
var UI_COLORS = [
  { id: 'blue', name: 'Xanh dương', c: '#4f6df5' },
  { id: 'green', name: 'Xanh lá', c: '#16a34a' },
  { id: 'purple', name: 'Tím', c: '#8b5cf6' },
  { id: 'orange', name: 'Cam', c: '#f97316' },
  { id: 'pink', name: 'Hồng', c: '#ec4899' },
  { id: 'dark', name: 'Tối', c: '#1f2637', bd: '#9aa3c7' }
];
function uiValid(list, id) {
  var i;
  for (i = 0; i < list.length; i++) if (list[i].id === id) return id;
  return null;
}
/* đọc lựa chọn giao diện, luôn trả về bộ hợp lệ (migrate dữ liệu cũ) */
function getUI() {
  var u = (DB.settings && DB.settings.ui && typeof DB.settings.ui === 'object') ? DB.settings.ui : {};
  return {
    layout: uiValid(UI_LAYOUTS, u.layout) || 'list',
    style: uiValid(UI_STYLES, u.style) || 'default',
    color: uiValid(UI_COLORS, u.color) || 'blue'
  };
}
function setUI(key, val) {
  var u = getUI();
  if (u[key] === val) return; /* đã chọn rồi thì thôi */
  u[key] = val;
  DB.settings.ui = u;
  saveDB();
  applyTheme();
  beep(true);
  var names = { layout: 'Kiểu hiển thị', style: 'Phong cách', color: 'Màu chủ đạo' };
  toast('✅ Đã đổi ' + (names[key] || 'giao diện') + '!');
}
function applyTheme() {
  var u = getUI();
  var cls = 'layout-' + u.layout + ' color-' + u.color;
  if (u.style !== 'default') cls += ' style-' + u.style;
  /* màu "Tối" luôn là dark mode; công tắc "Giao diện tối" cũ vẫn ép dark cho mọi màu */
  if (u.color === 'dark' || DB.settings.theme) cls += ' dark';
  document.body.className = cls;
  var t = $('set-theme'); t.textContent = DB.settings.theme ? 'BẬT' : 'TẮT'; t.className = 'toggle' + (DB.settings.theme ? ' on' : '');
  var a = $('set-autoplay'); a.textContent = DB.settings.autoplay ? 'BẬT' : 'TẮT'; a.className = 'toggle' + (DB.settings.autoplay ? ' on' : '');
  var s = $('set-sound'); s.textContent = DB.settings.sound ? 'BẬT' : 'TẮT'; s.className = 'toggle' + (DB.settings.sound ? ' on' : '');
  renderThemeScreen();
}
/* preview nhỏ cho từng tùy chọn (CSS/emoji có sẵn, không ảnh ngoài) */
function pvInner(group, id) {
  if (group === 'layout') {
    if (id === 'grid') return '<i></i><i></i><i></i><i></i>';
    if (id === 'compact') return '<i></i><i></i><i></i><i></i><i></i>';
    return '<i></i><i></i>';
  }
  if (group === 'style') return '<i>Nút</i>';
  return '';
}
function renderThemeOpts(elId, group, items, cur) {
  var el = $(elId);
  if (!el) return;
  var html = '', i, it;
  for (i = 0; i < items.length; i++) {
    it = items[i];
    html += '<button class="theme-opt' + (it.id === cur ? ' on' : '') + '" data-ui-group="' + group + '" data-ui-val="' + it.id + '">' +
      '<span class="pv pv-' + group + '-' + it.id + '">' + pvInner(group, it.id) + '</span>' +
      '<span class="to-body"><b>' + it.name + '</b><span>' + it.desc + '</span></span>' +
      '<span class="to-check">✓</span></button>';
  }
  el.innerHTML = html;
}
function renderThemeScreen() {
  var u = getUI();
  renderThemeOpts('theme-layout', 'layout', UI_LAYOUTS, u.layout);
  renderThemeOpts('theme-style', 'style', UI_STYLES, u.style);
  var el = $('theme-color');
  if (!el) return;
  var html = '', i, c;
  for (i = 0; i < UI_COLORS.length; i++) {
    c = UI_COLORS[i];
    html += '<button class="theme-color' + (c.id === u.color ? ' on' : '') + '" data-ui-group="color" data-ui-val="' + c.id + '">' +
      '<span class="sw" style="background:' + c.c + (c.bd ? ';border-color:' + c.bd : '') + '"></span><span>' + c.name + '</span></button>';
  }
  el.innerHTML = html;
}
function bindThemeScreen() {
  var scr = $('scr-theme');
  if (!scr) return;
  /* dùng cả click và touchend để nhạy trên mọi WebView, dedup bằng timestamp */
  var lastTap = 0;
  function onTap(e) {
    var now = Date.now();
    if (now - lastTap < 300) return;
    var el = e.target;
    while (el && el !== scr) {
      if (el.getAttribute && el.getAttribute('data-ui-val')) {
        lastTap = now;
        try { e.preventDefault(); } catch (err) {}
        setUI(el.getAttribute('data-ui-group'), el.getAttribute('data-ui-val'));
        return;
      }
      el = el.parentNode;
    }
  }
  scr.addEventListener('click', onTap);
}

function esc(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function shuffle(arr) {
  var a = arr.slice(), i, j, t;
  for (i = a.length - 1; i > 0; i--) { j = Math.floor(Math.random() * (i + 1)); t = a[i]; a[i] = a[j]; a[j] = t; }
  return a;
}
function fmtTime(sec) {
  var m = Math.floor(sec / 60), s = sec % 60;
  return (m < 10 ? '0' + m : m) + ':' + (s < 10 ? '0' + s : s);
}

/* ---------- điều hướng ---------- */
var hist = ['home'];
function show(id) {
  var secs = document.querySelectorAll('.screen'), i;
  for (i = 0; i < secs.length; i++) secs[i].className = 'screen' + (secs[i].id === 'scr-' + id ? ' active' : '');
  if (hist[hist.length - 1] !== id) hist.push(id);
  if (id === 'home') { renderHome(); checkDonateReminder(); }
  window.scrollTo(0, 0);
}
function goBack() {
  if (hist.length > 1) { hist.pop(); var prev = hist[hist.length - 1]; hist.pop(); show(prev); return true; }
  return false;
}
window.__systemBack = function () {
  var cur = hist[hist.length - 1];
  if (cur === 'quiz') { exitQuiz(); return true; }
  if (cur === 'review') { goBack(); return true; }
  return goBack();
};
document.addEventListener('click', function (e) {
  var el = e.target;
  while (el && el !== document) {
    if (el.getAttribute && el.getAttribute('data-go')) { beep(); show(el.getAttribute('data-go')); return; }
    el = el.parentNode;
  }
});

/* ---------- âm thanh nhỏ ---------- */
var AC = null;
function beep(ok) {
  if (!DB.settings.sound) return;
  try {
    AC = AC || new (window.AudioContext || window.webkitAudioContext)();
    var o = AC.createOscillator(), g = AC.createGain();
    o.connect(g); g.connect(AC.destination);
    o.frequency.value = ok === true ? 880 : (ok === false ? 220 : 520);
    g.gain.value = 0.06; o.start();
    setTimeout(function () { try { o.stop(); } catch (e) {} }, 120);
  } catch (e) {}
}

/* ---------- trang chủ ---------- */
function levelName(id) { return LEVELS[id - 1].badge + ' · ' + LEVELS[id - 1].name; }
function renderHome() {
  var all = (typeof QT === 'object' && QT) ? QT : {};
  var total = 0, k;
  for (k in all) { if (all.hasOwnProperty(k) && all[k] && all[k].length) total += all[k].length; }
  $('home-total').textContent = (total || 10042) + ' câu hỏi';
  $('home-done').textContent = (DB.stats.tests || 0) + ' đề đã làm';
  var acc = DB.stats.answered ? Math.round(100 * DB.stats.correct / DB.stats.answered) : 0;
  $('home-stats').textContent = 'Đã trả lời ' + DB.stats.answered + ' câu · đúng ' + acc + '%';
  var nw = DB.wrong.length;
  $('home-wrong-count').textContent = nw ? nw + ' câu cần ôn lại' : 'Chưa có — làm bài để ghi nhận câu sai';
  $('btn-wrong').disabled = !nw;
  /* thẻ "bài đang làm dở" */
  var p = getPaused(), rc = $('resume-card');
  if (p && p.qids && p.qids.length) {
    var pdone = 0, pi;
    for (pi = 0; pi < p.ans.length; pi++) if (p.ans[pi] >= 0) pdone++;
    $('resume-info').textContent = levelName(p.level) + ' · ' + SKILL_NAME[p.skill] +
      ' — đã làm ' + pdone + '/' + p.qids.length + ' câu · ' + fmtTime(p.elapsed || 0);
    rc.style.display = 'flex';
  } else {
    rc.style.display = 'none';
  }
  var html = '', i, L;
  for (i = 0; i < LEVELS.length; i++) {
    L = LEVELS[i];
    var qs = all[L.id] || [];
    var nghe = 0, doc = 0, j;
    for (j = 0; j < qs.length; j++) { if (qs[j].skill === 'nghe') nghe++; else doc++; }
    var b1 = DB.best[L.id + '_nghe'], b2 = DB.best[L.id + '_doc'], b3 = DB.best[L.id + '_both'];
    var bestTxt = 'Chưa làm đề nào';
    var bests = [];
    if (b1) bests.push('🎧' + b1.pct + '%');
    if (b2) bests.push('📖' + b2.pct + '%');
    if (b3) bests.push('🎲' + b3.pct + '%');
    if (bests.length) bestTxt = 'Kỷ lục: ' + bests.join(' · ');
    var bpct = Math.max(b1 ? b1.pct : 0, b2 ? b2.pct : 0, b3 ? b3.pct : 0);
    var circ = 100.5, off = (circ * (1 - bpct / 100)).toFixed(1);
    var ring = '<span class="lv-ring"><svg viewBox="0 0 40 40"><circle class="rr-bg" cx="20" cy="20" r="16"/><circle class="rr-fg" cx="20" cy="20" r="16" stroke-dasharray="' + circ + '" stroke-dashoffset="' + off + '" style="stroke:' + L.color + '"/></svg>' + (bpct ? '<i>' + bpct + '%</i>' : '') + '</span>';
    html += '<button class="level-card" data-level="' + L.id + '" style="--lc:' + L.color + '">' + ring +
      '<span class="lv-badge">' + L.badge + '</span><h4>' + L.name + '</h4>' +
      '<div class="lv-desc">' + L.desc + '</div>' +
      '<div class="lv-count">🎧 ' + nghe + ' câu nghe · 📖 ' + doc + ' câu đọc</div>' +
      '<div class="lv-best">' + bestTxt + '</div></button>';
  }
  $('level-grid').innerHTML = html;
  var cards = $('level-grid').querySelectorAll('.level-card'), c;
  for (c = 0; c < cards.length; c++) {
    cards[c].addEventListener('click', function () { beep(); openSetup(parseInt(this.getAttribute('data-level'), 10)); });
  }
  $('btn-wrong').onclick = function () { beep(); openWrong(); };
  $('btn-resume').onclick = function () { beep(); resumeQuiz(); };
  $('btn-resume-drop').onclick = function () { beep(); clearPaused(); renderHome(); toast('Đã bỏ bài làm dở.'); };
}

/* ---------- chọn đề ---------- */
var setup = { level: 1, skill: 'nghe', num: 10 };
function openSetup(level) {
  setup.level = level; setup.skill = 'nghe'; setup.num = 10;
  $('setup-title').textContent = '📝 ' + levelName(level);
  segSet('skill-seg', 'skill', 'nghe');
  segSet('num-seg', 'num', '10');
  updateSetupHint();
  show('setup');
}
function segSet(segId, key, val) {
  var btns = $(segId).querySelectorAll('button'), i;
  for (i = 0; i < btns.length; i++) {
    var on = (key === 'skill' ? btns[i].getAttribute('data-skill') : btns[i].getAttribute('data-num')) === String(val);
    btns[i].className = on ? 'on' : '';
  }
}
function updateSetupHint() {
  var all = (QT && QT[setup.level]) || [];
  var n = 0, i;
  for (i = 0; i < all.length; i++) {
    if (setup.skill === 'both' || all[i].skill === setup.skill) n++;
  }
  $('setup-count-hint').textContent = 'Ngân hàng đề ' + SKILL_NAME[setup.skill] + ' cấp độ này có ' + n + ' câu. Hệ thống sẽ chọn ngẫu nhiên ' + Math.min(setup.num, n) + ' câu.';
}
(function bindSetup() {
  var sb = $('skill-seg').querySelectorAll('button'), i;
  for (i = 0; i < sb.length; i++) sb[i].addEventListener('click', function () {
    setup.skill = this.getAttribute('data-skill'); segSet('skill-seg', 'skill', setup.skill); beep(); updateSetupHint();
  });
  var nb = $('num-seg').querySelectorAll('button');
  for (i = 0; i < nb.length; i++) nb[i].addEventListener('click', function () {
    setup.num = parseInt(this.getAttribute('data-num'), 10); segSet('num-seg', 'num', setup.num); beep(); updateSetupHint();
  });
  $('btn-start').addEventListener('click', function () { beep(); startQuiz(); });
})();

/* ---------- làm bài ---------- */
var G = null, timerId = null, curAudio = null;
window.__quizState = function () { return G; }; /* hook cho kiểm thử */
/* Tạm dừng / làm tiếp: lưu bài đang làm dở vào localStorage */
var PAUSE_KEY = 'kortest_paused_v1';
function savePaused() {
  if (!G || G.practice) return;
  try {
    localStorage.setItem(PAUSE_KEY, JSON.stringify({
      level: G.level, skill: G.skill,
      qids: G.qs.map(function (q) { return q.id; }),
      ans: G.ans, idx: G.idx, elapsed: G.elapsed, savedAt: Date.now()
    }));
  } catch (e) {}
}
function clearPaused() { try { localStorage.removeItem(PAUSE_KEY); } catch (e) {} }
function getPaused() {
  try { var r = localStorage.getItem(PAUSE_KEY); return r ? JSON.parse(r) : null; }
  catch (e) { return null; }
}
function startTimer() {
  clearInterval(timerId);
  timerId = setInterval(function () {
    if (!G) return;
    G.elapsed = Math.floor((Date.now() - G.t0) / 1000);
    $('quiz-timer').textContent = fmtTime(G.elapsed);
  }, 1000);
}
function resumeQuiz() {
  var p = getPaused();
  if (!p || !p.qids || !p.qids.length) { toast('Không có bài làm dở nào.'); return; }
  var all = (QT && QT[p.level]) || [], map = {}, i;
  for (i = 0; i < all.length; i++) map[all[i].id] = all[i];
  var pool = [];
  for (i = 0; i < p.qids.length; i++) if (map[p.qids[i]]) pool.push(map[p.qids[i]]);
  if (!pool.length) { clearPaused(); toast('Bài làm dở không còn hợp lệ.'); renderHome(); return; }
  setup.level = p.level; setup.skill = p.skill; setup.num = pool.length;
  G = {
    level: p.level, skill: p.skill, qs: pool,
    idx: Math.min(p.idx || 0, pool.length - 1),
    ans: (p.ans || []).slice(0, pool.length),
    t0: Date.now() - (p.elapsed || 0) * 1000, elapsed: p.elapsed || 0
  };
  for (i = G.ans.length; i < pool.length; i++) G.ans.push(-1);
  $('quiz-title').textContent = '📝 ' + levelName(p.level) + ' (làm tiếp)';
  show('quiz');
  renderQ();
  startTimer();
  toast('Chào mừng quay lại! Làm tiếp câu ' + (G.idx + 1) + ' nhé ⏯️');
}
function startQuiz() {
  var all = (QT && QT[setup.level]) || [];
  var pool = [], i;
  for (i = 0; i < all.length; i++) {
    if (setup.skill === 'both' || all[i].skill === setup.skill) pool.push(all[i]);
  }
  if (!pool.length) { alert('Chưa có câu hỏi cho phần này.'); return; }
  pool = shuffle(pool).slice(0, Math.min(setup.num, pool.length));
  G = { level: setup.level, skill: setup.skill, qs: pool, idx: 0, ans: [], t0: Date.now(), elapsed: 0 };
  for (i = 0; i < pool.length; i++) G.ans.push(-1);
  clearPaused(); /* đề mới thay thế bài dở cũ (nếu có) */
  $('quiz-title').textContent = '📝 ' + levelName(setup.level);
  show('quiz');
  renderQ();
  startTimer();
}
function stopAudio() {
  try { if (curAudio) { curAudio.pause(); curAudio = null; } } catch (e) {}
}
function renderQ() {
  stopAudio();
  var q = G.qs[G.idx], i;
  $('q-count').textContent = 'Câu ' + (G.idx + 1) + '/' + G.qs.length;
  $('q-skill').textContent = (q.skill === 'nghe' ? '🎧 Nghe' : '📖 Đọc') + (SUB_NAME[q.sub] ? ' · ' + SUB_NAME[q.sub] : '');
  var done = 0;
  for (i = 0; i < G.ans.length; i++) if (G.ans[i] >= 0) done++;
  $('q-answered').textContent = 'Đã làm: ' + done + '/' + G.qs.length;
  $('qprogress-fill').style.width = (100 * (G.idx + 1) / G.qs.length) + '%';
  $('q-audio-row').style.display = q.skill === 'nghe' ? 'flex' : 'none';
  if (q.passage) { $('q-passage').style.display = 'block'; $('q-passage').textContent = q.passage; }
  else { $('q-passage').style.display = 'none'; }
  $('q-prompt').textContent = q.prompt;
  var html = '';
  for (i = 0; i < q.options.length; i++) {
    html += '<button class="qopt' + (G.ans[G.idx] === i ? ' sel' : '') + '" data-opt="' + i + '">' +
      '<span class="k">' + 'ABCD'[i] + '.</span> ' + esc(q.options[i]) + '</button>';
  }
  $('q-options').innerHTML = html;
  var opts = $('q-options').querySelectorAll('.qopt');
  for (i = 0; i < opts.length; i++) {
    opts[i].addEventListener('click', function () {
      G.ans[G.idx] = parseInt(this.getAttribute('data-opt'), 10);
      beep();
      var os = $('q-options').querySelectorAll('.qopt'), k;
      for (k = 0; k < os.length; k++) os[k].className = 'qopt' + (k === G.ans[G.idx] ? ' sel' : '');
      var d = 0, j;
      for (j = 0; j < G.ans.length; j++) if (G.ans[j] >= 0) d++;
      $('q-answered').textContent = 'Đã làm: ' + d + '/' + G.qs.length;
      savePaused();
    });
  }
  if (q.skill === 'nghe' && q.audio && DB.settings.autoplay) playAudio(q);
}
function playAudio(q) {
  stopAudio();
  try {
    curAudio = new Audio('audio/' + q.audio);
    curAudio.addEventListener('error', function () { toast('🔇 Không tải được audio cho câu này.'); });
    var p = curAudio.play();
    if (p && p.catch) p.catch(function () {});
  } catch (e) {}
}
$('btn-replay').addEventListener('click', function () {
  if (G) { beep(); playAudio(G.qs[G.idx]); }
});
/* Điều hướng chống kẹt v1.4: validate idx, tự bỏ qua câu lỗi, không bao giờ đứng yên */
var navLock = 0, suppressClick = false;
function safeRenderQ() {
  try { renderQ(); return true; }
  catch (e) { return false; }
}
function slideCard(d) {
  try {
    var card = $('quiz-card');
    card.classList.remove('slide-l', 'slide-r');
    void card.offsetWidth;
    card.classList.add(d < 0 ? 'slide-r' : 'slide-l');
  } catch (e) {}
}
function goQ(d) {
  if (!G || !G.qs || !G.qs.length) return;
  var now = Date.now();
  if (now - navLock < 250) return; /* chống double-fire khi chạm 2 lần */
  navLock = now;
  /* sanitize idx: chống NaN hoặc out-of-range làm kẹt */
  var cur = parseInt(G.idx, 10);
  if (isNaN(cur) || cur < 0) cur = 0;
  if (cur >= G.qs.length) cur = G.qs.length - 1;
  var n = cur + d;
  if (n < 0) n = 0;
  if (n >= G.qs.length) n = G.qs.length - 1;
  if (n === cur) return;
  /* thử render, tự động bỏ qua câu bị lỗi theo hướng di chuyển — không bao giờ kẹt */
  var target = n, attempts = 0;
  while (attempts < G.qs.length) {
    G.idx = target;
    if (safeRenderQ()) break;
    target += d;
    if (target < 0 || target >= G.qs.length) break;
    attempts++;
  }
  if (attempts >= G.qs.length || !safeRenderQ()) {
    G.idx = cur;
    safeRenderQ();
    toast('Không mở được câu hỏi, bạn thử lại nhé.');
    return;
  }
  try { beep(); } catch (e) {}
  slideCard(d);
  savePaused();
  try { window.scrollTo(0, 0); } catch (e) {}
}
/* Nút Trước/Sau: chỉ dùng click (đơn giản, ổn định), navLock chống chạm đúp */
function bindNav(id, d) {
  var el = $(id);
  el.addEventListener('click', function (e) {
    try { e.preventDefault(); } catch (err) {}
    goQ(d);
  });
}
bindNav('btn-prev', -1);
bindNav('btn-next', 1);
/* Vuốt trái/phải: Pointer Events (chuột + chạm), fallback Touch Events */
(function swipe() {
  var card = $('quiz-card'), sx = 0, sy = 0, pid = null, active = false;
  function dn(x, y, id) { sx = x; sy = y; pid = id; active = true; suppressClick = false; }
  function up(x, y, id) {
    if (!active || (id !== undefined && id !== pid)) return;
    active = false;
    if (!G) return;
    var dx = x - sx, dy = y - sy;
    if (Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy) * 1.6) {
      suppressClick = true; /* chặn click ma ngay sau vuốt */
      goQ(dx < 0 ? 1 : -1);
    }
  }
  if (window.PointerEvent) {
    card.addEventListener('pointerdown', function (e) { dn(e.clientX, e.clientY, e.pointerId); });
    card.addEventListener('pointerup', function (e) { up(e.clientX, e.clientY, e.pointerId); });
    card.addEventListener('pointercancel', function () { active = false; });
  } else {
    card.addEventListener('touchstart', function (e) { var t = e.changedTouches[0]; dn(t.clientX, t.clientY); }, { passive: true });
    card.addEventListener('touchend', function (e) { var t = e.changedTouches[0]; up(t.clientX, t.clientY); }, { passive: true });
  }
  /* Chặn đúng 1 synthetic click bắn nhầm vào đáp án của câu mới ngay sau khi vuốt;
     chạm thật tiếp theo luôn bắt đầu bằng pointerdown/touchstart nên không bị ảnh hưởng */
  document.addEventListener('click', function (e) {
    if (suppressClick) {
      suppressClick = false;
      var t = e.target;
      if (t && t.closest && t.closest('.qopt')) { e.stopPropagation(); e.preventDefault(); }
    }
  }, true);
})();
function exitQuiz() {
  if (!G) { goBack(); return; }
  if (G.practice) {
    if (confirm('Thoát bài luyện? Kết quả chưa nộp sẽ bị mất.')) {
      stopAudio(); clearInterval(timerId); G = null; goBack();
    }
    return;
  }
  /* tự động lưu bài làm dở để lần sau vào làm tiếp */
  savePaused();
  stopAudio(); clearInterval(timerId); G = null;
  /* dọn hist để nút back hệ thống không quay lại màn quiz đã hủy */
  while (hist.length && hist[hist.length - 1] !== 'home') hist.pop();
  show('home');
  toast('Đã lưu bài làm dở — lần sau vào làm tiếp nhé ⏸️');
}
$('quiz-exit').addEventListener('click', exitQuiz);
$('btn-submit').addEventListener('click', function () {
  if (!G) return;
  var un = 0, i;
  for (i = 0; i < G.ans.length; i++) if (G.ans[i] < 0) un++;
  if (un > 0 && !confirm('Còn ' + un + ' câu chưa trả lời. Nộp bài?')) return;
  submitQuiz();
});
function submitQuiz() {
  stopAudio(); clearInterval(timerId);
  clearPaused(); /* đã nộp bài thì xóa bản lưu dở */
  var ok = 0, i;
  for (i = 0; i < G.qs.length; i++) if (G.ans[i] === G.qs[i].answer) ok++;
  var total = G.qs.length, pct = Math.round(100 * ok / total);
  var key = G.level + '_' + G.skill;
  var isBest = false;
  if (!G.practice) {
    var prev = DB.best[key];
    isBest = !prev || pct > prev.pct || (pct === prev.pct && G.elapsed < prev.time);
    if (isBest) DB.best[key] = { pct: pct, score: ok + '/' + total, time: G.elapsed, date: new Date().toLocaleDateString('vi-VN') };
  }
  DB.stats.tests = (DB.stats.tests || 0) + 1;
  DB.stats.answered += total;
  DB.stats.correct += ok;
  /* kho câu hay sai: thêm câu sai, luyện đúng thì xóa */
  var seen = {}, w, wi, qq;
  for (w = 0; w < DB.wrong.length; w++) seen[DB.wrong[w].id] = 1;
  for (wi = 0; wi < total; wi++) {
    qq = G.qs[wi];
    if (G.ans[wi] !== qq.answer) {
      if (!seen[qq.id]) { DB.wrong.push({ id: qq.id, q: qq }); seen[qq.id] = 1; }
    } else if (G.practice && seen[qq.id]) {
      DB.wrong = DB.wrong.filter(function (x) { return x.id !== qq.id; });
      seen[qq.id] = 0;
    }
  }
  if (DB.wrong.length > 300) DB.wrong = DB.wrong.slice(DB.wrong.length - 300);
  saveDB();
  $('res-score').textContent = ok + '/' + total;
  $('res-pct').textContent = pct + '%';
  var msg = pct >= 90 ? '🏆 Xuất sắc! Bạn đỉnh thật đấy!' :
            pct >= 70 ? '🎉 Rất tốt! Cố thêm chút nữa!' :
            pct >= 50 ? '💪 Khá đấy! Ôn thêm nhé!' : '📚 Đừng nản! Làm lại để tiến bộ nhé!';
  $('res-msg').textContent = msg + (isBest ? ' (Kỷ lục mới!)' : '');
  $('res-time').textContent = fmtTime(G.elapsed);
  $('res-ok').textContent = ok;
  $('res-bad').textContent = total - ok;
  $('res-best').textContent = G.practice ? '—' : DB.best[key].pct + '%';
  var ring = document.querySelector('.score-ring');
  ring.style.background = 'conic-gradient(var(--acc) ' + pct + '%, var(--line) ' + pct + '%)';
  if (pct >= 70) confetti();
  beep(pct >= 50);
  show('result');
  /* popup ủng hộ dễ chịu sau khi nộp bài (tối đa 2 tiếng/lần) */
  if (!G.practice && shouldShowDonate()) {
    setTimeout(function () { showDonatePopup(); }, 1200);
  }
}
$('btn-retry').addEventListener('click', function () { beep(); if (G && G.practice) startPractice(); else startQuiz(); });

/* ---------- câu hay sai ---------- */
function openWrong() { renderWrong(); show('wrong'); }
function renderWrong() {
  var n = DB.wrong.length;
  $('wrong-sub').textContent = n ? 'Bạn có ' + n + ' câu thường sai. Luyện lại để nhớ lâu hơn!' : 'Tuyệt vời! Chưa có câu nào bị sai.';
  $('wrong-practice').style.display = n ? 'block' : 'none';
  $('wrong-clear').style.display = n ? 'block' : 'none';
  var html = '', i, w;
  for (i = 0; i < Math.min(n, 100); i++) {
    w = DB.wrong[i];
    html += '<div class="wrow"><span class="wtag">' + (w.q.skill === 'nghe' ? '🎧' : '📖') + ' ' + (SUB_NAME[w.q.sub] || '') + '</span><span class="wtxt">' + esc(w.q.prompt) + '</span></div>';
  }
  if (n > 100) html += '<div class="muted center">…và ' + (n - 100) + ' câu nữa</div>';
  $('wrong-list').innerHTML = html || '<div class="muted center">Chưa có câu nào.</div>';
}
function startPractice() {
  if (!DB.wrong.length) { toast('Chưa có câu hay sai nào.'); return; }
  var pool = shuffle(DB.wrong.map(function (w) { return w.q; })).slice(0, 50);
  G = { level: 0, skill: 'practice', practice: true, qs: pool, idx: 0, ans: [], t0: Date.now(), elapsed: 0 };
  var i; for (i = 0; i < pool.length; i++) G.ans.push(-1);
  $('quiz-title').textContent = '📝 Luyện câu hay sai';
  show('quiz');
  safeRenderQ();
  startTimer();
}
$('wrong-back').addEventListener('click', function () { beep(); goBack(); });
$('wrong-practice').addEventListener('click', function () { beep(); startPractice(); });
$('wrong-clear').addEventListener('click', function () {
  if (confirm('Xóa hết các câu hay sai?')) { DB.wrong = []; saveDB(); renderWrong(); toast('Đã xóa.'); }
});

/* ---------- xem đáp án ---------- */
$('btn-review').addEventListener('click', function () { beep(); renderReview(); show('review'); });
$('review-back').addEventListener('click', function () { goBack(); });
function renderReview() {
  var html = '', i, j, q, ua;
  for (i = 0; i < G.qs.length; i++) {
    q = G.qs[i]; ua = G.ans[i];
    var good = ua === q.answer;
    var subTxt = SUB_NAME[q.sub] ? ' · ' + SUB_NAME[q.sub] : '';
    html += '<div class="rev ' + (good ? 'ok' : 'bad') + '">' +
      '<div class="rq">Câu ' + (i + 1) + ' ' + (q.skill === 'nghe' ? '🎧' : '📖') + subTxt + ' ' + (good ? '✅' : '❌') + '<br>' + esc(q.prompt) + '</div>';
    if (q.passage) html += '<div class="rpass">' + esc(q.passage) + '</div>';
    if (q.skill === 'nghe' && q.audio) html += '<div class="raudio"><button class="mbtn ghost audio-btn" data-audio="' + q.audio + '">🔊 Nghe lại</button></div>';
    for (j = 0; j < q.options.length; j++) {
      var cls = 'ropt';
      if (j === q.answer) cls += ' correct';
      else if (j === ua) cls += ' wrong';
      html += '<div class="' + cls + '">' + 'ABCD'[j] + '. ' + esc(q.options[j]) + '</div>';
    }
    html += '<div class="rexp">💡 ' + esc(q.explain) + '</div></div>';
  }
  $('review-list').innerHTML = html;
  var btns = $('review-list').querySelectorAll('[data-audio]'), b;
  for (b = 0; b < btns.length; b++) {
    btns[b].addEventListener('click', function () {
      stopAudio();
      try {
        curAudio = new Audio('audio/' + this.getAttribute('data-audio'));
        curAudio.addEventListener('error', function () { toast('🔇 Không tải được audio cho câu này.'); });
        var p = curAudio.play(); if (p && p.catch) p.catch(function () {});
      } catch (e) {}
    });
  }
}

/* ---------- confetti ---------- */
function confetti() {
  var c = $('confetti'), x;
  try { x = c.getContext('2d'); } catch (e) { x = null; }
  if (!x) return;
  c.style.display = 'block'; c.width = window.innerWidth; c.height = window.innerHeight;
  var colors = ['#4f6df5', '#7c5cf0', '#f59e0b', '#10b981', '#ef4444', '#fde047'], ps = [], i;
  for (i = 0; i < 130; i++) ps.push({ x: Math.random() * c.width, y: -20 - Math.random() * c.height * 0.4, w: 6 + Math.random() * 7, h: 8 + Math.random() * 8, vy: 2 + Math.random() * 3.5, vx: -1.5 + Math.random() * 3, rot: Math.random() * 6.28, vr: -0.15 + Math.random() * 0.3, col: colors[i % colors.length] });
  var t0 = Date.now();
  (function anim() {
    var el = Date.now() - t0, j;
    x.clearRect(0, 0, c.width, c.height);
    for (j = 0; j < ps.length; j++) {
      var p = ps[j]; p.x += p.vx; p.y += p.vy; p.rot += p.vr;
      x.save(); x.translate(p.x, p.y); x.rotate(p.rot); x.fillStyle = p.col; x.fillRect(-p.w / 2, -p.h / 2, p.w, p.h); x.restore();
    }
    if (el < 3000) requestAnimationFrame(anim); else c.style.display = 'none';
  })();
}

/* ---------- ticker ---------- */
function loadTicker() {
  try {
    var xhr = new XMLHttpRequest();
    xhr.timeout = 8000;
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4 && xhr.status === 200) {
        var txt = (xhr.responseText || '').replace(/\s+/g, ' ').replace(/^\s+|\s+$/g, '');
        if (txt) $('ticker-text').textContent = '📢 ' + txt;
      }
    };
    xhr.open('GET', TICKER_URL, true);
    xhr.send();
  } catch (e) {}
}

/* ---------- donate / about ---------- */
function copyText(t) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(t); return true; }
  } catch (e) {}
  try {
    var ta = document.createElement('textarea');
    ta.value = t; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    var ok = document.execCommand('copy');
    document.body.removeChild(ta); return ok;
  } catch (e) { return false; }
}
function toast(msg) {
  var d = $('toast');
  if (!d) {
    d = document.createElement('div');
    d.id = 'toast'; d.className = 'toast';
    document.body.appendChild(d);
  }
  d.textContent = msg;
  d.classList.add('show');
  clearTimeout(d._h);
  d._h = setTimeout(function () { d.classList.remove('show'); }, 2200);
}
$('btn-copy-acct').addEventListener('click', function () {
  beep();
  toast(copyText('0345140889') ? '📋 Đã sao chép số tài khoản!' : 'Không sao chép được, STK: 0345140889');
});
$('btn-zalo2').addEventListener('click', function () { beep(); try { window.open(ZALO_URL, '_blank'); } catch (e) {} });
$('btn-zalo3').addEventListener('click', function () { beep(); try { window.open(ZALO_URL, '_blank'); } catch (e) {} });

/* ---------- popup ủng hộ v1.4: hiện sau khi nộp bài, nhắc lại mỗi 2 tiếng ---------- */
var DONATE_KEY = 'kortest_donate_prompt_v1';
function getDonatePromptTime() {
  try { return parseInt(localStorage.getItem(DONATE_KEY) || '0', 10) || 0; }
  catch (e) { return 0; }
}
function setDonatePromptTime() {
  try { localStorage.setItem(DONATE_KEY, String(Date.now())); } catch (e) {}
}
function shouldShowDonate() {
  /* hiện nếu chưa từng hiện, hoặc đã qua 2 tiếng từ lần hiện trước */
  return Date.now() - getDonatePromptTime() > 2 * 60 * 60 * 1000;
}
function showDonatePopup() {
  setDonatePromptTime();
  var ov = document.createElement('div');
  ov.className = 'donate-overlay';
  ov.innerHTML =
    '<div class="donate-popup">' +
    '<div class="donate-emoji">❤️</div>' +
    '<h3>Cảm ơn bạn đã học!</h3>' +
    '<p class="muted">Bạn thấy app hữu ích chứ? Ủng hộ mình một ly cà phê để mình làm thêm nhiều đề hay nữa nhé! ☕</p>' +
    '<button class="mbtn" id="donate-go">❤️ Ủng hộ ngay</button>' +
    '<button class="mbtn ghost" id="donate-later">Để sau</button>' +
    '</div>';
  document.body.appendChild(ov);
  $('donate-go').addEventListener('click', function () {
    beep();
    document.body.removeChild(ov);
    show('donate');
  });
  $('donate-later').addEventListener('click', function () {
    beep();
    try { ov.classList.add('hide'); } catch (e) {}
    setTimeout(function () { try { document.body.removeChild(ov); } catch (e) {} }, 300);
    toast('Cảm ơn bạn! Hẹn gặp lại sau 2 tiếng nhé 😊');
  });
  /* chạm ra ngoài cũng đóng */
  ov.addEventListener('click', function (e) {
    if (e.target === ov) {
      try { document.body.removeChild(ov); } catch (err) {}
    }
  });
}
/* kiểm tra nhắc ủng hộ mỗi 2 tiếng: kiểm tra khi về trang chủ (tiết kiệm pin hơn setInterval) */
function checkDonateReminder() {
  try {
    if (shouldShowDonate() && (DB.stats.tests || 0) > 0 && !document.querySelector('.donate-overlay')) {
      showDonatePopup();
    }
  } catch (e) {}
}

/* ---------- cài đặt ---------- */
$('set-theme').addEventListener('click', function () { DB.settings.theme = !DB.settings.theme; saveDB(); applyTheme(); beep(); });
$('set-autoplay').addEventListener('click', function () { DB.settings.autoplay = !DB.settings.autoplay; saveDB(); applyTheme(); beep(); });
$('set-sound').addEventListener('click', function () { DB.settings.sound = !DB.settings.sound; saveDB(); applyTheme(); beep(); });
$('btn-reset').addEventListener('click', function () {
  if (confirm('Xóa toàn bộ tiến độ và kỷ lục?')) {
    DB = { settings: DB.settings, best: {}, stats: { tests: 0, answered: 0, correct: 0 }, wrong: [] };
    saveDB(); renderHome(); toast('Đã xóa dữ liệu.');
  }
});

/* ---------- khởi động ---------- */
bindThemeScreen();
applyTheme();
renderHome();
loadTicker();
})();
