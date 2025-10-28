(() => {
  const apiMeta = document.querySelector('meta[name="api-base"]');
  const API_URL = (apiMeta && apiMeta.getAttribute('content')) || '/run';

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
    // preserve newlines
    body.innerHTML = text.split('\n').map(escapeHtml).join('<br/>');
    wrapper.appendChild(meta);
    wrapper.appendChild(body);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return wrapper;
  }

  function escapeHtml(s){
    return s.replace(/[&<>\"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]);
  }

  function setLoading(el, on = true){
    if(!el) return;
    if(on){
      el.dataset.loading = '1';
      if(!el.querySelector('.spinner')){
        const s = document.createElement('span');
        s.className = 'spinner';
        s.textContent = '…';
        s.style.marginLeft = '0.5rem';
        el.appendChild(s);
      }
    } else {
      delete el.dataset.loading;
      const sp = el.querySelector('.spinner');
      if(sp) sp.remove();
    }
  }

  async function send(){
    const question = queryInput.value.trim();
    if(!question) return;
    queryInput.value = '';
    const k = kInput.value ? Number(kInput.value) : undefined;

    // add user message
    const userEl = appendMessage(question, 'user');

    // add placeholder for bot
    const botEl = appendMessage('Thinking...', 'bot');
    setLoading(botEl, true);

    try{
      const payload = { question };
      if(k) payload.k = k;
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if(!res.ok){
        const t = await res.text();
        botEl.querySelector('.body').innerText = 'Error: ' + res.status + ' ' + t;
        setLoading(botEl, false);
        return;
      }

      const data = await res.json();

      // Attempt to render the typical result shapes
      let rendered = '';
      if(data.result){
        const r = data.result;
        // if r has 'answer' use it
        if(r.answer) rendered = (typeof r.answer === 'object') ? JSON.stringify(r.answer, null, 2) : String(r.answer);
        else if(r.text) rendered = String(r.text);
        else if(r.decision) rendered = JSON.stringify(r, null, 2);
        else rendered = JSON.stringify(r, null, 2);
      } else {
        // fallback render whole payload
        rendered = JSON.stringify(data, null, 2);
      }

      botEl.querySelector('.body').innerText = rendered;
    }catch(err){
      botEl.querySelector('.body').innerText = 'Request failed: ' + String(err);
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
