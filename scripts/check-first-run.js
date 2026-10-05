#!/usr/bin/env node
/**
 * 首次使用引导 · 状态探测 / 标记脚本
 *
 * 用法（agent 每次激活 skill 时调用）：
 *   node check-first-run.js         # 只读探测（不改文件）
 *   node check-first-run.js --mark  # 展示引导后调用，标记为已展示
 *
 * 退出码：0 正常 · 1 状态文件不可写（不阻塞问答）
 * 输出：JSON 到stdout
 */
const fs = require('fs');
const path = require('path');
const os = require('os');

const SKILL = '达芬奇21中文操作手册';
const stateDir = path.join(os.homedir(), '.workbuddy', 'skills', '.state');
const stateFile = path.join(stateDir, SKILL + '.json');
const MARK = process.argv.includes('--mark');

// --topic "<主题关键词>"：记录本轮主题，供下轮判定是否追问（跨会话也有效）
const topicIdx = process.argv.indexOf('--topic');
const TOPIC = topicIdx > -1 ? (process.argv[topicIdx + 1] || '') : '';

function emit(obj, code) {
  process.stdout.write(JSON.stringify(obj, null, 2) + '\n');
  process.exit(code === undefined ? 0 : code);
}

// ---------- 0) 若传了 --topic，先记录本轮主题（供下轮判定追问） ----------
if (TOPIC) {
  let t = {};
  try {
    const o = JSON.parse(fs.readFileSync(stateFile, 'utf-8'));
    if (o && typeof o === 'object' && !Array.isArray(o)) t = o;
  } catch (e) { t = {}; }
  const arr = Array.isArray(t.recentTopics) ? t.recentTopics : [];
  t.recentTopics = [TOPIC].concat(arr.filter(x => x !== TOPIC)).slice(0, 3);
  try {
    fs.mkdirSync(stateDir, { recursive: true });
    fs.writeFileSync(stateFile, JSON.stringify(t, null, 2) + '\n', 'utf-8');
  } catch (e) { /* 不可写不阻塞 */ }
}

// ---------- 1) 读状态（不exit，交给末尾统一处理） ----------
let state = null;
let probe = null;          // 探测结果
let readable = true;

try {
  if (fs.existsSync(stateFile)) {
    const raw = fs.readFileSync(stateFile, 'utf-8');
    try {
      state = JSON.parse(raw);
      if (state === null || typeof state !== 'object' || Array.isArray(state)) {
        probe = { isFirstRun: true, reason: '状态文件内容不是对象，按首次处理' };
      }
    } catch (e) {
      probe = { isFirstRun: true, reason: '状态文件 JSON 损坏，按首次处理：' + e.message };
    }
  } else {
    probe = { isFirstRun: true, reason: '状态文件不存在（首次安装 / 已被删除）' };
  }
} catch (e) {
  readable = false;
  probe = { isFirstRun: true, reason: '状态文件读取失败，按首次处理：' + e.message };
}

if (!probe) {
  // 解析成功且是对象 → 判定
  const isFirst = state.firstRunShown !== true;  // 只有严格 true 才算已展示
  probe = {
    isFirstRun: isFirst,
    reason: isFirst ? 'firstRunShown 不为 true' : 'firstRunShown=true，已展示过，跳过引导'
  };
}

const base = {
  isFirstRun: probe.isFirstRun,
  stateFile,
  reason: probe.reason,
  flowOverviewShown: state ? state.flowOverviewShown === true : false,
  flowDetailedShown: state ? state.flowDetailedShown === true : false,
  useCount: state ? (Number(state.useCount) || 0) : 0,
  lastUsedAt: state ? (state.lastUsedAt || null) : null,
  firstRunShownAt: state ? (state.firstRunShownAt || null) : null,
  recentTopics: state && Array.isArray(state.recentTopics) ? state.recentTopics : []
};

// ---------- 2) 只读模式：直接返回 ----------
if (!MARK) {
  emit(Object.assign({ writable: true }, base), 0);
}

// ---------- 3) 标记模式：更新并写回 ----------
let cur = {};
if (readable) {
  try {
    const raw = fs.readFileSync(stateFile, 'utf-8');
    const o = JSON.parse(raw);
    if (o && typeof o === 'object' && !Array.isArray(o)) cur = o;
  } catch (e) { cur = {}; }
}

const now = new Date().toISOString();
const next = Object.assign({
  skill: SKILL,
  schemaVersion: 1,
  firstRunShown: false,
  flowOverviewShown: false,
  flowDetailedShown: false,
  useCount: 0
}, cur, {
  firstRunShown: true,
  flowOverviewShown: true,
  firstRunShownAt: cur.firstRunShownAt || now,
  flowOverviewShownAt: cur.flowOverviewShownAt || now,
  lastUsedAt: now,
  useCount: (Number(cur.useCount) || 0) + 1,
  note: 'firstRunShown=true 表示首次引导已展示，后续会话不再重弹。删除本文件即恢复为「首次」。'
});

try {
  fs.mkdirSync(stateDir, { recursive: true });
  fs.writeFileSync(stateFile, JSON.stringify(next, null, 2) + '\n', 'utf-8');
  emit({ ok: true, marked: true, stateFile, state: next }, 0);
} catch (e) {
  emit({ ok: false, marked: false, stateFile,
         error: '状态写入失败（目录只读或权限不足）：' + e.message,
         hint: '本次引导已展示，但下次可能重复展示。可提示用户手动创建该文件。' }, 1);
}
