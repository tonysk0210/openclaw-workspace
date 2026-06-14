// apply_104_semi.mjs - 半自動應徵：讀取 pending_jobs.json，對指定號碼執行應徵
import { readFileSync, writeFileSync, existsSync } from 'fs';

const CDP_URL = 'http://127.0.0.1:18800';
const WS_PATH = '/Users/anthonyshangkuan/.nvm/versions/node/v24.13.1/lib/node_modules/openclaw/node_modules/ws/index.js';
const PENDING_FILE = '/Users/anthonyshangkuan/.openclaw/workspace/data/pending_jobs.json';
const LOG_FILE = '/Users/anthonyshangkuan/.openclaw/workspace/data/apply_log.json';

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
  async scroll() { await this.evaluate('window.scrollTo(0, document.body.scrollHeight)'); await sleep(1000); }
}

async function connect() {
  const wsUrl = await getCDPTarget();
  const { default: WebSocket } = await import(WS_PATH);
  const ws = new WebSocket(wsUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; setTimeout(() => rej(new Error('WS timeout')), 8000); });
  return new CDP(ws);
}

async function applyToJob(cdp, job) {
  console.log(`\n  → 導航到: ${job.url}`);
  await cdp.navigate(job.url);
  await cdp.scroll();
  await sleep(1000);

  // Check if already applied:
  // - Button text says '已應徵' / '已投遞'
  // - OR no orange button exists (orange = can apply; all gray = already applied or closed)
  const alreadyApplied = await cdp.evaluate(`(() => {
    var btns = document.querySelectorAll('[class*="apply-button__button"]');
    if (!btns.length) return false;
    for (var b of btns) {
      var text = b.textContent.trim();
      if (text.includes('已應徵') || text.includes('已投遞')) return true;
    }
    // If no orange button found, job is not open for new applications
    var hasOrange = Array.from(btns).some(b => b.classList.contains('button--orange'));
    return !hasOrange;
  })()`);

  if (alreadyApplied) {
    console.log(`  ⚠ 已應徵過，跳過`);
    return { status: 'already_applied' };
  }

  // Find and click the active apply button (orange = active)
  const clicked = await cdp.evaluate(`(() => {
    // Try orange button first (main apply)
    var btn = document.querySelector('.apply-button__button.button--orange, .apply-button__button:not(.button--gray)');
    if (btn) { btn.click(); return 'clicked:' + btn.className.slice(0,50); }
    // Fallback: any apply button
    var btn2 = document.querySelector('.apply-button__button, .apply-button');
    if (btn2) { btn2.click(); return 'clicked-fallback:' + btn2.className.slice(0,50); }
    return 'not-found';
  })()`);

  console.log(`  click result: ${clicked}`);

  if (!clicked || clicked === 'not-found') {
    return { status: 'button_not_found' };
  }

  await sleep(3000);

  // Step 1.5a: Select resume '自訂履歷: Java工程師' explicitly
  const resumeTrigger = await cdp.evaluate(`(() => {
    var trigger = document.querySelector('.select-resume .multiselect');
    if (trigger) { trigger.click(); return 'resume-trigger-clicked'; }
    return 'resume-trigger-not-found';
  })()`);
  await sleep(800);

  const resumeSelected = await cdp.evaluate(`(() => {
    var opts = document.querySelectorAll('.select-resume .multiselect__option');
    for (var opt of opts) {
      if (opt.textContent.trim() === 'Java工程師') {
        opt.click();
        return 'resume-selected:' + opt.textContent.trim();
      }
    }
    return 'resume-not-found';
  })()`);
  console.log(`  resume: ${resumeSelected}`);
  await sleep(500);

  // Step 1.5b: Select cover letter '自訂推薦信1' explicitly
  const letterTrigger = await cdp.evaluate(`(() => {
    var trigger = document.querySelector('.apply-msg .multiselect');
    if (trigger) { trigger.click(); return 'letter-trigger-clicked'; }
    return 'letter-trigger-not-found';
  })()`);
  await sleep(800);

  const letterSelected = await cdp.evaluate(`(() => {
    var opts = document.querySelectorAll('.apply-msg .multiselect__option');
    for (var opt of opts) {
      if (opt.textContent.trim().includes('自訂推薦信1') || opt.textContent.trim().includes('自訂推薦信 1')) {
        opt.click();
        return 'letter-selected:' + opt.textContent.trim();
      }
    }
    return 'letter-not-found';
  })()`);
  console.log(`  letter: ${letterSelected}`);
  await sleep(500);

  // Step 2: Click 確認送出 button in the apply form
  const submitResult = await cdp.evaluate(`(() => {
    // Primary: .submit-btn (104 apply form confirm button)
    var submitBtn = document.querySelector('.submit-btn, button.submit-btn');
    if (submitBtn) {
      var text = submitBtn.textContent.trim();
      submitBtn.click();
      return 'submitted:' + text;
    }
    // Fallback: any confirm-like button in modal
    var confirmBtn = document.querySelector(
      '[class*="modal"] button[class*="btn-primary"], ' +
      '[class*="apply"] button[class*="confirm"]'
    );
    if (confirmBtn) {
      confirmBtn.click();
      return 'confirmed:' + confirmBtn.textContent.trim();
    }
    return 'no-submit-btn';
  })()`);

  console.log(`  submit result: ${submitResult}`);

  await sleep(2000);

  // Verify success
  const verifyResult = await cdp.evaluate(`(() => {
    var successEl = document.querySelector('[class*="success"], [class*="applied"], [class*="complete"]');
    var successText = successEl ? successEl.textContent.trim().slice(0,50) : '';
    // Check button state
    var appliedBtn = document.querySelector('.apply-button__button');
    var btnText = appliedBtn ? appliedBtn.textContent.trim() : '';
    return JSON.stringify({successText, btnText, url: location.href.slice(0,80)});
  })()`);

  let verifyData = {};
  try { verifyData = JSON.parse(verifyResult || '{}'); } catch {}
  console.log(`  verify: btnText="${verifyData.btnText}" url=${verifyData.url}`);

  const success = verifyData.btnText?.includes('已應徵') ||
                  verifyData.successText?.length > 0 ||
                  submitResult?.startsWith('submitted') ||
                  submitResult?.startsWith('confirmed');

  return {
    status: success ? 'success' : 'uncertain',
    btnText: verifyData.btnText,
    submitResult
  };
}

