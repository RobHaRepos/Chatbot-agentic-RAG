(() => {
  const apiMeta = document.querySelector('meta[name="api-base"]');
  const API_URL = apiMeta?.getAttribute('content') || '/run';

  const messagesEl = document.getElementById('messages');
  const queryInput = document.getElementById('queryInput');
  const sendBtn = document.getElementById('sendBtn');
  const kInput = document.getElementById('kInput');
  const apiUrlText = document.getElementById('apiUrlText');

  apiUrlText.textContent = API_URL;

  function appendMessage(text, who = 'bot'){
    const wrapper = document.createElement('div');
    wrapper.className = 'msg ' + (who === 'user' ? 'user' : 'bot');
    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = who === 'user' ? 'You' : 'Assistant';
    const body = document.createElement('div');
    body.className = 'body';
    body.innerText = text;
    wrapper.appendChild(meta);
    wrapper.appendChild(body);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return wrapper;
  }

  function setLoading(el, isLoading){
    if(!el) return;
    el.dataset.loading = isLoading ? '1' : '0';
  }

  // Helper: build request payload
  function buildPayload(question, k){
    const payload = { question };
    if(k) payload.k = k;
    return payload;
  }

  // Helper: log safely (fire-and-forget)
  function safeLog(level, event, meta){
    try {
      globalThis?.FrontendLogger?.log(level, event, meta);
    } catch (err) {
      try {
        console.error('FrontendLogger failed', { level, event, meta, err });
      } catch (error_) {
      }
    }
  }

  // Helper: render result object into a string for display
  function renderResultObject(data){
    if(!data) return JSON.stringify(data, null, 2);
    const r = data.result || data;
    if(r && typeof r === 'object'){
      if('answer' in r && r.answer) return (typeof r.answer === 'object') ? JSON.stringify(r.answer, null, 2) : String(r.answer);
      if('text' in r && r.text) return String(r.text);
      if('decision' in r) return JSON.stringify(r, null, 2);
      return JSON.stringify(r, null, 2);
    }
    return String(r);
  }

  async function handleErrorResponse(botEl, res, question){
    const t = await res.text();
    if(botEl) botEl.querySelector('.body').innerText = 'Error: ' + res.status + ' ' + t;
    safeLog('error', 'api_error', {status: res.status, text: t, question});
  }

  async function handleException(botEl, question, err){
    if(botEl) botEl.querySelector('.body').innerText = 'Request failed: ' + String(err);
    safeLog('error', 'request_failed', {question, error: String(err)});
  }

  async function send(){
    const question = queryInput.value.trim();
    if(!question) return;
    queryInput.value = '';
    const k = kInput.value ? Number(kInput.value) : undefined;

    // add user message and placeholder for bot
    appendMessage(question, 'user');
    const botEl = appendMessage('Thinking...', 'bot');
    setLoading(botEl, true);

    try{
      safeLog('info', 'send_question', {question});
      const payload = buildPayload(question, k);
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if(!res.ok){
        await handleErrorResponse(botEl, res, question);
        return;
      }

      const data = await res.json();
      safeLog('info', 'received_response', {question, result: data.result});

      const rendered = renderResultObject(data);
      botEl.querySelector('.body').innerText = rendered;
    }catch(err){
      await handleException(botEl, question, err);
    }finally{
      setLoading(botEl, false);
    }
  }

  // submit handlers
  sendBtn.addEventListener('click', send);
  queryInput.addEventListener('keydown', (e) => {
    if(e.key === 'Enter' && !e.shiftKey){
      e.preventDefault();
      send();
    }
  });

})();
