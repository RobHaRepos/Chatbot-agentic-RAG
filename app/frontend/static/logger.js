// Lightweight frontend logger that posts logs to the backend /log endpoint.
(function(){
  try{
    const apiMeta = document.querySelector('meta[name="api-base"]');
    // API base may be something like http://localhost:8000/run - derive origin
    const API_BASE = (apiMeta && apiMeta.getAttribute('content')) || '/run';
    let LOG_ENDPOINT = '/log';
    try{
      // If API_BASE is an absolute URL or origin+path, use its origin for logging endpoint
      const url = new URL(API_BASE, location.href);
      LOG_ENDPOINT = url.origin + '/log';
    }catch(e){
      // fallback to relative /log
      LOG_ENDPOINT = '/log';
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
    if(window.console){
      ['log','info','warn','error'].forEach((m)=>{
        const orig = window.console[m] && window.console[m].bind(window.console);
        if(!orig) return;
        window.console[m] = function(...args){
          try{
            const msg = args.map(a => (typeof a === 'object' ? JSON.stringify(a) : String(a))).join(' ');
            window.FrontendLogger.log(m, msg, {href: location.href});
          }catch(e){}
          try{ orig(...args); }catch(_){ /* ignore */ }
        };
      });
    }

    // Capture uncaught errors and unhandled promise rejections
    window.addEventListener('error', function(ev){
      try{
        window.FrontendLogger.log('error', ev.message || 'window_error', {
          filename: ev.filename, lineno: ev.lineno, colno: ev.colno
        });
      }catch(e){}
    });

    window.addEventListener('unhandledrejection', function(ev){
      try{
        const r = ev.reason;
        window.FrontendLogger.log('error', 'unhandledrejection', {reason: (typeof r === 'object' ? JSON.stringify(r) : String(r))});
      }catch(e){}
    });

  }catch(e){
    // very defensive: if anything in logger init fails, don't break the app
    console && console.warn && console.warn('FrontendLogger init failed', e);
  }
})();
