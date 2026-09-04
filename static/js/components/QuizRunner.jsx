/**
 * QuizRunner.jsx - Interactive React Quiz Testing Engine with shadcn/ui design tokens,
 * active stopwatch timer, right sidebar for jumping directly to any question,
 * radio card selection, and form auto-submission.
 */

(function () {
  const { useState, useEffect, useMemo } = React;

  function QuizRunner({
    arenaName,
    arenaId,
    attemptId,
    questions,
    csrfToken,
    submitUrl,
    exitUrl,
  }) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [answers, setAnswers] = useState({});
    const [markedForOverview, setMarkedForOverview] = useState({});
    const [secondsElapsed, setSecondsElapsed] = useState(0);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const totalQuestions = questions ? questions.length : 0;
    const currentQ = questions && questions[currentIndex] ? questions[currentIndex] : null;

    // Active stopwatch timer
    useEffect(() => {
      const timer = setInterval(() => {
        setSecondsElapsed((prev) => prev + 1);
      }, 1000);
      return () => clearInterval(timer);
    }, []);

    const formattedTime = useMemo(() => {
      const mins = Math.floor(secondsElapsed / 60);
      const secs = secondsElapsed % 60;
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }, [secondsElapsed]);

    // Handle answer changes
    const handleAnswerChange = (qId, value) => {
      setAnswers((prev) => ({
        ...prev,
        [qId]: value,
      }));
    };

    // Toggle mark for overview
    const toggleMarkOverview = (qId) => {
      setMarkedForOverview((prev) => ({
        ...prev,
        [qId]: !prev[qId],
      }));
    };

    // Calculate answered count
    const answeredCount = useMemo(() => {
      return Object.values(answers).filter((val) => typeof val === 'string' && val.trim().length > 0).length;
    }, [answers]);

    // Calculate marked count
    const markedCount = useMemo(() => {
      return Object.values(markedForOverview).filter(Boolean).length;
    }, [markedForOverview]);

    const progressPercentage = totalQuestions > 0 ? (answeredCount / totalQuestions) * 100 : 0;

    // Form submission
    const handleSubmit = (e) => {
      if (e) e.preventDefault();
      const unanswered = totalQuestions - answeredCount;
      const marked = markedCount;
      if (unanswered > 0 || marked > 0) {
        let confirmMsg = '';
        if (unanswered > 0 && marked > 0) {
          confirmMsg = `You have ${unanswered} unanswered question${unanswered > 1 ? 's' : ''} and ${marked} question${marked > 1 ? 's' : ''} marked for overview. Are you sure you want to submit?`;
        } else if (unanswered > 0) {
          confirmMsg = `You have ${unanswered} unanswered question${unanswered > 1 ? 's' : ''}. Are you sure you want to submit?`;
        } else if (marked > 0) {
          confirmMsg = `You still have ${marked} question${marked > 1 ? 's' : ''} marked for overview. Are you sure you want to submit?`;
        }
        if (!confirm(confirmMsg)) return;
      }
      setIsSubmitting(true);
      document.getElementById('hiddenQuizForm').submit();
    };

    if (!currentQ) {
      return (
        <div className="text-center py-16 text-muted-foreground bg-card rounded-xl border border-border">
          <p>No questions loaded for this attempt.</p>
          <a href={exitUrl} className="mt-3 inline-block text-primary hover:underline text-xs font-semibold">
            Return to Arena
          </a>
        </div>
      );
    }

    const currentAnswer = answers[currentQ.id] || '';

    return (
      <div className="space-y-6">
        {/* Hidden HTML Form submitted to Django */}
        <form id="hiddenQuizForm" method="POST" action={submitUrl} className="hidden">
          <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
          <input type="hidden" name="duration_seconds" value={secondsElapsed} />
          {questions.map((q) => (
            <input
              key={q.id}
              type="hidden"
              name={`question_${q.id}`}
              value={answers[q.id] || ''}
            />
          ))}
        </form>

        {/* Top Header Bar (shadcn Card style) */}
        <div className="rounded-xl border border-border bg-card p-4 sm:p-5 text-card-foreground shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] uppercase font-bold text-primary tracking-wider">
                  Active Timed Quiz
                </span>
                <span className="text-muted-foreground text-xs">&bull;</span>
                <span className="text-xs text-muted-foreground truncate max-w-sm">{arenaName}</span>
              </div>
              <h1 className="text-base sm:text-lg font-bold text-foreground">
                Question {currentIndex + 1} of {totalQuestions}
              </h1>
            </div>

            <div className="flex items-center space-x-3 self-end sm:self-center">
              {/* Timer Display */}
              <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-secondary text-secondary-foreground font-mono text-xs font-bold border border-border shadow-2xs">
                <i className="fa-regular fa-clock text-primary text-xs animate-pulse"></i>
                <span>{formattedTime}</span>
              </div>

              {/* Exit Button */}
              <a
                href={exitUrl}
                onClick={(e) => {
                  if (!confirm('Exit this quiz attempt? Your progress will not be saved.')) {
                    e.preventDefault();
                  }
                }}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-secondary border border-border transition-colors flex items-center space-x-1"
                title="Exit quiz without saving"
              >
                <i className="fa-solid fa-arrow-left text-[10px]"></i>
                <span className="hidden sm:inline">Exit</span>
              </a>
            </div>
          </div>

          {/* Overall Progress Bar */}
          <div className="w-full bg-secondary h-2 rounded-full mt-3 overflow-hidden border border-border/40">
            <div
              className="bg-primary h-full transition-all duration-300 rounded-full"
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
        </div>

        {/* 2-Column Responsive Workspace: Question Center + Right Navigator Sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Main Column: Active Question & Inputs (col-span-8) */}
          <div className="lg:col-span-8 space-y-5">
            
            {/* Question Card */}
            <div className="rounded-xl border border-border bg-card p-6 sm:p-7 text-card-foreground shadow-xs space-y-5">
              
              {/* Card Header: Badges & Actions */}
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`px-2.5 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${
                      currentQ.type === 'MCQ'
                        ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20'
                        : currentQ.type === 'SHORT'
                        ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                        : 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20'
                    }`}
                  >
                    {currentQ.type}
                  </span>
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-secondary text-secondary-foreground border border-border">
                    {currentQ.difficulty}
                  </span>
                  {currentQ.is_multiagent_verified && (
                    <span
                      className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 flex items-center shadow-2xs"
                      title="100% Fact-Checked by 4-Agent consensus pipeline"
                    >
                      <i className="fa-solid fa-shield-halved mr-1 text-[9px] text-emerald-500"></i>
                      Multi-Agent Verified
                    </span>
                  )}
                </div>

                <div className="flex items-center space-x-2.5">
                  <button
                    type="button"
                    onClick={() => toggleMarkOverview(currentQ.id)}
                    className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold border transition-colors ${
                      markedForOverview[currentQ.id]
                        ? 'bg-amber-500/15 border-amber-500/40 text-amber-600 dark:text-amber-400'
                        : 'bg-secondary border-border text-muted-foreground hover:text-foreground hover:bg-secondary/80'
                    }`}
                    title={markedForOverview[currentQ.id] ? "Remove mark for overview" : "Mark this question for overview"}
                  >
                    <i className={`fa-${markedForOverview[currentQ.id] ? 'solid' : 'regular'} fa-bookmark mr-1.5 text-[11px] ${markedForOverview[currentQ.id] ? 'text-amber-500' : ''}`}></i>
                    <span>{markedForOverview[currentQ.id] ? 'Marked for Overview' : 'Mark for Overview'}</span>
                  </button>

                  <span className="text-xs font-bold text-muted-foreground font-mono">
                    {currentIndex + 1} / {totalQuestions}
                  </span>
                </div>
              </div>

              {/* Question Text */}
              <p className="text-base sm:text-lg font-bold text-foreground leading-relaxed">
                {currentQ.question}
              </p>

              {/* Inputs Section */}
              {currentQ.type === 'MCQ' && currentQ.options && currentQ.options.length > 0 ? (
                <div className="space-y-2.5 pt-1">
                  {currentQ.options.map((opt, optIdx) => {
                    const isSelected = currentAnswer === opt;
                    return (
                      <label
                        key={optIdx}
                        onClick={() => handleAnswerChange(currentQ.id, opt)}
                        className={`flex items-center p-3.5 sm:p-4 rounded-xl border cursor-pointer transition-all ${
                          isSelected
                            ? 'border-primary bg-primary/10 ring-1 ring-primary text-foreground font-semibold shadow-xs'
                            : 'border-border bg-secondary hover:bg-secondary/80 text-foreground'
                        }`}
                      >
                        <div
                          className={`w-6 h-6 rounded-full border flex items-center justify-center font-bold text-xs mr-3 flex-shrink-0 transition-colors ${
                            isSelected
                              ? 'border-primary bg-primary text-primary-foreground'
                              : 'border-border bg-background text-muted-foreground'
                          }`}
                        >
                          {String.fromCharCode(65 + optIdx)}
                        </div>
                        <span className="text-xs sm:text-sm leading-normal flex-1">{opt}</span>
                        {isSelected && (
                          <i className="fa-solid fa-circle-check text-primary text-sm ml-2"></i>
                        )}
                      </label>
                    );
                  })}
                </div>
              ) : currentQ.type === 'SHORT' ? (
                <div className="space-y-2 pt-1">
                  <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Write your concise answer (1-3 sentences):
                  </label>
                  <textarea
                    rows="4"
                    value={currentAnswer}
                    onChange={(e) => handleAnswerChange(currentQ.id, e.target.value)}
                    placeholder="Type your answer here..."
                    className="w-full px-4 py-3 rounded-xl border border-input bg-background text-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring leading-relaxed"
                  ></textarea>
                  <div className="flex justify-between text-[11px] text-muted-foreground">
                    <span>Focus on key terminology and clear explanation.</span>
                    <span>{currentAnswer.length} characters</span>
                  </div>
                </div>
              ) : (
                <div className="space-y-2 pt-1">
                  <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Write your detailed analytical answer:
                  </label>
                  <textarea
                    rows="7"
                    value={currentAnswer}
                    onChange={(e) => handleAnswerChange(currentQ.id, e.target.value)}
                    placeholder="Structure your answer addressing the core concepts, reasoning, and context..."
                    className="w-full px-4 py-3 rounded-xl border border-input bg-background text-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring leading-relaxed"
                  ></textarea>
                  <div className="flex justify-between text-[11px] text-muted-foreground">
                    <span>Break into paragraphs or bullet points where appropriate.</span>
                    <span>{currentAnswer.length} characters</span>
                  </div>
                </div>
              )}

            </div>

            {/* Bottom Navigation Buttons */}
            <div className="flex items-center justify-between pt-1">
              <button
                type="button"
                disabled={currentIndex === 0}
                onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
                className={`px-4 py-2 rounded-lg text-xs font-semibold border transition-all ${
                  currentIndex === 0
                    ? 'border-border text-muted-foreground opacity-40 cursor-not-allowed'
                    : 'border-input bg-background text-foreground hover:bg-secondary'
                }`}
              >
                <i className="fa-solid fa-arrow-left mr-1.5 text-[10px]"></i>
                <span>Previous</span>
              </button>

              {/* Center Toggle: Mark for Overview */}
              <button
                type="button"
                onClick={() => toggleMarkOverview(currentQ.id)}
                className={`inline-flex items-center px-3.5 py-2 rounded-lg text-xs font-semibold border transition-colors ${
                  markedForOverview[currentQ.id]
                    ? 'bg-amber-500/15 border-amber-500/40 text-amber-600 dark:text-amber-400'
                    : 'border-border bg-secondary text-muted-foreground hover:text-foreground hover:bg-secondary/80'
                }`}
              >
                <i className={`fa-${markedForOverview[currentQ.id] ? 'solid' : 'regular'} fa-bookmark mr-1.5 text-xs ${markedForOverview[currentQ.id] ? 'text-amber-500' : ''}`}></i>
                <span>{markedForOverview[currentQ.id] ? 'Marked for Overview' : 'Mark for Overview'}</span>
              </button>

              <div className="flex items-center space-x-2">
                {currentIndex < totalQuestions - 1 ? (
                  <button
                    type="button"
                    onClick={() => setCurrentIndex((prev) => Math.min(totalQuestions - 1, prev + 1))}
                    className="px-5 py-2 rounded-lg text-xs font-semibold bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm transition-all flex items-center space-x-1.5"
                  >
                    <span>Next Question</span>
                    <i className="fa-solid fa-arrow-right text-[10px]"></i>
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={handleSubmit}
                    className="px-6 py-2 rounded-lg text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 shadow-md shadow-emerald-600/20 hover:scale-[1.01] active:scale-[0.99] transition-all flex items-center space-x-1.5"
                  >
                    {isSubmitting ? (
                      <>
                        <i className="fa-solid fa-circle-notch fa-spin text-xs"></i>
                        <span>Submitting...</span>
                      </>
                    ) : (
                      <>
                        <span>Submit Quiz & Grade</span>
                        <i className="fa-solid fa-check text-xs"></i>
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>

          </div>

          {/* Right Sidebar: Direct Question Navigator (col-span-4) */}
          <div className="lg:col-span-4 space-y-4 lg:sticky lg:top-20">
            
            {/* Question Jump Box (shadcn Card style) */}
            <div className="rounded-xl border border-border bg-card p-5 text-card-foreground shadow-xs space-y-4">
              
              {/* Header */}
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <div className="flex items-center space-x-2">
                  <i className="fa-solid fa-compass text-primary text-sm"></i>
                  <h2 className="text-xs font-bold uppercase tracking-wider text-foreground">
                    Question Navigator
                  </h2>
                </div>
                <div className="flex items-center space-x-1.5">
                  {markedCount > 0 && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 flex items-center">
                      <i className="fa-solid fa-bookmark mr-1 text-[8px] text-amber-500"></i>
                      {markedCount} Marked
                    </span>
                  )}
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary border border-primary/20">
                    {answeredCount}/{totalQuestions}
                  </span>
                </div>
              </div>

              {/* Legend */}
              <div className="flex items-center justify-between text-[11px] text-muted-foreground pb-1">
                <div className="flex items-center space-x-1">
                  <span className="w-2.5 h-2.5 rounded-full bg-primary ring-2 ring-primary/30"></span>
                  <span>Current</span>
                </div>
                <div className="flex items-center space-x-1">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                  <span>Answered</span>
                </div>
                <div className="flex items-center space-x-1">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                  <span>Marked</span>
                </div>
                <div className="flex items-center space-x-1">
                  <span className="w-2.5 h-2.5 rounded-full bg-muted border border-border"></span>
                  <span>Pending</span>
                </div>
              </div>

              {/* Direct Jump Buttons Grid */}
              <div>
                <span className="block text-[10px] uppercase font-bold text-muted-foreground tracking-wider mb-2">
                  Jump Directly to Any Question:
                </span>
                <div className="grid grid-cols-5 gap-2">
                  {questions.map((q, idx) => {
                    const isAnswered = !!(answers[q.id] && answers[q.id].trim().length > 0);
                    const isCurrent = idx === currentIndex;
                    const isMarked = !!markedForOverview[q.id];

                    return (
                      <button
                        key={q.id}
                        type="button"
                        onClick={() => setCurrentIndex(idx)}
                        className={`relative h-10 rounded-lg text-xs font-bold transition-all flex flex-col items-center justify-center ${
                          isCurrent
                            ? 'bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2 shadow-sm font-extrabold'
                            : isAnswered
                            ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/25 font-bold'
                            : 'bg-secondary text-foreground border border-border hover:bg-muted hover:border-primary/40'
                        } ${isMarked && !isCurrent ? 'ring-2 ring-amber-500/70 border-amber-500' : ''}`}
                        title={`Jump to Question ${idx + 1} (${q.type}) - ${isAnswered ? 'Answered' : 'Unanswered'}${isMarked ? ' • Marked for Overview' : ''}`}
                      >
                        <span>{idx + 1}</span>
                        {isMarked ? (
                          <span className="absolute -top-1.5 -right-1 w-3.5 h-3.5 rounded-full bg-amber-500 text-white text-[8px] flex items-center justify-center shadow-xs" title="Marked for Overview">
                            <i className="fa-solid fa-bookmark text-[7px]"></i>
                          </span>
                        ) : isAnswered && !isCurrent ? (
                          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-500 border border-card flex items-center justify-center"></span>
                        ) : null}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Sidebar Direct Submit Button */}
              <div className="pt-2 border-t border-border">
                <button
                  type="button"
                  disabled={isSubmitting}
                  onClick={handleSubmit}
                  className="w-full py-2.5 px-4 rounded-lg text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 shadow-sm transition-all flex items-center justify-center space-x-1.5"
                >
                  {isSubmitting ? (
                    <>
                      <i className="fa-solid fa-circle-notch fa-spin text-xs"></i>
                      <span>Submitting...</span>
                    </>
                  ) : (
                    <>
                      <i className="fa-solid fa-paper-plane text-[11px]"></i>
                      <span>Finish & Submit ({answeredCount}/{totalQuestions})</span>
                    </>
                  )}
                </button>
              </div>

            </div>

          </div>

        </div>

      </div>
    );
  }

  // Mount helper
  function initQuizRunner() {
    const rootEl = document.getElementById('react-quiz-runner');
    const dataEl = document.getElementById('quiz-questions-data');

    if (rootEl && dataEl && !rootEl.dataset.mounted) {
      rootEl.dataset.mounted = 'true';
      try {
        const questions = JSON.parse(dataEl.textContent || '[]');
        const arenaName = rootEl.getAttribute('data-arena-name');
        const arenaId = rootEl.getAttribute('data-arena-id');
        const attemptId = rootEl.getAttribute('data-attempt-id');
        const csrfToken = rootEl.getAttribute('data-csrf-token');
        const submitUrl = rootEl.getAttribute('data-submit-url');
        const exitUrl = rootEl.getAttribute('data-exit-url');

        const root = ReactDOM.createRoot(rootEl);
        root.render(
          React.createElement(QuizRunner, {
            arenaName,
            arenaId,
            attemptId,
            questions,
            csrfToken,
            submitUrl,
            exitUrl,
          })
        );
      } catch (err) {
        console.error('Error mounting React QuizRunner:', err);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initQuizRunner);
  } else {
    initQuizRunner();
  }
})();
