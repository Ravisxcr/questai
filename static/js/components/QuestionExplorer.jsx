/**
 * QuestionExplorer.jsx - Interactive React component for exploring questions,
 * multi-agent reasoning, source evidence, and distractor breakdowns with shadcn/ui styling.
 */

(function () {
  const { useState, useMemo } = React;

  function QuestionExplorer({ initialQuestions, arenaId, csrfToken }) {
    const [questions, setQuestions] = useState(initialQuestions || []);
    const [selectedType, setSelectedType] = useState('ALL');
    const [searchQuery, setSearchQuery] = useState('');
    const [expandedCards, setExpandedCards] = useState({});
    const [onlyVerified, setOnlyVerified] = useState(false);
    const [copiedId, setCopiedId] = useState(null);

    // Toggle individual card accordion
    const toggleExpand = (id) => {
      setExpandedCards((prev) => ({ ...prev, [id]: !prev[id] }));
    };

    // Filter questions
    const filteredQuestions = useMemo(() => {
      return questions.filter((q) => {
        // Type filter
        if (selectedType !== 'ALL' && q.type !== selectedType) {
          return false;
        }
        // Verified filter
        if (onlyVerified && !q.is_multiagent_verified) {
          return false;
        }
        // Search query
        if (searchQuery.trim()) {
          const qText = (q.question || '').toLowerCase();
          const ansText = (q.correct_answer || '').toLowerCase();
          const expText = (q.explanation || '').toLowerCase();
          const query = searchQuery.toLowerCase();
          return qText.includes(query) || ansText.includes(query) || expText.includes(query);
        }
        return true;
      });
    }, [questions, selectedType, searchQuery, onlyVerified]);

    // Counts
    const counts = useMemo(() => {
      return {
        all: questions.length,
        mcq: questions.filter((q) => q.type === 'MCQ').length,
        short: questions.filter((q) => q.type === 'SHORT').length,
        long: questions.filter((q) => q.type === 'LONG').length,
        verified: questions.filter((q) => q.is_multiagent_verified).length,
      };
    }, [questions]);

    // Copy question to clipboard
    const copyQuestion = (q) => {
      let text = `Question: ${q.question}\n`;
      if (q.options && q.options.length) {
        text += `Options:\n${q.options.map((opt, i) => `  ${i + 1}. ${opt}`).join('\n')}\n`;
      }
      text += `Correct Answer: ${q.correct_answer}\n`;
      if (q.explanation) text += `Explanation: ${q.explanation}\n`;
      if (q.step_by_step_reasoning) text += `Reasoning: ${q.step_by_step_reasoning}\n`;

      navigator.clipboard.writeText(text).then(() => {
        setCopiedId(q.id);
        setTimeout(() => setCopiedId(null), 2000);
      });
    };

    // Delete question
    const deleteQuestion = async (id) => {
      if (!confirm('Are you sure you want to delete this question?')) return;
      try {
        const res = await fetch(`/questions/${id}/delete/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
          },
        });
        if (res.ok || res.status === 302) {
          setQuestions((prev) => prev.filter((q) => q.id !== id));
        }
      } catch (err) {
        console.error('Failed to delete question:', err);
      }
    };

    return (
      <div className="space-y-4">
        {/* Controls: Filter Tabs & Live Search Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-border">
          {/* Tabs */}
          <div className="flex items-center space-x-1 p-1 rounded-lg bg-muted text-muted-foreground text-xs font-semibold overflow-x-auto">
            {['ALL', 'MCQ', 'SHORT', 'LONG'].map((type) => (
              <button
                key={type}
                onClick={() => setSelectedType(type)}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  selectedType === type
                    ? 'bg-background text-foreground shadow-xs font-bold'
                    : 'hover:text-foreground'
                }`}
              >
                {type === 'ALL' && `All (${counts.all})`}
                {type === 'MCQ' && `MCQ (${counts.mcq})`}
                {type === 'SHORT' && `Short (${counts.short})`}
                {type === 'LONG' && `Long (${counts.long})`}
              </button>
            ))}
          </div>

          {/* Search & Verified filter */}
          <div className="flex items-center space-x-2">
            {counts.verified > 0 && (
              <button
                onClick={() => setOnlyVerified(!onlyVerified)}
                className={`px-2.5 py-1.5 rounded-md text-xs font-medium border transition-colors flex items-center space-x-1.5 ${
                  onlyVerified
                    ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-600 dark:text-emerald-400 font-bold'
                    : 'border-border text-muted-foreground hover:text-foreground'
                }`}
                title="Filter questions verified by multi-agent consensus"
              >
                <i className="fa-solid fa-shield-halved text-[10px]"></i>
                <span className="hidden sm:inline">Verified Only ({counts.verified})</span>
              </button>
            )}

            <div className="relative flex-1 sm:w-64">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search questions..."
                className="w-full pl-7 pr-7 py-1.5 text-xs rounded-md border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
              />
              <i className="fa-solid fa-magnifying-glass absolute left-2.5 top-2 text-muted-foreground text-[10px]"></i>
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-1.5 text-muted-foreground hover:text-foreground text-xs"
                >
                  <i className="fa-solid fa-xmark"></i>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Questions List */}
        {filteredQuestions.length > 0 ? (
          <div className="space-y-4">
            {filteredQuestions.map((q, idx) => {
              const isExpanded = !!expandedCards[q.id];
              return (
                <div
                  key={q.id}
                  className="rounded-xl border border-border bg-card text-card-foreground p-5 sm:p-6 space-y-4 shadow-2xs hover:border-primary/40 transition-colors"
                >
                  {/* Top Bar: Badges and Actions */}
                  <div className="flex items-center justify-between">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span
                        className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${
                          q.type === 'MCQ'
                            ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20'
                            : q.type === 'SHORT'
                            ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                            : 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20'
                        }`}
                      >
                        {q.type}
                      </span>
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-secondary text-secondary-foreground">
                        {q.difficulty}
                      </span>
                      {q.is_multiagent_verified && (
                        <span
                          className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 flex items-center shadow-xs"
                          title="100% Fact-Checked by 4-agent consensus pipeline"
                        >
                          <i className="fa-solid fa-shield-halved mr-1 text-[9px] text-emerald-500"></i>
                          Multi-Agent Verified
                        </span>
                      )}
                    </div>

                    <div className="flex items-center space-x-1 text-muted-foreground">
                      <button
                        onClick={() => copyQuestion(q)}
                        className="p-1.5 rounded-md hover:bg-secondary hover:text-foreground transition-colors"
                        title="Copy question and answer"
                      >
                        {copiedId === q.id ? (
                          <i className="fa-solid fa-check text-emerald-500 text-xs"></i>
                        ) : (
                          <i className="fa-regular fa-copy text-xs"></i>
                        )}
                      </button>
                      <button
                        onClick={() => deleteQuestion(q.id)}
                        className="p-1.5 rounded-md hover:bg-destructive/10 hover:text-destructive transition-colors"
                        title="Delete question"
                      >
                        <i className="fa-solid fa-trash text-xs"></i>
                      </button>
                    </div>
                  </div>

                  {/* Question Text */}
                  <p className="text-sm sm:text-base font-semibold text-foreground leading-relaxed">
                    {q.question}
                  </p>

                  {/* MCQ Options Display */}
                  {q.type === 'MCQ' && q.options && q.options.length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                      {q.options.map((opt, i) => (
                        <div
                          key={i}
                          className="p-3 rounded-xl border border-border bg-secondary/50 hover:bg-secondary text-xs sm:text-sm text-foreground flex items-center shadow-2xs transition-colors"
                        >
                          <span className="w-6 h-6 rounded-full border border-border bg-background flex items-center justify-center font-bold text-xs text-muted-foreground mr-3 flex-shrink-0">
                            {String.fromCharCode(65 + i)}
                          </span>
                          <span className="font-medium leading-snug">{opt}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Collapsible Model Answer & Deep Reasoning */}
                  <div className="pt-1">
                    <button
                      onClick={() => toggleExpand(q.id)}
                      className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs font-semibold transition-colors select-none border border-border"
                    >
                      <span className="flex items-center">
                        <i className="fa-solid fa-brain mr-2 text-primary text-xs"></i>
                        <span>
                          {isExpanded ? 'Hide' : 'Reveal'} Model Answer & Multi-Agent Reasoning
                        </span>
                      </span>
                      <i
                        className={`fa-solid fa-chevron-down text-[10px] transition-transform duration-200 ${
                          isExpanded ? 'rotate-180' : ''
                        }`}
                      ></i>
                    </button>

                    {isExpanded && (
                      <div className="mt-3 p-5 rounded-xl border border-border bg-card space-y-4 text-xs sm:text-sm text-foreground shadow-2xs animate-in fade-in zoom-in-95 duration-150">
                        {/* Correct Answer */}
                        <div>
                          <span className="font-bold text-muted-foreground uppercase text-[10px] tracking-wider block mb-1">
                            Correct / Model Answer:
                          </span>
                          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-900 dark:text-emerald-200 font-semibold text-xs sm:text-sm">
                            {q.correct_answer}
                          </div>
                        </div>

                        {/* Grounding Source Evidence */}
                        {q.grounding_evidence && (
                          <div className="p-3 rounded-lg bg-muted border-l-2 border-primary">
                            <span className="font-bold text-[10px] uppercase text-muted-foreground tracking-wider block mb-0.5">
                              Source Evidence Quote:
                            </span>
                            <p className="italic text-foreground text-xs leading-relaxed">
                              "{q.grounding_evidence}"
                            </p>
                          </div>
                        )}

                        {/* Step-by-Step Reasoning */}
                        {q.step_by_step_reasoning && (
                          <div className="space-y-1">
                            <span className="font-bold text-foreground flex items-center">
                              <i className="fa-solid fa-route mr-1.5 text-primary text-xs"></i>
                              Step-by-Step Deductive Reasoning:
                            </span>
                            <p className="p-3 rounded-lg bg-secondary border border-border text-foreground whitespace-pre-line leading-relaxed font-normal">
                              {q.step_by_step_reasoning}
                            </p>
                          </div>
                        )}

                        {/* Distractor Analysis */}
                        {q.distractor_analysis && Object.keys(q.distractor_analysis).length > 0 && (
                          <div className="space-y-1.5">
                            <span className="font-bold text-foreground flex items-center">
                              <i className="fa-solid fa-magnifying-glass-chart mr-1.5 text-rose-500 text-xs"></i>
                              Why Other Options Are Incorrect (Distractor Analysis):
                            </span>
                            <div className="space-y-1">
                              {Object.entries(q.distractor_analysis).map(([opt, reason], i) => (
                                <div
                                  key={i}
                                  className="p-2.5 rounded-lg bg-destructive/10 border border-destructive/20 text-xs"
                                >
                                  <span className="font-bold text-destructive">
                                    &bull; {opt}:
                                  </span>
                                  <span className="text-foreground ml-1.5">{reason}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Core Explanation */}
                        {q.explanation && (
                          <div>
                            <span className="font-bold text-foreground block mb-0.5">Explanation:</span>
                            <p className="text-muted-foreground leading-relaxed">{q.explanation}</p>
                          </div>
                        )}

                        {/* Key Points */}
                        {q.key_points && q.key_points.length > 0 && (
                          <div>
                            <span className="font-bold text-foreground block mb-1">
                              Key Points / Rubric:
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {q.key_points.map((kp, i) => (
                                <span
                                  key={i}
                                  className="px-2 py-0.5 rounded-md bg-secondary text-secondary-foreground text-[11px] font-medium"
                                >
                                  • {kp}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-16 px-4 rounded-xl border border-dashed border-border bg-card">
            <div className="w-12 h-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center mx-auto mb-3 text-lg">
              <i className="fa-solid fa-circle-question"></i>
            </div>
            <h3 className="text-sm font-bold text-foreground">No questions found</h3>
            <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
              {searchQuery
                ? `No questions matching "${searchQuery}". Try a different keyword.`
                : 'Upload PDFs to this Arena to generate AI questions with multi-agent verification.'}
            </p>
          </div>
        )}
      </div>
    );
  }

  // Robust mount helper (works whether DOMContentLoaded has already fired or not)
  function initQuestionExplorer() {
    const rootEl = document.getElementById('react-question-explorer');
    const dataEl = document.getElementById('arena-questions-data');

    if (rootEl && dataEl && !rootEl.dataset.mounted) {
      rootEl.dataset.mounted = 'true';
      try {
        const questions = JSON.parse(dataEl.textContent || '[]');
        const arenaId = rootEl.getAttribute('data-arena-id');
        const csrfToken = rootEl.getAttribute('data-csrf-token');

        const root = ReactDOM.createRoot(rootEl);
        root.render(
          React.createElement(QuestionExplorer, {
            initialQuestions: questions,
            arenaId: arenaId,
            csrfToken: csrfToken,
          })
        );
      } catch (err) {
        console.error('Error mounting React QuestionExplorer:', err);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initQuestionExplorer);
  } else {
    initQuestionExplorer();
  }
})();

