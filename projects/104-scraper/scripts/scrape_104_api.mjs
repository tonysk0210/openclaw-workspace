// scrape_104_api.mjs - 用 104 JSON API 抓職缺，更穩定
// 固定 10 筆 per batch
import { writeFileSync } from 'fs';

const CDP_URL = 'http://127.0.0.1:18800';
import { mkdirSync } from 'fs';
const _now = new Date();
const _MM = String(_now.getMonth() + 1).padStart(2, '0');
const _DD = String(_now.getDate()).padStart(2, '0');
const DATE_DIR = process.env.HOME + `/Desktop/${_MM}-${_DD}`;
const DESKTOP = DATE_DIR;
try { mkdirSync(DATE_DIR, { recursive: true }); } catch {}
const TODAY = new Date().toISOString().slice(0, 10);
const BATCH_SIZE = 10;
const WS_PATH = '/Users/anthonyshangkuan/.nvm/versions/node/v24.13.1/lib/node_modules/openclaw/node_modules/ws/index.js';

const keepAlive = setInterval(() => process.stdout.write('.\n'), 20000);
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function getCDPTarget() {
  const r = await fetch(`${CDP_URL}/json`);
  const targets = await r.json();
  const page = targets.find(t => t.type === 'page');
  if (!page) throw new Error('No page target');
  return page.webSocketDebuggerUrl;
}

class CDP {
  constructor(ws) {
    this.ws = ws; this.id = 1; this.pending = new Map(); this.handlers = {};
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { res, rej } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? rej(new Error(msg.error.message)) : res(msg.result);
      } else if (msg.method && this.handlers[msg.method]) {
        this.handlers[msg.method](msg.params);
      }
    };
  }
  cmd(method, params = {}, timeout = 20000) {
    const id = this.id++;
    return new Promise((res, rej) => {
      this.pending.set(id, { res, rej });
      this.ws.send(JSON.stringify({ id, method, params }));
      setTimeout(() => { if (this.pending.has(id)) { this.pending.delete(id); rej(new Error(`timeout: ${method}`)); } }, timeout);
    });
  }
  on(event, fn) { this.handlers[event] = fn; }
  async evaluate(expr) {
    try { const r = await this.cmd('Runtime.evaluate', { expression: expr, returnByValue: true }); return r?.result?.value; } catch { return null; }
  }
  async navigate(url) { await this.cmd('Page.navigate', { url }, 25000); await sleep(3000); }
}

async function connect() {
  const wsUrl = await getCDPTarget();
  const { default: WebSocket } = await import(WS_PATH);
  const ws = new WebSocket(wsUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; setTimeout(() => rej(new Error('WS timeout')), 8000); });
  return new CDP(ws);
}