async function main() {
  // Parse job numbers from args (e.g., node apply_104_semi.mjs 1 3 5)
  const selectedNums = process.argv.slice(2).map(Number).filter(n => n > 0);

  if (selectedNums.length === 0) {
    console.error('Usage: node apply_104_semi.mjs <num1> [num2] ...');
    console.error('Example: node apply_104_semi.mjs 1 3 5');
    process.exit(1);
  }

  if (!existsSync(PENDING_FILE)) {
    console.error(`找不到 ${PENDING_FILE}，請先執行搜尋`);
    process.exit(1);
  }

  const pendingData = JSON.parse(readFileSync(PENDING_FILE, 'utf8'));
  const jobs = pendingData.jobs || [];

  console.log(`=== 半自動應徵 ===`);
  console.log(`待應徵清單: ${jobs.length} 筆`);
  console.log(`選擇應徵: ${selectedNums.join(', ')}`);

  const selected = selectedNums
    .map(n => jobs.find(j => j.num === n))
    .filter(Boolean);

  if (selected.length === 0) {
    console.error('沒有符合的職缺號碼');
    process.exit(1);
  }

  console.log(`\n確認應徵清單:`);
  selected.forEach(j => console.log(`  #${j.num} ${j.title} — ${j.company}`));

  const cdp = await connect();
  console.log('\nCDP 連接成功，開始應徵...');

  // Load existing log
  let applyLog = [];
  if (existsSync(LOG_FILE)) {
    try { applyLog = JSON.parse(readFileSync(LOG_FILE, 'utf8')); } catch {}
  }

  const results = [];
  for (const job of selected) {
    console.log(`\n[${job.num}] ${job.title} — ${job.company}`);
    const result = await applyToJob(cdp, job);
    const entry = {
      date: new Date().toISOString().slice(0, 10),
      num: job.num,
      title: job.title,
      company: job.company,
      url: job.url,
      ...result
    };
    results.push(entry);
    applyLog.push(entry);

    const icon = result.status === 'success' ? '✓' : result.status === 'already_applied' ? '↩' : '?';
    console.log(`  ${icon} status: ${result.status}`);
    await sleep(1500);
  }

  // Save log
  writeFileSync(LOG_FILE, JSON.stringify(applyLog, null, 2), 'utf8');

  clearInterval(keepAlive);
  cdp.ws.close();

  console.log(`\n=== 應徵結果 ===`);
  results.forEach(r => {
    const icon = r.status === 'success' ? '✓' : r.status === 'already_applied' ? '↩' : '?';
    console.log(`${icon} #${r.num} ${r.title} — ${r.company} [${r.status}]`);
  });

  const successCount = results.filter(r => r.status === 'success').length;
  console.log(`\n成功: ${successCount}/${results.length}`);
  process.exit(0);
}

main().catch(e => { console.error('Fatal:', e); clearInterval(keepAlive); process.exit(1); });
