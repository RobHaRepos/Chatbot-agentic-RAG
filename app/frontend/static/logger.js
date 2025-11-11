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
      console?.warn?.('FrontendLogger: invalid API_BASE, falling back to /log', err?.message);
    }

    async function sendLog(payload){
      try{
        // fire-and-forget; keep small and tolerant
        await fetch(LOG_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      } catch (err) {
        console?.warn?.('FrontendLogger: sendLog failed', err?.message);
      }
    }

    globalThis.FrontendLogger = {
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
    if (globalThis.console) {
      for (const m of ['log', 'info', 'warn', 'error']) {
        const orig = globalThis.console[m]?.bind(globalThis.console);
        if (!orig) continue;
        globalThis.console[m] = function(...args) {
          try {
            const msg = args.map(a => (typeof a === 'object' ? JSON.stringify(a) : String(a))).join(' ');
            try {
              globalThis.FrontendLogger.log(m, msg, { href: location.href });
            } catch (e) {
              try { orig('FrontendLogger.log failed', e?.message); } catch (_) { /* last-resort ignore */ }
              throw e;
            }
          } catch (e) {
            try { orig('FrontendLogger formatting failed', e?.message); } catch (_) { /* last-resort ignore */ }
          }
          return orig(...args);
        };
      }
    }

    // Capture uncaught errors and unhandled promise rejections
    globalThis.addEventListener('error', function(ev){
      try{
        globalThis.FrontendLogger.log('error', ev.message || 'window_error', {
          filename: ev.filename, lineno: ev.lineno, colno: ev.colno
        });
      } catch (e) {
        try { globalThis.console?.error?.('FrontendLogger.log failed handling window error', e?.message); } catch (_) { }
        throw e;
      }
    });

    globalThis.addEventListener('unhandledrejection', function(ev){
      try{
        const r = ev.reason;
        globalThis.FrontendLogger.log('error', 'unhandledrejection', {reason: (typeof r === 'object' ? JSON.stringify(r) : String(r))});
      } catch (e) {
        try { globalThis.console?.error?.('FrontendLogger.log failed handling unhandledrejection', e?.message); } catch (_) { }
        throw e;
      }
    });

  } catch (e) {
    console?.warn?.('FrontendLogger init failed', e);
  }
})();
