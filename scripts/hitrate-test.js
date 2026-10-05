#!/usr/bin/env node
/**
 * 问句命中率回归测试
 *
 * 用法（词典改动后必跑）：
 *   node scripts/hitrate-test.js          # 跑全部测试集
 *   node scripts/hitrate-test.js --verbose# 打印未命中明细
 *
 * 测试集分两档：
 *   A. 规范术语问句（应接近 100%）
 *   B. 小白白话问句（描述不清/ 只说现象 / 用错词）
 *
 * 判定逻辑与 SKILL.md「升级触发判定」一致：
 *   问句归一化（三层词典）→ 取核心词 → 查各资产 → 命中即算成功
 */
const fs = require('fs');
const path = require('path');
const os = require('os');

const SKILL_DIR = path.join(os.homedir(), '.workbuddy', 'skills', '达芬奇21中文操作手册');
const REF = path.join(SKILL_DIR, 'references');
const VERBOSE = process.argv.includes('--verbose');

// ---------- 加载三层词典 ----------
function loadDict(file) {
  const m = {};
  const p = path.join(REF, file);
  if (!fs.existsSync(p)) return m;
  for (const line of fs.readFileSync(p, 'utf-8').split('\n')) {
    if (line.trim().startsWith('#') || !line.trim()) continue;
    if (file === '实战路由表.txt') {
      // 该表用 Tab 分隔，且结构是「关键词 ⇥ 章节 ⇥ 同义词...」（与其它词典相反）
      const t = line.split('\t').map(x => x.trim()).filter(Boolean);
      if (t.length < 2) continue;
      m[t[0]] = { val: t[1], tgt: t.slice(2).join(' ') };   // val=章节，tgt=同义词
      // 同义词也建索引，便于同义词直接命中
      for (let i = 2; i < t.length; i++) m[t[i]] = { val: t[1], tgt: t[0] };
      continue;
    }
    if (!line.includes('⇥')) continue;
    const parts = line.split('⇥');
    m[parts[0].trim()] = { val: parts[1].trim(), tgt: (parts[2] || '').trim() };
  }
  return m;
}

const pheno = loadDict('小白现象词典.txt');   // ①
const spoken = loadDict('口语问句映射.txt');  // ②
const termEn = loadDict('实战术语对照.txt');  // ③
const routeCn = loadDict('实战路由表.txt');  // ③

// ---------- 真实用户问句（来自状态文件 recentTopics） ----------
const STATE_DIR = path.join(os.homedir(), '.workbuddy', 'skills', '.state');
const STATE_FILE = path.join(STATE_DIR, '达芬奇21中文操作手册.json');
let realTopics = [];
try {
  if (fs.existsSync(STATE_FILE)) {
    const st = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
    if (Array.isArray(st.recentTopics)) realTopics = st.recentTopics;
  }
} catch (e) { /* 状态损坏不影响测试 */ }

// ---------- 待查资产 ----------
const ASSETS = [
  '高频速查.md', 'shortcuts.md', 'quickref.json',
  'Resolve_FX中英对照.md', 'Fairlight音频插件.md',
  'index_terms.txt', 'chapters.txt',
  '实战术语对照.txt', '实战路由表.txt', '实战技巧蒸馏-油管博主.md',
  '开源插件清单.md', '官方开发文档蒸馏.md',
  '21.1原文检索.txt', '21.1英文原文检索.txt'
].filter(f => fs.existsSync(path.join(REF, f)));

// 预载小文件到内存（1MB 以下），大文件走 grep
const CACHE = new Map();
const SMALL_MAX = 1024 * 1024;
const mem = new Map();
for (const f of ASSETS) {
  const fp = path.join(REF, f);
  const sz = fs.statSync(fp).size;
  if (sz <= SMALL_MAX) mem.set(f, fs.readFileSync(fp, 'utf-8'));
}