// Use browser's fetch() via CDP to bypass Cloudflare
async function browserFetch(cdp, url, referer) {
  const expr = `
    (async () => {
      try {
        const r = await fetch(${JSON.stringify(url)}, {
          headers: {
            'Accept': 'application/json, text/plain, */*',
            'Referer': ${JSON.stringify(referer || 'https://www.104.com.tw/')},
          },
          credentials: 'include'
        });
        if (!r.ok) return JSON.stringify({error: r.status, text: await r.text()});
        return await r.text();
      } catch(e) {
        return JSON.stringify({error: e.message});
      }
    })()
  `;
  const raw = await cdp.cmd('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }, 30000);
  const text = raw?.result?.value;
  if (!text) return null;
  try {
    const parsed = JSON.parse(text);
    if (parsed?.error) { console.log(`  ⚠ fetch error: ${parsed.error}`); return null; }
    return parsed;
  } catch { return null; }
}

async function searchJobs(cdp, order) {
  const url = `https://www.104.com.tw/jobs/search/api/jobs?asc=0&keyword=Java&mode=s&order=${order}&pagesize=30`;
  return browserFetch(cdp, url, 'https://www.104.com.tw/jobs/search/?keyword=Java&mode=s');
}

async function getJobDetail(cdp, jobNo) {
  const url = `https://www.104.com.tw/job/ajax/content/${jobNo}`;
  return browserFetch(cdp, url, `https://www.104.com.tw/job/${jobNo}`);
}

function extractDetail(data) {
  if (!data || !data.data) return { company: '', content: '', req: '' };
  const d = data.data;

  const company = d.header?.custName || '';

  // 工作內容
  const content = (d.jobDetail?.jobDescription || '').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();

  // 條件要求
  const reqParts = [];
  if (d.condition?.workExp) reqParts.push('工作經歷: ' + d.condition.workExp);
  if (d.condition?.edu) reqParts.push('學歷要求: ' + d.condition.edu);
  if (d.condition?.major?.length) reqParts.push('科系要求: ' + d.condition.major.join('、'));
  if (d.condition?.skill?.length) {
    const skills = d.condition.skill.map(s => typeof s === 'object' ? (s.description || s.name || JSON.stringify(s)) : s);
    reqParts.push('擅長工具: ' + skills.join('、'));
  }
  if (d.condition?.other) reqParts.push('其他條件: ' + d.condition.other.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim());

  const req = reqParts.join(' | ');

  return { company, content, req };
}

function makeCSVRow(arr) {
  return arr.map(v => {
    v = String(v || '').replace(/\r/g, '').replace(/\n/g, ' ');
    return (v.includes(',') || v.includes('"')) ? '"' + v.replace(/"/g, '""') + '"' : v;
  }).join(',');
}

function formatSalary(j) {
  if (j.salaryLow > 0 && j.salaryHigh > 0) return `月薪${j.salaryLow.toLocaleString()}~${j.salaryHigh.toLocaleString()}元`;
  if (j.salaryLow > 0) return `月薪${j.salaryLow.toLocaleString()}元以上`;
  return '待遇面議';
}

async function runBatch(cdp, order, outFile, label) {
  console.log(`\n=== ${label} ===`);
  const searchData = await searchJobs(cdp, order);
  // API returns data as a direct array (not data.list)
  const jobList = Array.isArray(searchData?.data) ? searchData.data : (searchData?.data?.list || []);
  console.log(`  API 返回 ${jobList.length} 筆，取前 ${BATCH_SIZE} 筆`);

  const jobs = jobList.slice(0, BATCH_SIZE);
  const header = makeCSVRow(['#', '職缺名稱', '公司名稱', '薪資待遇', '工作地點', '工作內容', '條件要求', '連結']);
  const rows = [header];

  for (let i = 0; i < jobs.length; i++) {
    const j = jobs[i];
    // Job URL is in link.job (alphanumeric code), NOT jobNo (numeric ID)
    const jobUrl = j.link?.job || '';
    const jobCode = jobUrl ? jobUrl.split('/').pop() : '';
    const title = j.jobName || j.title || '';
    const listSalary = formatSalary(j);
    const listLocation = j.jobAddrNoDesc || j.addr || '';
    const url = jobUrl || (jobCode ? `https://www.104.com.tw/job/${jobCode}` : '');

    console.log(`[${i + 1}/${jobs.length}] ${title.slice(0, 50)}`);

    let company = j.custName || '', content = '', req = '';
    if (jobCode) {
      await sleep(600);
      const detail = await getJobDetail(cdp, jobCode);
      const extracted = extractDetail(detail);
      if (extracted.company) company = extracted.company;
      content = extracted.content;
      req = extracted.req;
    }

    if (content) console.log(`  ✓ company(${company}) content(${content.length}ch) req(${req.length}ch)`);
    else console.log(`  ⚠ no content`);

    rows.push(makeCSVRow([i + 1, title, company, listSalary, listLocation, content, req, url]));
  }

  const bom = '﻿';
  writeFileSync(outFile, bom + rows.join('\n'), 'utf8');
  const hasContent = rows.slice(1).filter(r => r.length > 100).length;
  console.log(`Saved: ${outFile} (${rows.length - 1} 筆, ${hasContent} 有內容)`);
  return rows.length - 1;
}

async function main() {
  console.log(`=== 104 Java 職缺爬蟲 (API 模式) === ${TODAY}`);
  console.log(`批次大小: ${BATCH_SIZE} 筆`);

  const cdp = await connect();
  console.log('CDP 連接成功');

  // Navigate to 104 first to establish session
  await cdp.cmd('Network.enable');
  console.log('預熱瀏覽器 session...');
  await cdp.navigate('https://www.104.com.tw/jobs/search/?keyword=Java&mode=s');
  await sleep(3000);

  const recOut = `${DESKTOP}/104_Java_符合度高_${TODAY}.csv`;
  const relOut = `${DESKTOP}/104_Java_最近更新_${TODAY}.csv`;

  const recCount = await runBatch(cdp, 14, recOut, '符合度高');
  const relCount = await runBatch(cdp, 1, relOut, '最近更新');

  clearInterval(keepAlive);
  cdp.ws.close();

  console.log(`\n=== 完成 ===`);
  console.log(`符合度高: ${recOut} (${recCount} 筆)`);
  console.log(`最近更新: ${relOut} (${relCount} 筆)`);
  process.exit(0);
}

main().catch(e => { console.error('Fatal:', e); clearInterval(keepAlive); process.exit(1); });
