/**
 * TaskProgressBanner.jsx - Interactive React component for live background Celery task polling
 * with shadcn/ui styling, animated progress indicators, and auto-refresh on completion.
 */

(function () {
  const { useState, useEffect } = React;

  function TaskProgressBanner({ taskId, arenaId, initialStatus, initialMessage }) {
    const [status, setStatus] = useState(initialStatus || 'PENDING');
    const [message, setMessage] = useState(initialMessage || 'Processing PDF text and generating questions with Ollama...');
    const [generatedCount, setGeneratedCount] = useState(0);
    const [totalRequested, setTotalRequested] = useState(0);
    const [errorDetail, setErrorDetail] = useState('');
    const [dismissed, setDismissed] = useState(false);

    useEffect(() => {
      if (!taskId || !arenaId || status === 'SUCCESS' || status === 'FAILURE' || dismissed) {
        return;
      }

      const pollInterval = setInterval(async () => {
        try {
          const res = await fetch(`/arenas/${arenaId}/tasks/${taskId}/status/`);
          if (res.ok) {
            const data = await res.json();
            if (data.status) setStatus(data.status);
            if (data.message) setMessage(data.message);
            if (data.generated_count !== undefined) setGeneratedCount(data.generated_count);
            if (data.total_requested !== undefined) setTotalRequested(data.total_requested);

            if (data.status === 'SUCCESS') {
              clearInterval(pollInterval);
              setMessage(`Complete! Generated ${data.generated_count} questions. Refreshing workspace...`);
              setTimeout(() => {
                window.location.reload();
              }, 1500);
            } else if (data.status === 'FAILURE') {
              clearInterval(pollInterval);
              setErrorDetail(data.error_detail || 'An unexpected error occurred during generation.');
            }
          }
        } catch (err) {
          console.error('Task polling error:', err);
        }
      }, 2500);

      return () => clearInterval(pollInterval);
    }, [taskId, arenaId, status, dismissed]);

    if (dismissed) return null;

    // Success State
    if (status === 'SUCCESS') {
      return (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-800 dark:text-emerald-200 p-4 shadow-sm flex items-center justify-between animate-in fade-in duration-300">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 text-white flex items-center justify-center font-bold">
              <i className="fa-solid fa-circle-check text-base"></i>
            </div>
            <div>
              <h4 className="text-xs sm:text-sm font-bold">Generation Completed Successfully</h4>
              <p className="text-xs opacity-90">{message}</p>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-emerald-500/20 text-emerald-700 dark:text-emerald-300">
            {generatedCount} Qs Added
          </span>
        </div>
      );
    }

    // Failure State
    if (status === 'FAILURE') {
      return (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 text-destructive p-4 shadow-sm flex items-start justify-between animate-in fade-in duration-300">
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 rounded-lg bg-destructive text-destructive-foreground flex items-center justify-center font-bold mt-0.5 flex-shrink-0">
              <i className="fa-solid fa-circle-exclamation text-base"></i>
            </div>
            <div>
              <h4 className="text-xs sm:text-sm font-bold">Generation Encountered an Error</h4>
              <p className="text-xs mt-0.5">{errorDetail || message}</p>
            </div>
          </div>
          <button
            onClick={() => setDismissed(true)}
            className="text-destructive/70 hover:text-destructive p-1 rounded-md transition-colors"
            title="Dismiss notification"
          >
            <i className="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>
      );
    }

    // In Progress State (PENDING / STARTED)
    return (
      <div className="rounded-xl border border-primary/30 bg-primary/5 text-foreground p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3 relative overflow-hidden">
        {/* Animated Accent Bar */}
        <div className="absolute top-0 left-0 bottom-0 w-1 bg-primary animate-pulse"></div>

        <div className="flex items-center space-x-3 pl-1">
          <div className="w-9 h-9 rounded-xl bg-primary text-primary-foreground flex items-center justify-center font-bold shadow-xs">
            <i className="fa-solid fa-circle-notch fa-spin text-sm"></i>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h4 className="text-xs sm:text-sm font-bold text-foreground">
                AI Generation & Multi-Agent Verification in Progress
              </h4>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary border border-primary/20">
                Live Polling
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">{message}</p>
          </div>
        </div>

        <div className="flex items-center space-x-3 self-end sm:self-center">
          <div className="text-right hidden md:block">
            <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">Worker</span>
            <span className="text-xs font-semibold text-foreground">Celery + Ollama</span>
          </div>
        </div>
      </div>
    );
  }

  function initTaskProgressBanner() {
    const rootEl = document.getElementById('react-task-progress');
    if (rootEl && !rootEl.dataset.mounted) {
      rootEl.dataset.mounted = 'true';
      try {
        const taskId = rootEl.getAttribute('data-task-id');
        const arenaId = rootEl.getAttribute('data-arena-id');
        const initialStatus = rootEl.getAttribute('data-initial-status');
        const initialMessage = rootEl.getAttribute('data-initial-message');

        const root = ReactDOM.createRoot(rootEl);
        root.render(
          React.createElement(TaskProgressBanner, {
            taskId,
            arenaId,
            initialStatus,
            initialMessage,
          })
        );
      } catch (err) {
        console.error('Error mounting React TaskProgressBanner:', err);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTaskProgressBanner);
  } else {
    initTaskProgressBanner();
  }
})();

