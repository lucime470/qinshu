const $ = (id) => document.getElementById(id);
const BRANCHES = "子丑寅卯辰巳午未申酉戌亥";
let chart = null;
let selectedBird = null;
let currentLessonId = null;
let lessonSaving = false;

function nowLocal() {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

async function loadChart(event) {
  if (event) event.preventDefault();
  $("status").textContent = "起课中…";
  const payload = {datetime: $("datetime").value + ":00", timezone: "Asia/Shanghai"};
  if ($("longitude").value) payload.longitude = Number($("longitude").value);
  const res = await fetch("/api/chart", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
  const data = await res.json();
  if (!res.ok) { $("status").textContent = data.error?.message || "起课失败"; return; }
  if (!window.__birds) {
    const bl = await fetch("/api/birds");
    const bd = await bl.json();
    window.__birds = Object.fromEntries(bd.birds.map(b => [b.name, b]));
  }
  chart = data;
  selectedBird = null;
  currentLessonId = null;
  $("status").textContent = "";
  renderChart();
}

function renderChart() {
  const c = chart;
  chart.relations = chart.relations || {};
  chart.relations.suo_bo_facts = chart.relations.suo_bo_facts || {};
  chart.relations.suo_bo_facts.outer = chart.relations.suo_bo_facts.outer || {};
  chart.relations.xing_hai = chart.relations.xing_hai || {};
  chart.relations.strength = chart.relations.strength || {};
  chart.relations.fuduan = chart.relations.fuduan || {matched:false, hour_bird:null};
  chart.relations.suo_bo = chart.relations.suo_bo || {inner:{name:"—"}};
  chart.relations.suo_bo.inner = chart.relations.suo_bo.inner || {name:"—"};
  $("lunar").textContent = c.calendar.lunar_date + " · " + c.calendar.solar_term;
  $("pillars").innerHTML = Object.entries(c.calendar.four_pillars)
    .map(([k,v]) => `<span class="pillar">${{year:"年",month:"月",day:"日",hour:"时"}[k]}<b>${v}</b></span>`).join("");
  renderDial();
  renderSuoBoTabs();
  renderSuoBoDial();
  renderCards();
  renderChartTable();
  renderRelations();
  renderSolarVariant();
}

function sanheGroupOf(...names) {
  const groups = ["申子辰", "亥卯未", "寅午戌", "巳酉丑"];
  const palaces = names.map(name => window.__birds?.[name]?.palace).filter(Boolean);
  if (palaces.length !== names.length) return "";
  if (new Set(palaces).size < 2) return "";
  return groups.find(g => palaces.every(p => g.includes(p))) || "";
}
function relationEdge(rel, a, b) {
  if (rel === "我生") return {from: a, to: b, label: "生"};
  if (rel === "生我") return {from: b, to: a, label: "生"};
  if (rel === "我克") return {from: a, to: b, label: "克"};
  if (rel === "克我") return {from: b, to: a, label: "克"};
  return null;
}

function branchPalace(name) {
  return window.__birds?.[name]?.palace || "";
}

function renderRelations() {
  const c = chart;
  const r = c.relations;
  const self = r.self || c.birds.fan_qin;
  const other = r.other || c.birds.dao_jiang;
  const sk = r.sheng_ke || {};
  const facts = r.suo_bo_facts || {};
  const deDi = facts.de_di || {};

  const nodes = {
    self: {x: 130, y: 105, bird: self, role: "我禽", status: deDi.fan_qin},
    other: {x: 410, y: 105, bird: other, role: "他禽", status: deDi.dao_jiang},
  };
  const rel = sk.self_vs_other || "无直接生克";
  const edge = relationEdge(rel, "self", "other");
  const label = rel === "比和" ? "比和" : edge ? edge.label : "无直接生克";

  let svg = `<svg class="sheng-ke-diagram" viewBox="0 0 540 215" role="img" aria-label="彼我生克关系图">
    <defs>
      <marker id="arrow-sheng" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#3fb950"></path></marker>
      <marker id="arrow-ke" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#f85149"></path></marker>
      <marker id="arrow-even" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#8b949e"></path></marker>
    </defs>`;
  if (edge) {
    const a = nodes[edge.from], b = nodes[edge.to];
    const dx = b.x - a.x, dy = b.y - a.y;
    const len = Math.hypot(dx, dy) || 1;
    const ux = dx / len, uy = dy / len;
    const color = edge.label === "生" ? "#3fb950" : "#f85149";
    const marker = edge.label === "生" ? "arrow-sheng" : "arrow-ke";
    const startX = a.x + ux * 62, startY = a.y + uy * 52;
    const endX = b.x - ux * 62, endY = b.y - uy * 52;
    svg += `<line x1="${startX}" y1="${startY}" x2="${endX}" y2="${endY}" stroke="${color}" stroke-width="2" marker-end="url(#${marker})"></line>`;
    svg += `<text class="edge-label" x="${(startX + endX) / 2}" y="${(startY + endY) / 2 - 14}" fill="${color}">${edge.label}</text>`;
  } else {
    const a = nodes.self, b = nodes.other;
    svg += `<line x1="${a.x + 66}" y1="${a.y}" x2="${b.x - 66}" y2="${b.y}" stroke="#8b949e" stroke-width="1.6" stroke-dasharray="5 4"></line>`;
    svg += `<text class="edge-label" x="270" y="92" fill="#8b949e">${rel === "比和" ? "比和" : "无直接生克"}</text>`;
  }
  Object.values(nodes).forEach(n => {
    const strength = r.strength?.[n.bird]?.status || "—";
    const deDiStatus = n.status?.status || "—";
    svg += `<g class="node">
      <circle cx="${n.x}" cy="${n.y}" r="52"></circle>
      <text class="role" x="${n.x}" y="${n.y - 26}">${n.role}</text>
      <text class="name" x="${n.x}" y="${n.y - 4}">${escapeHtml(n.bird)}</text>
      <text class="palace" x="${n.x}" y="${n.y + 16}">${escapeHtml(branchPalace(n.bird) || "—")}宫 · ${escapeHtml(strength)}</text>
      <text class="palace" x="${n.x}" y="${n.y + 34}">${escapeHtml(deDiStatus)}</text>
    </g>`;
  });
  svg += `</svg>`;
  $("sheng-ke-diagram").innerHTML = svg;

  const hourXingHai = (facts.xing_hai || {}).hour || [];
  const xingHaiHtml = hourXingHai.length
    ? hourXingHai.map(x => `<div class="event-row"><span class="tag warn">刑害</span><span>${escapeHtml(x.text || "—")}${x.matched_target ? `（落${escapeHtml(x.matched_target)}）` : ""}</span></div>`).join("")
    : `<div class="event-row"><span class="tag">无</span><span>时禽未见刑害命中</span></div>`;

  const sanheRow = (label, hit, names) => {
    const group = hit ? sanheGroupOf(...names) : "";
    return `<div class="event-row">
      <span class="tag ${hit ? "good" : ""}">${hit ? "三合" : "不合"}</span>
      <span>${escapeHtml(label)}${hit ? `（${escapeHtml(group)}局）` : ""}</span>
    </div>`;
  };

  $("sanhe-box").innerHTML = `
    <div class="relation-box">
      <div class="relation-box-head">
        <h4>三合</h4>
        <h4>时禽刑害</h4>
      </div>
      <div class="relation-box-body">
        <div class="relation-col">
          ${sanheRow(`彼我：${self} · ${other}`, Boolean(r.sanhe), [self, other])}
          ${sanheRow(`日与彼我：${c.birds.day} · ${self} · ${other}`, Boolean(r.sanhe_with_day), [c.birds.day, self, other])}
          ${sanheRow(`日时翻禽：${c.birds.day} · ${c.birds.hour} · ${self}`, Boolean(r.day_time_sanhe), [c.birds.day, c.birds.hour, self])}
        </div>
        <div class="relation-col">${xingHaiHtml}</div>
      </div>
    </div>`;
}
const SUO_BO_ROLES = [
  ["day", "日禽"], ["hour", "时禽"], ["fan_qin", "翻禽"],
  ["dao_jiang", "倒将"], ["qi_jiang", "气将"], ["huo_yao", "活曜"],
];
let suoBoRole = "fan_qin";

function pointOn(cx, cy, r, angle) {
  return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
}

function sectorPath(cx, cy, rInner, rOuter, a0, a1) {
  const [x0, y0] = pointOn(cx, cy, rOuter, a0);
  const [x1, y1] = pointOn(cx, cy, rOuter, a1);
  const [x2, y2] = pointOn(cx, cy, rInner, a1);
  const [x3, y3] = pointOn(cx, cy, rInner, a0);
  return `M${x0},${y0} A${rOuter},${rOuter} 0 0 1 ${x1},${y1} L${x2},${y2} A${rInner},${rInner} 0 0 0 ${x3},${y3} Z`;
}

function renderSuoBoDial() {
  const c = chart;
  const role = SUO_BO_ROLES.find(x => x[0] === suoBoRole) || SUO_BO_ROLES[0];
  const key = role[0];
  const name = c.birds[key];
  const profile = window.__birds?.[name];
  const innerMap = profile?.suo_bo_dial?.inner || {};
  const outerMap = profile?.suo_bo_dial?.outer_columns || {};
  const outerByBranch = Object.fromEntries(
    Object.entries(outerMap).map(([column, branch]) => [branch, column])
  );
  const size = 600, cx = size / 2, cy = size / 2;
  const r0 = 78, r1 = 150, r2 = 222, r3 = 294;
  const branches = BRANCHES.split("");
  const step = Math.PI * 2 / 12;
  // 午在正上、子在正下，顺时针排布。
  const base = -Math.PI / 2 - step * 6.5;
  let out = `<svg class="suo-bo-dial" viewBox="0 0 ${size} ${size}" role="img" aria-label="${escapeHtml(name)}锁泊圆盘">`;
  out += `<circle class="ring" cx="${cx}" cy="${cy}" r="${r3}"></circle>`;
  out += `<circle class="boundary" cx="${cx}" cy="${cy}" r="${r2}"></circle>`;
  out += `<circle class="boundary" cx="${cx}" cy="${cy}" r="${r1}"></circle>`;
  branches.forEach((branch, i) => {
    const a0 = base + i * step, a1 = a0 + step;
    const mid = (a0 + a1) / 2;
    out += `<path class="sector" fill="transparent" d="${sectorPath(cx, cy, r0, r3, a0, a1)}" data-branch="${branch}"></path>`;
    const [bx, by] = pointOn(cx, cy, (r0 + r1) / 2, mid);
    out += `<text class="label branch" x="${bx}" y="${by + 5}">${branch}</text>`;
    const [ix, iy] = pointOn(cx, cy, (r1 + r2) / 2, mid);
    out += `<text class="label" x="${ix}" y="${iy + 5}">${escapeHtml(innerMap[branch] || "—")}</text>`;
    const [ox, oy] = pointOn(cx, cy, (r2 + r3) / 2, mid);
    out += `<text class="label" x="${ox}" y="${oy + 5}">${escapeHtml(outerByBranch[branch] || "—")}</text>`;
  });
  out += `<circle cx="${cx}" cy="${cy}" r="${r0 - 4}" fill="var(--card)" stroke="var(--line)"></circle>`;
  out += `</svg>`;
  $("suo-bo-dial").innerHTML = out;
}
function renderSuoBoTabs() {
  const c = chart;
  $("suo-bo-tabs").innerHTML = SUO_BO_ROLES.map(([key, label]) => {
    const name = c.birds[key];
    return `<button type="button" role="tab" data-role="${key}" class="${key === suoBoRole ? "active" : ""}" aria-selected="${key === suoBoRole}">${label} · ${escapeHtml(name)}</button>`;
  }).join("");
  $("suo-bo-tabs").querySelectorAll("button").forEach(el => {
    el.addEventListener("click", () => {
      suoBoRole = el.dataset.role;
      renderSuoBoTabs();
      renderSuoBoDial();
    });
  });
}

function renderDial() {
  const c = chart;
  const size = 620, cx = size/2, cy = size/2, rOuter = 252, rInner = 176;
  const branchOrder = BRANCHES.split("");
  const byBranch = {};
  branchOrder.forEach(b => byBranch[b] = []);
  const seen = new Set();
  Object.entries(c.birds).forEach(([key, name]) => {
    const profile = window.__birds?.[name];
    if (!profile) return;
    const dedupKey = profile.palace + ":" + name;
    if (seen.has(dedupKey)) return;
    seen.add(dedupKey);
    byBranch[profile.palace].push({key, name});
  });
  let out = `<svg class="dial" viewBox="0 0 ${size} ${size}" role="img" aria-label="十二宫圆盘">`;
  branchOrder.forEach((b, i) => {
    // 子时在正下方，顺钟向排：子、丑、寅……
    const a0 = (i * 30 - 105) * Math.PI/180, a1 = ((i+1) * 30 - 105) * Math.PI/180;
    const p = (r,a) => [cx + r*Math.cos(a), cy + r*Math.sin(a)];
    const [x0,y0] = p(rOuter,a0), [x1,y1] = p(rOuter,a1);
    const [x2,y2] = p(rInner,a1), [x3,y3] = p(rInner,a0);
    const [tx,ty] = p((rOuter+rInner)/2, (a0+a1)/2);
    out += `<path class="cell" d="M${x0},${y0} A${rOuter},${rOuter} 0 0 1 ${x1},${y1} L${x2},${y2} A${rInner},${rInner} 0 0 0 ${x3},${y3} Z" data-branch="${b}"></path>`;
    out += `<text class="branch" x="${tx}" y="${ty-20}" data-branch="${b}">${b}</text>`;
    byBranch[b].forEach((item, j) => {
      out += `<text class="bird" x="${tx}" y="${ty + j*18}" data-name="${item.name}" data-branch="${b}">${item.name}</text>`;
    });
  });
  out += `<circle cx="${cx}" cy="${cy}" r="${rInner-26}" fill="var(--card)" stroke="var(--line)"></circle>`;
  out += `<text x="${cx}" y="${cy-14}" text-anchor="middle" fill="var(--muted)" font-size="14">${c.yuan.name} · 第 ${c.yuan.day_index} 日</text>`;
  out += `<text x="${cx}" y="${cy+16}" text-anchor="middle" fill="var(--gold)" font-size="20" font-weight="800">${c.yuan.leader_bird}</text>`;
  out += `<text x="${cx}" y="${cy+42}" text-anchor="middle" fill="var(--muted)" font-size="12">元首禽</text>`;
  out += `</svg>`;
  $("dial").innerHTML = out;
  $("dial").querySelectorAll("text.bird").forEach(el => {
    el.addEventListener("click", () => selectBird(el.dataset.name));
  });
  $("dial").querySelectorAll("path.cell").forEach(el => {
    el.addEventListener("click", () => selectBranch(el.dataset.branch));
  });
  applyHighlight();
}
function renderSolarVariant() {
  const v = chart.calendar.solar_time_variant;
  if (!v) { $("solar-variant").innerHTML = ""; return; }
  const p = v.four_pillars;
  $("solar-variant").innerHTML = `
    <div class="box">
      <b>真太阳时对照</b>
      <span class="tag">经度 ${escapeHtml(v.longitude)}°E</span>
      <div class="small">${escapeHtml(v.local_time)} · ${escapeHtml(p.year)} ${escapeHtml(p.month)} ${escapeHtml(p.day)} ${escapeHtml(p.hour)}</div>
      <div class="hint">经度差 ${escapeHtml(v.longitude_minutes)} 分钟 · 均时差 ${escapeHtml(v.equation_minutes)} 分钟</div>
      <div class="hint">${escapeHtml(v.note)}</div>
    </div>`;
}

function renderCards() {
  const c = chart;
  const items = [
    ["七元", c.yuan.name, "gold", null],
    ["元内日序", c.yuan.day_index, "", null],
    ["日禽", c.birds.day, "", c.birds.day],
    ["时禽", c.birds.hour, "", c.birds.hour],
    ["气将", c.birds.qi_jiang, "", c.birds.qi_jiang],
    ["翻禽（我）", c.birds.fan_qin, "gold", c.birds.fan_qin],
    ["倒将（他）", c.birds.dao_jiang, "", c.birds.dao_jiang],
    ["活曜", c.birds.huo_yao, "", c.birds.huo_yao],
  ];
  $("cards").innerHTML = items.map(([k,v,cls,name]) =>
    `<div class="card${name ? " bird-card" : ""}"${name ? ` data-name="${name}"` : ""}><div class="k">${k}</div><div class="v ${cls}">${v}</div></div>`
  ).join("");
  const r = c.relations;
  const hourFact = r.suo_bo_facts.outer.hour || {column:"—", judgement:{label:null}};
  const cardBird = (name) => `<button type="button" class="v link" data-name="${escapeHtml(name)}">${escapeHtml(name)}</button>`;
  const relationCard = (label, names, body) => `<div class="card${names.length ? " relation-card" : ""}"${names.length ? ` data-names="${escapeHtml(names.join("|"))}"` : ""}><div class="k">${label}</div><div class="v">${body}</div></div>`;
  const rel = `
    <div class="card"><div class="k">彼我生克</div><div class="v">${r.sheng_ke.self_vs_other}</div></div>
    ${relationCard("我禽合", r.he, r.he.map(cardBird).join("、") || "—")}
    ${relationCard("我禽冲", r.chong, r.chong.map(cardBird).join("、") || "—")}
    <div class="card"><div class="k">内锁泊</div><div class="v">${r.suo_bo.inner.name}</div></div>
    <div class="card"><div class="k">时禽外锁泊</div><div class="v">${hourFact.column || "—"} · ${hourFact.judgement?.label || "—"}</div><div class="hint">${hourFact.de_di?.status || "—"}</div></div>
    <div class="card" data-fuduan="1"><div class="k">伏断</div><div class="v">${r.fuduan.matched ? "时禽逢伏断" : "不逢"}</div></div>
  `;
  $("cards").insertAdjacentHTML("beforeend", rel);
  $("cards").querySelectorAll(".bird-card").forEach(el => {
    el.addEventListener("click", () => selectBird(el.dataset.name));
  });
  $("cards").querySelectorAll("button.link[data-name]").forEach(el => {
    el.addEventListener("click", (event) => {
      event.stopPropagation();
      selectBird(el.dataset.name);
    });
  });
  $("cards").querySelectorAll(".relation-card[data-names]").forEach(el => {
    const names = el.dataset.names.split("|").filter(Boolean);
    if (names.length === 1) el.addEventListener("click", () => selectBird(names[0]));
  });
  if (!selectedBird) renderDetail(c.birds.fan_qin);
}

async function renderDetail(name) {
  const res = await fetch("/api/birds/" + encodeURIComponent(name));
  if (!res.ok) return;
  const b = await res.json();
  const fact = birdFact(name);
  const outer = fact?.outer;
  const xh = fact?.xingHai || [];
  const strength = chart.relations.strength?.[name];
  const fuduan = chart.relations.fuduan || {};
  $("detail").innerHTML = `
    <h3>${b.name}</h3>
    <span class="tag">${b.bird_code}</span><span class="tag">${b.seven_luminary}宿</span><span class="tag">${b.day_night}禽</span>
    ${strength ? `<span class="tag ${strength.status === "旺" ? "good" : "warn"}">${strength.season}·${strength.status}</span>` : ""}
    <dl>
      <dt>五行</dt><dd>${b.element === "日" ? "火（日同火）" : b.element === "月" ? "水（月同水）" : b.element}</dd>
      <dt>阴阳</dt><dd>${b.yinyang}</dd>
      <dt>宫位</dt><dd>${b.palace || "—"}</dd>
      <dt>合</dt><dd>${b.he.join("、") || "—"}</dd>
      <dt>冲</dt><dd>${b.chong.join("、") || "—"}</dd>
      <dt>外锁泊</dt><dd>${outer ? `${outer.column}宫（${outer.branch}支）` : "—"}</dd>
      <dt>锁泊吉凶</dt><dd>${outer ? `${outer.judgement.label || "—"} · ${outer.judgement.text}` : "—"}</dd>
      <dt>得地</dt><dd>${outer ? `${outer.de_di?.status || "—"}${outer.de_di?.label ? "（" + outer.de_di.label + "）" : ""}` : "—"}</dd>
      <dt>刑害</dt><dd>${xh.length ? xh.map(x => `${x.text}（${x.matched_target || "无具体宫位"}）`).join("；") : "未见命中"}</dd>
      <dt>伏断</dt><dd>${fuduan.matched && fuduan.hour_bird === name ? "时禽逢伏断" : "非时禽或未逢"}</dd>
    </dl>
    <div class="nature">${b.natures?.text || "本条禽性原文待补。"}</div>
  `;
}

function birdKey(name) {
  const map = {
    [chart.birds.day]:"day",
    [chart.birds.hour]:"hour",
    [chart.birds.qi_jiang]:"qi_jiang",
    [chart.birds.fan_qin]:"fan_qin",
    [chart.birds.dao_jiang]:"dao_jiang",
    [chart.birds.huo_yao]:"huo_yao",
  };
  return map[name] || null;
}

function birdFact(name) {
  const key = birdKey(name);
  if (!key) return null;
  const facts = chart.relations.suo_bo_facts;
  return {outer: facts?.outer?.[key], xingHai: facts?.xing_hai?.[key] || chart.relations.xing_hai?.[key] || []};
}

function renderChartTable() {
  const c = chart;
  const r = c.relations;
  const roles = [
    ["day", "日禽"],
    ["hour", "时禽"],
    ["qi_jiang", "气将"],
    ["fan_qin", "翻禽（我）"],
    ["dao_jiang", "倒将（他）"],
    ["huo_yao", "活曜"],
  ];
  const rows = roles.map(([key, label]) => {
    const name = c.birds[key];
    const profile = window.__birds?.[name] || {};
    const outer = r.suo_bo_facts.outer[key] || {};
    const judgement = outer.judgement || {};
    const feiFu = r.fei_fu?.[name] || "—";
    const strength = r.strength?.[name] || {};
    return `<tr>
      <td>${escapeHtml(label)}</td>
      <td><button class="link" type="button" data-name="${escapeHtml(name)}">${escapeHtml(name)}</button></td>
      <td>${escapeHtml(profile.seven_luminary || "—")}</td>
      <td>${escapeHtml(profile.palace || "—")}</td>
      <td>${escapeHtml(profile.day_night || "—")}</td>
      <td>${escapeHtml(feiFu)}</td>
      <td>${escapeHtml(outer.column || "—")}${outer.branch ? `（${escapeHtml(outer.branch)}）` : ""}</td>
      <td>${escapeHtml(judgement.label || "—")}</td>
      <td>${escapeHtml(outer.de_di?.status || "—")}</td>
      <td>${escapeHtml(strength.status || "—")}</td>
      <td>${escapeHtml((profile.he || []).join("、") || "—")}</td>
      <td>${escapeHtml((profile.chong || []).join("、") || "—")}</td>
    </tr>`;
  }).join("");
  const f = c.calendar.four_pillars;
  $("chart-table").innerHTML = `
    <table class="fact-table">
      <caption>${escapeHtml(f.year)} ${escapeHtml(f.month)} ${escapeHtml(f.day)} ${escapeHtml(f.hour)} · ${escapeHtml(c.calendar.solar_term)} · ${escapeHtml(c.yuan.name)}第 ${c.yuan.day_index} 日</caption>
      <thead><tr>
        <th>项目</th><th>禽星</th><th>七曜</th><th>本宫</th><th>昼夜</th><th>飞伏</th>
        <th>外锁泊</th><th>吉凶</th><th>得地</th><th>旺衰</th><th>合</th><th>冲</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
  $("chart-table").querySelectorAll("[data-name]").forEach(el => {
    el.addEventListener("click", () => selectBird(el.dataset.name));
  });
}

function selectBird(name) {
  selectedBird = name;
  applyHighlight();
  renderDetail(name);
}

function selectBranch(branch) {
  selectedBird = null;
  $("dial").querySelectorAll(".cell, .bird, .branch").forEach(el => el.classList.remove("hi"));
  $("dial").querySelectorAll(`[data-branch="${branch}"]`).forEach(el => el.classList.add("hi"));
  $("cards").querySelectorAll(".card").forEach(el => el.classList.remove("hi"));
  const names = [...$("dial").querySelectorAll(`text.bird[data-branch="${branch}"]`)].map(el => el.dataset.name);
  const dayBranch = chart.calendar.four_pillars.day[1];
  const facts = chart.relations.suo_bo_facts.outer;
  const outerHere = Object.values(facts).filter(x => x?.branch === branch);
  $("detail").innerHTML = `
    <h3>${branch}宫</h3>
    <span class="tag">圆盘宫位</span>
    <dl>
      <dt>本宫禽星</dt><dd>${names.join("、") || "本盘四课未落此宫"}</dd>
      <dt>内锁泊</dt><dd>${branch === dayBranch ? chart.relations.suo_bo.inner.name + "（当日日支）" : "—"}</dd>
      <dt>外锁泊落此宫</dt><dd>${outerHere.map(x => `${x.bird}（${x.column}）`).join("、") || "—"}</dd>
      <dt>锁泊说明</dt><dd>内锁泊只看当日日支；外锁泊按各禽七曜长生位顺数到用时。</dd>
    </dl>
    <p class="hint">点击左上角圆盘中的禽星，可回到禽星详情与刑害、锁泊吉凶。</p>
  `;
}

function applyHighlight() {
  const svg = $("dial");
  svg.querySelectorAll(".cell, .bird, .branch").forEach(el => el.classList.remove("hi"));
  $("cards").querySelectorAll(".card").forEach(el => el.classList.remove("hi"));
  if (!selectedBird) return;
  const profile = window.__birds?.[selectedBird];
  const fact = birdFact(selectedBird);
  $("cards").querySelectorAll(".card").forEach(el => {
    const names = (el.dataset.names || "").split("|").filter(Boolean);
    if (el.dataset.name === selectedBird || names.includes(selectedBird)) el.classList.add("hi");
  });
  svg.querySelectorAll("text.bird").forEach(el => {
    if (el.dataset.name === selectedBird) el.classList.add("hi");
  });
  if (profile?.palace) {
    svg.querySelectorAll(`path.cell[data-branch="${profile.palace}"]`).forEach(el => el.classList.add("hi"));
  }
  if (fact?.outer) {
    svg.querySelectorAll(`path.cell[data-branch="${fact.outer.branch}"]`).forEach(el => el.classList.add("hi"));
  }
}

async function loadCategories() {
  const res = await fetch("/api/categories");
  const data = await res.json();
  const options = data.categories.map(c => `<option value="${c.code}">${c.name}</option>`).join("");
  $("category").innerHTML = '<option value="">选择占类</option>' + options;
  $("lesson-category").innerHTML = '<option value="">全部占类</option>' + options;
}

function escapeHtml(text) {
  return String(text ?? "").replace(/[&<>"]/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[ch]));
}

async function showReading() {
  const code = $("category").value;
  if (!chart) return;
  if (!code) { $("reading").innerHTML = '<span class="reading-empty">请选择占类。</span>'; return; }
  const res = await fetch("/api/reading", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({chart, category_code: code, household: $("household").value}),
  });
  const data = await res.json();
  if (!res.ok) { $("reading").textContent = data.error?.message || "读取失败"; return; }
  const roles = data.role_map.roles.map(r => `
    <div class="role"><div class="k">${escapeHtml(r.role)}${r.note ? " · " + escapeHtml(r.note) : ""}</div><div class="v">${escapeHtml(r.bird || "—")}</div></div>
  `).join("");
  const secondary = data.role_map.secondary_roles.map(r => `
    <div class="role"><div class="k">${escapeHtml(r.role)}</div><div class="v">${escapeHtml(r.bird || "—")}</div></div>
  `).join("");
  const matched = data.matched_rules.length ? data.matched_rules.map(r => `
    <li>${escapeHtml(r.condition)} <span class="meaning">— ${escapeHtml(r.meaning)}</span></li>
  `).join("") : '<li class="meaning">本盘未命中可判定条件。</li>';
  const others = data.all_rules.filter(r => !r.matched).map(r => `
    <li>${escapeHtml(r.condition)} <span class="meaning">— ${escapeHtml(r.meaning)}</span></li>
  `).join("");
  $("reading").innerHTML = `
    <h3>${escapeHtml(data.category_name)}</h3>
    <div class="hint">出处：${escapeHtml(data.source_page)}</div>
    <h4>用神 · 演禽正传（主）</h4>
    <div class="role-grid">${roles}</div>
    <h4>用神 · 禽星易见（对照）</h4>
    <div class="role-grid">${secondary || '<div class="empty">该占类无对照条目。</div>'}</div>
    <h4>命中条件</h4>
    <ul class="rule-list">${matched}</ul>
    <h4>其余相关原文</h4>
    <ul class="rule-list">${others || '<li class="meaning">无。</li>'}</ul>
    <h4>原文</h4>
    ${data.original.primary.text ? `<div class="original"><b>演禽正传</b><br>${escapeHtml(data.original.primary.text)}</div>` : ""}
    ${data.original.secondary.text ? `<div class="original"><b>禽星易见</b><br>${escapeHtml(data.original.secondary.text)}</div>` : ""}
    ${data.conflicts.length ? `<div class="warning-item"><span class="tag warn">两书差异</span>${escapeHtml(data.conflicts[0].difference)}
      <ul class="rule-list">${(data.conflicts[0].role_comparison || []).map(x => `<li>${escapeHtml(x.primary)}：${escapeHtml(x.primary_bird || "—")} / ${escapeHtml(x.secondary)}：${escapeHtml(x.secondary_bird || "—")}</li>`).join("")}</ul>
    </div>` : ""}
  `;
}

async function saveLesson() {
  if (!chart) return;
  if (lessonSaving) return;
  lessonSaving = true;
  $("save-btn").disabled = true;
  try {
  const res = await fetch("/api/lessons", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      chart,
      category_code: $("category").value || null,
      judgement_text: $("judgement").value,
      notes: $("notes").value,
    }),
  });
  const data = await res.json();
  if (!res.ok) { $("status").textContent = data.error?.message || "保存失败"; return; }
  $("status").textContent = `已保存课例 #${data.id}`;
  currentLessonId = data.id;
  loadLessons();
  } finally {
    lessonSaving = false;
    $("save-btn").disabled = false;
  }
}

async function loadLessons() {
  const params = new URLSearchParams();
  const query = $("lesson-q").value.trim();
  const category = $("lesson-category").value;
  const from = $("lesson-from").value;
  const to = $("lesson-to").value;
  if (query) params.set("q", query);
  if (category) params.set("category_code", category);
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const res = await fetch("/api/lessons?" + params.toString());
  const data = await res.json();
  $("lessons").innerHTML = data.lessons.length ? data.lessons.map(item => `
    <div class="lesson-item">
      <div class="meta">
        <b>#${item.id} ${escapeHtml(item.lesson_time)}</b>
        <div class="small">${escapeHtml(item.four_pillars.year)} ${escapeHtml(item.four_pillars.month)} ${escapeHtml(item.four_pillars.day)} ${escapeHtml(item.four_pillars.hour)} · ${escapeHtml(item.day_bird || "")} / ${escapeHtml(item.fan_qin || "")}</div>
        <div>${escapeHtml(item.judgement_text || "")}</div>
      </div>
      <button class="btn" type="button" data-load="${item.id}">查看</button>
      <button class="btn danger" type="button" data-del="${item.id}">删除</button>
    </div>
  `).join("") : '<div class="empty">还没有课例。</div>';
  $("lessons").querySelectorAll("[data-load]").forEach(el => el.addEventListener("click", () => openLesson(el.dataset.load)));
  $("lessons").querySelectorAll("[data-del]").forEach(el => el.addEventListener("click", () => removeLesson(el.dataset.del)));
}

async function openLesson(id) {
  const res = await fetch("/api/lessons/" + id);
  const data = await res.json();
  if (!res.ok) return;
  chart = data.chart_snapshot;
  selectedBird = null;
  currentLessonId = data.id;
  $("judgement").value = data.judgement_text || "";
  $("notes").value = data.notes || "";
  $("category").value = data.category_code || "";
  $("datetime").value = (data.lesson_time || "").slice(0, 16);
  renderChart();
  $("status").textContent = `已载入课例 #${id}`;
}

async function removeLesson(id) {
  if (!confirm(`删除课例 #${id}？此操作不可撤销。`)) return;
  const res = await fetch("/api/lessons/" + id, {method: "DELETE"});
  if (res.ok) loadLessons();
}

function resetLessonFilters() {
  $("lesson-q").value = "";
  $("lesson-category").value = "";
  $("lesson-from").value = "";
  $("lesson-to").value = "";
  loadLessons();
}

$("datetime").value = nowLocal();
$("chart-form").addEventListener("submit", loadChart);
$("reading-btn").addEventListener("click", showReading);
$("save-btn").addEventListener("click", saveLesson);
$("lesson-search").addEventListener("click", loadLessons);
$("lesson-reset").addEventListener("click", resetLessonFilters);
loadCategories();
loadLessons();
loadChart();






