(function(){
  try{
    const apiMeta = document.querySelector('meta[name="api-base"]');
  const API_BASE = apiMeta?.getAttribute('content') || '/run';
    let LOG_ENDPOINT = '/log';
    try{
      const url = new URL(API_BASE, location.href);
      LOG_ENDPOINT = url.origin + '/log';
    } catch (err) {
      LOG_ENDPOINT = '/log';
      try { console && console.warn && console.warn('FrontendLogger: invalid API_BASE, falling back to /log', err && err.message); } catch (_) { }
    }

    async function sendLog(payload){
      try{
        // fire-and-forget; keep small and tolerant
        await fetch(LOG_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      }catch(_){
        // ignore network/logging failures silently
      }
    }

    window.FrontendLogger = {
      log(level, message, meta){
        const entry = {
          ts: new Date().toISOString(),
          level: (level || 'info'),
          message: String(message || ''),
          meta: meta || {},
        };
        // send async without awaiting
        void sendLog(entry);
      }
    };

    // Capture console methods and forward to backend
    if(globalThis.console){
      ['log','info','warn','error'].forEach((m)=>{
        const orig = globalThis.console[m]?.bind(globalThis.console);
        if(!orig) return;
        globalThis.console[m] = function(...args){
          try{
            const msg = args.map(a => (typeof a === 'object' ? JSON.stringify(a) : String(a))).join(' ');
            globalThis.FrontendLogger.log(m, msg, {href: location.href});
          }catch(e){}
          try{ orig(...args); }catch(_){ /* ignore */ }
        };
      });
    }

    // Capture uncaught errors and unhandled promise rejections
    globalThis.addEventListener('error', function(ev){
      try{
        globalThis.FrontendLogger.log('error', ev.message || 'window_error', {
          filename: ev.filename, lineno: ev.lineno, colno: ev.colno
        });
      }catch(e){}
    });

    globalThis.addEventListener('unhandledrejection', function(ev){
      try{
        const r = ev.reason;
        globalThis.FrontendLogger.log('error', 'unhandledrejection', {reason: (typeof r === 'object' ? JSON.stringify(r) : String(r))});
      }catch(e){}
    });

  }catch(e){
    // very defensive: if anything in logger init fails, don't break the app
    try { console?.warn?.('FrontendLogger init failed', e); } catch (_) { }
  }
})();
