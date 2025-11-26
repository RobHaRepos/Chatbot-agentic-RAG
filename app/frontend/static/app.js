(() => {
  const apiMeta = document.querySelector('meta[name="api-base"]');
  const API_URL = apiMeta?.getAttribute('content') || '/run';
  // Compute TTS URL based on the API_URL; default to /tts when not available.
  // Choose a TTS URL based on how the API base is configured.
  // Avoid nested ternaries for readability and to satisfy SonarQube rule S3358.
  let TTS_URL;
  if (API_URL.endsWith('/run')) {
    TTS_URL = API_URL.replace(/\/run$/, '/tts');
  } else if (API_URL.endsWith('/')) {
    TTS_URL = API_URL + 'tts';
  } else {
    TTS_URL = '/tts';
  }

  const messagesEl = document.getElementById('messages');
  const queryInput = document.getElementById('queryInput');
  const sendBtn = document.getElementById('sendBtn');
  const kInput = document.getElementById('kInput');
  const apiUrlText = document.getElementById('apiUrlText');

  apiUrlText.textContent = API_URL;

  function appendMessage(text, who = 'bot'){
    const wrapper = document.createElement('div');
    wrapper.className = 'msg ' + (who === 'user' ? 'user' : 'bot');

    // Structure: [controls] [content(meta + body)]
    const controls = document.createElement('div');
    controls.className = 'controls';
    let ttsBtn = null;
    if (who === 'bot'){
      ttsBtn = document.createElement('button');
      ttsBtn.className = 'tts-btn';
      ttsBtn.type = 'button';
      ttsBtn.title = 'Speak this message';
      ttsBtn.innerText = '🔊';
      ttsBtn.disabled = !text?.trim();
      controls.appendChild(ttsBtn);
    }

    const content = document.createElement('div');
    content.className = 'msg-content';
    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = who === 'user' ? 'You' : 'Assistant';
    const body = document.createElement('div');
    body.className = 'body';
    body.innerText = text;
    content.appendChild(meta);
    content.appendChild(body);

    // Append in order: controls then content; for user messages controls will be empty
    wrapper.appendChild(controls);
    wrapper.appendChild(content);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    // Add click handler for TTS button (closure over body text)
    if(ttsBtn){
      ttsBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const textToSpeak = body.innerText || '';
        if(!textToSpeak.trim()) return;
        playTTS(textToSpeak, ttsBtn);
      });
    }

    return wrapper;
  }

  function setLoading(el, isLoading){
    if(!el) return;
    el.dataset.loading = isLoading ? '1' : '0';
    // If a TTS button exists in the element, disable while loading
    const ttsBtn = el.querySelector?.('.tts-btn');
    if(ttsBtn) ttsBtn.disabled = !!isLoading;
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
      console?.error?.('FrontendLogger failed', { level, event, meta, err });
    }
  }

  // Helper: render result object into a string for display
  function renderResultObject(data){
    if(!data) return JSON.stringify(data, null, 2);
    const r = data.result || data;
    if(r && typeof r === 'object'){
      if('answer' in r && r.answer) return (typeof r.answer === 'object') ? JSON.stringify(r.answer, null, 2) : String(r.answer);
      if('text' in r && r.text) return String(r.text);
      if('action' in r) return JSON.stringify(r, null, 2);
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
      // Once the bot text is rendered, enable its TTS button (if present)
      let ttsBtn = botEl.querySelector('.tts-btn');
      if (ttsBtn){
        // Enable existing button
        ttsBtn.disabled = false;
      } else {
        // fallback: create a tts button if the initial appendMessage didn't create one
        const controls = botEl.querySelector('.controls') || document.createElement('div');
        controls.className = 'controls';
        ttsBtn = document.createElement('button');
        ttsBtn.className = 'tts-btn';
        ttsBtn.type = 'button';
        ttsBtn.title = 'Speak this message';
        ttsBtn.innerText = '🔊';
        const bodyEl = botEl.querySelector('.body');
        ttsBtn.disabled = !bodyEl?.innerText?.trim();
        controls.appendChild(ttsBtn);
        // if controls didn't exist as a child, insert it
        if(!botEl.querySelector('.controls')){
          botEl.insertBefore(controls, botEl.firstChild);
        }
        // attach click handler
        if(bodyEl){
          ttsBtn.addEventListener('click', (e) => { e.preventDefault(); playTTS(bodyEl.innerText, ttsBtn); })
        }
      }
    }catch(err){
      await handleException(botEl, question, err);
    }finally{
      setLoading(botEl, false);
    }
  }

  // A single audio instance shared for playback control
  let _activeAudio = null;
  function stopActiveAudio(){
    if(_activeAudio){
      try {
        _activeAudio.pause();
      } catch (err) {
        // Log the error so we can diagnose playback issues; do not crash the UI
        console.error('Failed to pause active audio', err);
      } finally {
        // Always clear the reference to the active audio so we don't leak handles
        _activeAudio = null;
      }
    }
  }

  async function playTTS(text, btn){
    if(!text) return;
    // Provide immediate UI feedback
    if(btn){ btn.disabled = true; btn.innerText = '🔊…'; }
    stopActiveAudio();
    try{
      const resp = await fetch(TTS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      if(!resp.ok){
        const msg = await resp.text();
        throw new Error(resp.status + ' ' + msg);
      }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      _activeAudio = audio;
      audio.onended = () => {
        if(btn){ btn.innerText = '🔊'; btn.disabled = false; }
        URL.revokeObjectURL(url);
        _activeAudio = null;
      };
      audio.onerror = (e) => {
        console.error('Audio playback error', e);
        if(btn){ btn.innerText = '🔊'; btn.disabled = false; }
      };
      await audio.play();
      if(btn) btn.innerText = '⏸';
      // Optional: clicking while playing toggles pause/play
      const toggleHandler = () => {
        if(!_activeAudio) return;
        if(_activeAudio.paused){ _activeAudio.play(); btn.innerText = '⏸'; }
        else { _activeAudio.pause(); btn.innerText = '▶️'; }
      };
      btn.addEventListener('click', toggleHandler, { once: true });
    }catch(err){
      console.error('TTS fetch failed', err);
      if(btn){ btn.innerText = '🔊'; btn.disabled = false; }
      alert('TTS error: ' + (err?.message || err));
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