function assetHit(word) {
  if (!word) return false;
  const w = word.toLowerCase();
  for (const f of ASSETS) {
    if (mem.has(f)) {
      if (mem.get(f).toLowerCase().includes(w)) return true;
    } else {
      try {
        const out = require('child_process').execSync(
          'grep -c -F -- "' + word.replace(/"/g, '\\"') + '" "' + path.join(REF, f) + '"',
          { encoding: 'utf-8', timeout: 8000 });
        if (parseInt(out.trim(), 10) > 0) return true;
      } catch (e) { /* grep 无匹配返回 1 */ }
    }
  }
  return false;
}

// 判定是否「需澄清」条目——词典里可能写成 '需澄清' 或 '需澄清:请用户描述…'
function isClarify(val, tgt) {
  const a = String(val || '');
  const b = String(tgt || '');
  return a.includes('需澄清') || b.includes('需澄清') ||
         a === '澄清' || b === '澄清';
}

function expand(val) {
  return val.replace(/→/g, ' ').replace(/\//g, ' ').replace(/，/g, ' ')
    .split(/\s+/).filter(x => x && x !== '删' && x !== '-');
}

/** 模拟 agent 的归一化 + 检索流程 */
function resolve(q) {
  // 整句精确
  if (pheno[q]) {
    const { val, tgt } = pheno[q];
    if (isClarify(val, tgt)) return { ok: true, via: '需澄清反问' };
    const cs = expand(val);
    if (cs.some(assetHit)) return { ok: true, via: '①整句' };
  }
  if (spoken[q]) {
    const cs = expand(spoken[q].val);
    if (cs.some(assetHit)) return { ok: true, via: '②整句' };
  }
  // 滑窗 12→2，长词优先
  for (let L = 12; L >= 2; L--) {
    for (let i = 0; i + L <= q.length; i++) {
      const seg = q.slice(i, i + L);
      let e = pheno[seg] || spoken[seg] || termEn[seg] || routeCn[seg];
      if (!e) continue;
      const val = e.val !== undefined ? e.val : e;
      if (isClarify(e.val, e.tgt)) return { ok: true, via: '需澄清反问' };
      const cs = expand(val);
      if (cs.length && cs.some(assetHit)) return { ok: true, via: '滑窗' };
      // 片段本身若已是资产里的术语（英文缩写/产品名），直接算命中
      if (/^[A-Za-z][A-Za-z0-9_.\s-]{1,}$/.test(seg) && assetHit(seg.trim())) {
        return { ok: true, via: '英文术语' };
      }
    }
  }
  // 兜底：抽词后查（中文词 + 英文词/术语，中英混合问句要能取到）
  const zh = q.match(/[\u4e00-\u9fff]{2,}/g) || [];
  const en = q.match(/[A-Za-z][A-Za-z0-9_.]{1,}/g) || [];
  if (zh.some(assetHit) || en.some(assetHit)) return { ok: true, via: '直查' };
  return { ok: false, via: '' };
}

// ---------- 测试集 ----------
const SET_A = [
  '怎么调速', '怎么重置参数', '关键帧在哪', '怎么导出',
  '示波器', '一级校色', '二级调色', '节点图', '跟踪器',
  '字幕', '混音', '降噪', '响度', 'LUT', 'DCTL',
  '快捷键', 'Mac快捷键', 'Studio专属', '离线渲染',
  '色彩管理', 'ACES', 'RCM', 'HDR', 'Dolby Vision', 'Rec.709',
  'Fusion', 'Magic Mask', '转场', '蒙版', '代理媒体',
  'TimelineItem怎么设速度', 'Python怎么建项目', 'MCP怎么控制Resolve',
  '自动字幕', '批量渲染', '智能重构图', '人声隔离'
];

const SET_B = [
  // 描述不清 / 只说现象
  '我录的声音一会大一会小', '画面灰蒙蒙的没精神', '人声被音乐盖住了',
  '怎么去掉沙沙声', '串起来的那个树是干嘛的', '颜色很脏',
  '前面那个镜头特别黄后面那个特别蓝', '人脸特别红', '画面太灰怎么调',
  // 用错词 / 口语
  '怎么存成文件', '那个按钮在哪', '这个东西在哪一页', '怎么用滤镜',
  '怎么对轴', '怎么抠像', '怎么导出', '变声', '有没有免费插件',
  '装了不生效', '免费版能装插件吗', '怎么拼两段视频', '代理文件怎么设置',
  // 说不清（应转为澄清，也算"处理成功"）
  '就是那个一整条', '不知道怎么说', '反正就是不对', '别人都能弄我不行',
  // 跳跃式
  '怎么加字幕', '画面发灰', '字幕颜色能改吗', '插件怎么装', 'DCTL怎么装',
  '怎么调色', '怎么调色快一点', '人声太吵怎么办', '底噪好大',
  '齿音好重', '人声不清晰', '怎么让声音变亮'
];

function run(name, set) {
  let ok = 0;
  const miss = [];
  const via = {};
  for (const q of set) {
    const r = resolve(q);
    if (r.ok) { ok++; via[r.via] = (via[r.via] || 0) + 1; }
    else miss.push(q);
  }
  const pct = (ok / set.length * 100).toFixed(1);
  console.log(`\n【${name}】 ${ok}/${set.length} = ${pct}%`);
  console.log('  命中路径:', JSON.stringify(via));
  if (miss.length) {
    console.log(`  未命中 ${miss.length} 条:`);
    miss.forEach(q => console.log('    ❌ ' + q));
  }
  return { ok, total: set.length, pct, miss };
}

console.log('='.repeat(60));
console.log('问句命中率回归测试');
console.log('='.repeat(60));
console.log('词典: 小白现象' + Object.keys(pheno).length +
  ' / 口语问句' + Object.keys(spoken).length +
  ' / 中英术语' + Object.keys(termEn).length +
  ' / 实战路由' + Object.keys(routeCn).length);
console.log('资产:', ASSETS.length, '个（内存预载 ' + mem.size + '）');

const a = run('A 规范术语问句', SET_A);
const b = run('B 小白白话问句', SET_B);

console.log('\n' + '='.repeat(60));
const all = a.ok + b.ok, tot = a.total + b.total;
console.log(`总计: ${all}/${tot} = ${(all / tot * 100).toFixed(1)}%`);
// ---------- 真实问句覆盖检查 ----------
if (realTopics.length) {
  const rows = realTopics.map(t => ({ t, r: resolve(String(t).split('-').pop() || t) }));
  const unhit = rows.filter(x => !x.r.ok);
  console.log('\n' + '-'.repeat(60));
  console.log('真实问句覆盖（来自 recentTopics，' + rows.length + ' 条）:');
  rows.forEach(x => console.log('  ' + (x.r.ok ? '\u2705' : '\u274c') + ' ' + x.t + (x.r.ok ? '  via ' + x.r.via : '')));
  if (unhit.length) {
    console.log('\n\u26a0\ufe0f 真实问句未命中 ' + unhit.length + ' 条 \u2192 建议补进词典:');
    unhit.forEach(x => console.log('    ' + x.t));
  } else {
    console.log('\u2705 真实问句全部命中');
  }
} else {
  console.log('\n（暂无 recentTopics \u2014\u2014 skill 尚未被实际使用过，或未记录 --topic）');
}

console.log('\n' + '-'.repeat(60));
console.log('词典规模: 小白现象 ' + Object.keys(pheno).length +
  ' / 口语问句 ' + Object.keys(spoken).length +
  ' / 中英术语 ' + Object.keys(termEn).length +
  ' / 实战路由 ' + Object.keys(routeCn).length);
console.log('（记录新问法：node scripts/check-first-run.js --topic "域-对象"）');

const warn = (r, label) => {
  if (r.pct < 95) console.log(`⚠️${label} 命中率 ${r.pct}% (< 95%)，建议补词典`);
  else console.log(`✅ ${label} 命中率 ${r.pct}%`);
};
warn(a, '术语问句');
warn(b, '白话问句');
console.log('='.repeat(60));
