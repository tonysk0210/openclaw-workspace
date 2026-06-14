// search_104_semi.mjs - 半自動流程第一步：搜尋職缺，存 pending_jobs.json，產出清單+詳細CSV
// 獨立腳本，不污染原先的 scrape_104_api.mjs
// 已投遞紀錄存於 data/apply_log.json，搜尋時自動過濾已投職缺
import { writeFileSync, existsSync, readFileSync, mkdirSync } from 'fs';

const CDP_URL = 'http://127.0.0.1:18800';
const WS_PATH = '/Users/anthonyshangkuan/.nvm/versions/node/v24.13.1/lib/node_modules/openclaw/node_modules/ws/index.js';
const PENDING_FILE = '/Users/anthonyshangkuan/.openclaw/workspace/projects/104-apply-semi/data/pending_jobs.json';
const LOG_FILE = '/Users/anthonyshangkuan/.openclaw/workspace/projects/104-apply-semi/data/apply_log.json';

const KEYWORD = process.argv[2] || 'Java';
const COUNT = parseInt(process.argv[3]) || 10;

// 排序條件（第4個參數）: 符合度高(預設) | 最新更新 | 薪資最高
const ORDER_MAP = {
  '符合度高': 14,
  '最新更新': 1,
  '薪資最高': 2,
  '工作經歷': 7,
};
const ORDER_LABEL = process.argv[4] || '符合度高';
const ORDER = ORDER_MAP[ORDER_LABEL] ?? 14;

// Output to date folder on Desktop (local time)
const _now = new Date();
const _MM = String(_now.getMonth() + 1).padStart(2, '0');
const _DD = String(_now.getDate()).padStart(2, '0');
const TODAY = `${_now.getFullYear()}-${_MM}-${_DD}`;
const DATE_DIR = process.env.HOME + `/Desktop/${_MM}-${_DD}`;
try { mkdirSync(DATE_DIR, { recursive: true }); } catch {}

const keepAlive = setInterval(() => process.stdout.write('.\n'), 20000);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function getCDPTarget() {
  const r = await fetch(`${CDP_URL}/json`);
  const targets = await r.json();
  const page = targets.find(t => t.type === 'page');
  if (!page) throw new Error('No page target');
  return page.webSocketDebuggerUrl;
}

class CDP {
  constructor(ws) {
    this.ws = ws; this.id = 1; this.pending = new Map();
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { res, rej } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? rej(new Error(msg.error.message)) : res(msg.result);
      }
    };
  }
  cmd(method, params = {}, timeout = 25000) {
    const id = this.id++;
    return new Promise((res, rej) => {
      this.pending.set(id, { res, rej });
      this.ws.send(JSON.stringify({ id, method, params }));
      setTimeout(() => { if (this.pending.has(id)) { this.pending.delete(id); rej(new Error(`timeout: ${method}`)); } }, timeout);
    });
  }
  async navigate(url) { await this.cmd('Page.navigate', { url }, 25000); await sleep(3000); }
  async evaluate(expr, awaitPromise = false) {
    try {
      const r = await this.cmd('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise }, awaitPromise ? 20000 : 10000);
      return r?.result?.value;
    } catch { return null; }
  }
}

async function connect() {
  const wsUrl = await getCDPTarget();
  const { default: WebSocket } = await import(WS_PATH);
  const ws = new WebSocket(wsUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; setTimeout(() => rej(new Error('WS timeout')), 8000); });
  return new CDP(ws);
}

function formatSalary(j) {
  if (j.salaryLow > 0 && j.salaryHigh > 0) return `月薪${j.salaryLow.toLocaleString()}~${j.salaryHigh.toLocaleString()}元`;
  if (j.salaryLow > 0) return `月薪${j.salaryLow.toLocaleString()}元以上`;
  return '待遇面議';
}

