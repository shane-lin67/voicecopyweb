const form = document.querySelector('#job-form');
const tabs = document.querySelectorAll('.tab');
const linkPanel = document.querySelector('#link-panel');
const filePanel = document.querySelector('#file-panel');
const fileInput = document.querySelector('#file');
const submit = document.querySelector('#submit');
const progressCard = document.querySelector('#progress-card');
const stage = document.querySelector('#stage');
const percent = document.querySelector('#percent');
const bar = document.querySelector('#bar');
const errorBox = document.querySelector('#error');
const resultCard = document.querySelector('#result-card');
const result = document.querySelector('#result');
const dialog = document.querySelector('#token-dialog');
let activeTab = 'link';

function extractUrl(text) {
  const match = text.match(/https?:\/\/[^\s<>]+/i);
  if (!match) return text.trim();
  return match[0].replace(/[，。！？、；：）】》」』〉”’"']+$/g, '');
}

document.querySelector('#url').addEventListener('paste', event => {
  const pasted = event.clipboardData?.getData('text') || '';
  const url = extractUrl(pasted);
  if (url !== pasted.trim()) {
    event.preventDefault();
    event.currentTarget.value = url;
  }
});

tabs.forEach(tab => tab.addEventListener('click', () => {
  tabs.forEach(item => item.classList.remove('active'));
  tab.classList.add('active');
  activeTab = tab.dataset.tab;
  linkPanel.classList.toggle('active', activeTab === 'link');
  filePanel.classList.toggle('active', activeTab === 'file');
}));

fileInput.addEventListener('change', () => {
  document.querySelector('#file-name').textContent = fileInput.files[0]?.name || '';
});

function token() { return localStorage.getItem('voice-copy-token') || ''; }
function setProgress(label, value) {
  progressCard.hidden = false;
  stage.textContent = label;
  percent.textContent = `${value}%`;
  bar.style.width = `${value}%`;
}
function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
  submit.disabled = false;
}

async function submitJob() {
  errorBox.hidden = true; resultCard.hidden = true;
  const data = new FormData();
  if (activeTab === 'link') {
    const urlField = document.querySelector('#url');
    urlField.value = extractUrl(urlField.value);
    data.append('url', urlField.value);
  }
  else if (fileInput.files[0]) data.append('file', fileInput.files[0]);
  submit.disabled = true;
  setProgress('正在提交任务', 3);
  const response = await fetch('/api/jobs', { method: 'POST', headers: {'X-Access-Token': token()}, body: data });
  if (response.status === 401) { submit.disabled = false; dialog.showModal(); return; }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || payload.error?.message || '提交失败');
  }
  const { job_id } = await response.json();
  listen(job_id);
}

function listen(jobId) {
  const events = new EventSource(`/api/jobs/${jobId}/events?token=${encodeURIComponent(token())}`);
  events.onmessage = ({data}) => {
    const event = JSON.parse(data);
    if (event.type === 'progress') setProgress(event.stage, event.progress);
    if (event.type === 'complete') {
      events.close(); setProgress('完成', 100); submit.disabled = false;
      result.value = event.result; resultCard.hidden = false;
      resultCard.scrollIntoView({behavior: 'smooth', block: 'start'});
    }
    if (event.type === 'error') { events.close(); showError(event.message); }
  };
  events.onerror = () => { events.close(); showError('连接中断，请确认 Mac 上的服务仍在运行。'); };
}

form.addEventListener('submit', event => {
  event.preventDefault();
  submitJob().catch(error => showError(error.message));
});

document.querySelector('#token-form').addEventListener('submit', () => {
  localStorage.setItem('voice-copy-token', document.querySelector('#token-input').value.trim());
  setTimeout(() => submitJob().catch(error => showError(error.message)), 50);
});

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return true;
  }

  // 局域网 HTTP 在手机上不是安全上下文，Clipboard API 会被禁用。
  // 直接选中结果框并使用旧复制命令，兼容 iOS Safari 和 Android 浏览器。
  result.focus({preventScroll: true});
  result.setSelectionRange(0, result.value.length);
  const copied = document.execCommand('copy');
  result.setSelectionRange(result.value.length, result.value.length);
  result.blur();
  return copied;
}

document.querySelector('#copy').addEventListener('click', async event => {
  const button = event.currentTarget;
  if (!result.value.trim()) return;
  try {
    const copied = await copyText(result.value);
    button.textContent = copied ? '已复制' : '请长按复制';
  } catch (_) {
    result.focus();
    result.select();
    button.textContent = '请长按复制';
  }
  setTimeout(() => button.textContent = '复制全文', 1600);
});