async function browserFetch(cdp, url, referer) {
  const expr = `(async () => {
    try {
      const r = await fetch(${JSON.stringify(url)}, {
        headers: {'Accept': 'application/json, text/plain, */*', 'Referer': ${JSON.stringify(referer || 'https://www.104.com.tw/')}},
        credentials: 'include'
      });
      if (!r.ok) return JSON.stringify({error: r.status});
      return await r.text();
    } catch(e) { return JSON.stringify({error: e.message}); }
  })()`;
  const raw = await cdp.cmd('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }, 30000);
  const text = raw?.result?.value;
  if (!text) return null;
  try {
    const parsed = JSON.parse(text);
    if (parsed?.error) return null;
    return parsed;
  } catch { return null; }
}

function extractDetail(data) {
  if (!data || !data.data) return { company: '', content: '', req: '' };
  const d = data.data;
  const company = d.header?.custName || '';
  const content = (d.jobDetail?.jobDescription || '').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
  const reqParts = [];
  if (d.condition?.workExp) reqParts.push('工作經歷: ' + d.condition.workExp);
  if (d.condition?.edu) reqParts.push('學歷要求: ' + d.condition.edu);
  if (d.condition?.major?.length) reqParts.push('科系要求: ' + d.condition.major.join('、'));
  if (d.condition?.skill?.length) {
    const skills = d.condition.skill.map(s => typeof s === 'object' ? (s.description || s.name || '') : s).filter(Boolean);
    if (skills.length) reqParts.push('擅長工具: ' + skills.join('、'));
  }
  if (d.condition?.other) reqParts.push('其他條件: ' + d.condition.other.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim());
  return { company, content, req: reqParts.join(' | ') };
}

function makeCSVRow(arr) {
  return arr.map(v => {
    v = String(v || '').replace(/\r/g, '').replace(/\n/g, ' ');
    return (v.includes(',') || v.includes('"')) ? '"' + v.replace(/"/g, '""') + '"' : v;
  }).join(',');
}

async function main() {
  const cdp = await connect();

  // Warm up browser session on 104
  await cdp.navigate(`https://www.104.com.tw/jobs/search/?keyword=${encodeURIComponent(KEYWORD)}&mode=s`);
  await sleep(2000);

  // Fetch search results
  const apiUrl = `https://www.104.com.tw/jobs/search/api/jobs?asc=0&keyword=${encodeURIComponent(KEYWORD)}&mode=s&order=${ORDER}&pagesize=${COUNT + 10}`;
  const searchData = await browserFetch(cdp, apiUrl, `https://www.104.com.tw/jobs/search/?keyword=${encodeURIComponent(KEYWORD)}&mode=s`);

  // Load previously applied URLs from log (avoid re-applying)
  let appliedUrls = new Set();
  if (existsSync(LOG_FILE)) {
    try {
      const log = JSON.parse(readFileSync(LOG_FILE, 'utf8'));
      log.forEach(entry => { if (entry.url) appliedUrls.add(entry.url); });
    } catch {}
  }

  const jobList = Array.isArray(searchData?.data) ? searchData.data : [];

  // Filter out already-applied jobs
  const filtered = jobList.filter(j => {
    const url = j.link?.job || '';
    return !j.isApplied && !appliedUrls.has(url);
  });

  const skipped = jobList.length - filtered.length;
  if (skipped > 0) process.stderr.write(`(已過濾 ${skipped} 筆已投遞職缺)\n`);

  const baseJobs = filtered.slice(0, COUNT).map((j, i) => ({
    num: i + 1,
    title: j.jobName || '',
    company: j.custName || '',
    salary: formatSalary(j),
    location: j.jobAddrNoDesc || '',
    url: j.link?.job || '',
  }));

  // Fetch job details for each job (same session → consistent data)
  process.stderr.write(`抓取 ${baseJobs.length} 筆詳細資料...\n`);
  const bom = '﻿';
  const csvHeader = makeCSVRow(['#', '職缺名稱', '公司名稱', '薪資待遇', '工作地點', '工作內容', '條件要求', '連結']);
  const csvRows = [csvHeader];

  const jobs = [];
  for (const j of baseJobs) {
    const jobCode = j.url ? j.url.split('/').pop() : '';
    let content = '', req = '', company = j.company;
    if (jobCode) {
      await sleep(600);
      const detailUrl = `https://www.104.com.tw/job/ajax/content/${jobCode}`;
      const detail = await browserFetch(cdp, detailUrl, j.url);
      const extracted = extractDetail(detail);
      if (extracted.company) company = extracted.company;
      content = extracted.content;
      req = extracted.req;
    }
    process.stderr.write(`  [${j.num}/${baseJobs.length}] ${j.title.slice(0,30)} ${content ? '✓' : '⚠'}\n`);
    jobs.push({ ...j, company, content, req });
    csvRows.push(makeCSVRow([j.num, j.title, company, j.salary, j.location, content, req, j.url]));
  }

  // Save CSV to date folder
  const csvPath = `${DATE_DIR}/104_${KEYWORD}_${ORDER_LABEL}_${TODAY}.csv`;
  writeFileSync(csvPath, bom + csvRows.join('\n'), 'utf8');
  process.stderr.write(`CSV saved: ${csvPath}\n`);

  // Save pending jobs (with detail)
  writeFileSync(PENDING_FILE, JSON.stringify({
    date: TODAY, keyword: KEYWORD,
    total_fetched: jobList.length, skipped_applied: skipped,
    csv: csvPath, jobs
  }, null, 2), 'utf8');

  clearInterval(keepAlive);
  cdp.ws.close();

  // Print formatted list
  console.log(`\n===OUTPUT_START===`);
  console.log(`📋 ${KEYWORD} 職缺搜尋結果（${ORDER_LABEL}）— ${TODAY}`);
  const skipNote = skipped > 0 ? `｜已略過 ${skipped} 筆已投遞` : '';
  console.log(`共 ${jobs.length} 筆${skipNote}，回覆「投 號碼」即可應徵，例如：投 1 3 5\n`);
  jobs.forEach(j => {
    console.log(`${j.num}. ${j.title}`);
    console.log(`   🏢 ${j.company} | 💰 ${j.salary} | 📍 ${j.location}`);
    console.log(`   🔗 ${j.url}`);
    console.log('');
  });
  console.log(`===OUTPUT_END===`);
  console.log(`===CSV_PATH===`);
  console.log(csvPath);
  process.exit(0);
}

main().catch(e => { console.error('Fatal:', e); clearInterval(keepAlive); process.exit(1); });
