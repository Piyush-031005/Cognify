import { useEffect, useMemo, useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import InsideLayout from "../components/InsideLayout";
import { Button } from "@/components/ui/button";
import { getCurrentUser, saveReport, type QuestionAnalytics } from "@/lib/storage";
import { toast } from "@/hooks/use-toast";

export default function Quiz() {
  const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:10000";

  const [questions, setQuestions] = useState<any[]>([]);
  const [idx, setIdx] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const analyticsRef = useRef<any[]>([]);
  const [processing, setProcessing] = useState(false);
  const [reflection, setReflection] = useState("");
  
  const [isLoading, setIsLoading] = useState(true);
  const [loadingState, setLoadingState] = useState("Analyzing cognitive memory history...");
  const [manualConfidence, setManualConfidence] = useState<number>(0.7);
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes default
  const [isSubmitting, setIsSubmitting] = useState(false);

  const user = getCurrentUser();
  const navigate = useNavigate();

  const startedAt = useRef<number>(Date.now());
  const lastInteract = useRef<number>(Date.now());
  const idleAccum = useRef<number>(0);
  const changes = useRef<number>(0);

  const attemptsRef = useRef<number>(0);
  const backspaceRef = useRef<number>(0);
  const focusLostRef = useRef<number>(0);
  const hoverCountRef = useRef<number>(0);
  const sameOptionClicksRef = useRef<number>(0);
  const hoveredOptionsRef = useRef<Set<number>>(new Set());
  const attemptIdRef = useRef<string>(Date.now().toString() + "_" + Math.floor(Math.random()*10000));

  // Rotate loading stage texts
  useEffect(() => {
    if (!isLoading) return;
    const stages = [
      "Analyzing cognitive memory history...",
      "Compiling adaptive item response blueprint...",
      "Selecting calibrated questions..."
    ];
    let step = 0;
    const interval = setInterval(() => {
      step = (step + 1) % stages.length;
      setLoadingState(stages[step]);
    }, 1500);
    return () => clearInterval(interval);
  }, [isLoading]);

  // Countdown timer
  useEffect(() => {
    if (timeLeft <= 0) {
      toast({ title: "Time is up! Submitting automatically.", variant: "destructive" });
      submit();
      return;
    }
    const timer = setInterval(() => {
      setTimeLeft(prev => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [timeLeft]);

  useEffect(() => {
    const fetchQuestions = async () => {
      const currentUser = getCurrentUser();
      const roomCode = currentUser?.roomCode;

      if (!roomCode) {
        toast({ title: "No room assigned.", variant: "destructive" });
        navigate("/dashboard");
        return;
      }

      try {
        setIsLoading(true);
        const res = await fetch(`${API}/room-questions/${roomCode}`);
        if (!res.ok) {
          throw new Error("Failed to load questions from server.");
        }
        const data = await res.json();
        console.log("LOCKED QUESTIONS RECEIVED => ", data);
        setQuestions(data);
      } catch (err: any) {
        toast({
          title: "Failed to load quiz",
          description: err.message || "An error occurred",
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchQuestions();
  }, []);

  const total = questions.length;
  const q = questions[idx] || null;

  useEffect(() => {
    startedAt.current = Date.now();
    lastInteract.current = Date.now();
    idleAccum.current = 0;
    changes.current = 0;
    attemptsRef.current = 0;
    backspaceRef.current = 0;
    focusLostRef.current = 0;
    hoverCountRef.current = 0;
    sameOptionClicksRef.current = 0;
    hoveredOptionsRef.current = new Set();
    setSelected(null);
    setManualConfidence(0.7); // reset manual confidence
  }, [idx]);

  useEffect(() => {
    const t = setInterval(() => {
      const since = Date.now() - lastInteract.current;
      if (since > 4000) idleAccum.current += 500;
    }, 500);

    return () => clearInterval(t);
  }, []);

  useEffect(() => {
  const handleKey = () => {
    lastInteract.current = Date.now();
  };

  const handleMove = () => {
    lastInteract.current = Date.now();
  };

  const handleBlur = () => {
    focusLostRef.current += 1;
  };

  window.addEventListener("keydown", handleKey);
  window.addEventListener("mousemove", handleMove);
  window.addEventListener("blur", handleBlur);

  return () => {
    window.removeEventListener("keydown", handleKey);
    window.removeEventListener("mousemove", handleMove);
    window.removeEventListener("blur", handleBlur);
  };
}, []);

  const choose = (i: number) => {
    if (selected === i) {
      sameOptionClicksRef.current += 1;
    }
    setSelected(i);
    attemptsRef.current += 1;
    lastInteract.current = Date.now();
  };

  const submit = async () => {
    if (idx === total - 1 && reflection.trim() === "") {
      toast({ title: "Please write your reflection (2-3 lines)", variant: "destructive" });
      return;
    }

    if (selected === null) return;
    setIsSubmitting(true);

    try {
      const responseTimeMs = Date.now() - startedAt.current;
      const correct = selected === q.correctIndex;

      const dynamicConfidence = Math.max(
        0.35,
        Math.min(
          0.95,
          0.88
            - changes.current * 0.08
            - backspaceRef.current * 0.015
            - focusLostRef.current * 0.06
            - (idleAccum.current / 1000) * 0.01
            - hoverCountRef.current * 0.008
            - sameOptionClicksRef.current * 0.02
            - attemptsRef.current * 0.015
            - (reflection.trim().length < 20 && idx === total - 1 ? 0.05 : 0)
        )
      );

      // Combine manual confidence selection and behavioral signature confidence
      const finalConfidence = Math.round(((manualConfidence * 0.6) + (dynamicConfidence * 0.4)) * 100) / 100;

      const submitRes = await fetch(`${API}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: q.id,
          question_text: q.prompt,
          student_email: user?.email,
          attempt_id: attemptIdRef.current,
          room_code: user?.roomCode,
          subject: user?.assignedSubject,
          topic: user?.assignedTopic,
          subtopic: user?.assignedSubtopic,
          selected_option_index: selected,

          response_time: responseTimeMs / 1000,
          attempts: attemptsRef.current || 1,
          confidence: finalConfidence,
          is_application: q.prompt.length > 25 ? 1 : 0,
          correct: correct,

          time_taken: responseTimeMs / 1000,
          idle_time: idleAccum.current / 1000,
          rewrite_count: changes.current,
          backspace_count: backspaceRef.current,
          skipped: selected === null,

          reflection: idx === total - 1 ? reflection : "",
          hover_count: hoverCountRef.current,
          same_option_clicks: sameOptionClicksRef.current,
          reflection_length: idx === total - 1 ? reflection.trim().length : 30
        })
      });

      if (!submitRes.ok) {
        throw new Error("Failed to submit response to the server.");
      }

      const processedResponse = await submitRes.json();
      const processedSession = processedResponse.session || (processedResponse.data && processedResponse.data.session);

      if (processedSession) {
        analyticsRef.current.push(processedSession);
      }

      console.log("ANALYTICS REF => ", analyticsRef.current);

      if (idx + 1 < total) {
        const isAdaptive = user?.assessmentStrategy && user.assessmentStrategy.startsWith("adaptive_");
        if (isAdaptive) {
          try {
            const nextQRes = await fetch(`${API}/adaptive-question`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                subject: user?.assignedSubject,
                topic: user?.assignedTopic,
                subtopic: user?.assignedSubtopic,
                difficulty: q.difficulty || "medium",
                correct: correct,
                response_time: responseTimeMs / 1000,
                confidence: finalConfidence,
                hesitation: processedSession?.hesitation_score || 0.3,
                strategy: user?.assessmentStrategy
              })
            });
            if (nextQRes.ok) {
              const nextQData = await nextQRes.json();
              if (nextQData && nextQData.question) {
                const updatedQuestions = [...questions];
                updatedQuestions[idx + 1] = {
                  ...nextQData.question,
                  difficulty: nextQData.difficulty,
                  cognitive_type: nextQData.cognitive_type,
                  subtopic: nextQData.subtopic || user?.assignedSubtopic
                };
                setQuestions(updatedQuestions);
              }
            }
          } catch (err) {
            console.error("Adaptive question selection failed:", err);
          }
        }
        setIdx(idx + 1);
        setIsSubmitting(false);
      } else {
        setProcessing(true);

        setTimeout(async () => {
          try {
            const reportRes = await fetch(`${API}/report?student_email=${user?.email}&attempt_id=${attemptIdRef.current}`);
            if (!reportRes.ok) throw new Error("Failed to fetch evaluation report.");
            const report = await reportRes.json();
            console.log("FULL REPORT FROM BACKEND => ", report);

            const weakRes = await fetch(`${API}/weakness`);
            const weakData = await weakRes.json();

            const finalReport: any = {
              id: "",
              userEmail: "",
              takenAt: new Date().toISOString(),
              perQuestion: report.perQuestion || [],

              scores: {
                conceptual: Math.round((report.conceptual || 0) * 100),
                memorized: Math.round((report.memorized || 0) * 100),
                fakeUnderstanding: Math.round((report.fake || 0) * 100),

                hesitation: Math.round((report.hesitation || 0) * 100),
                confidence: Math.round((report.confidence || 0) * 100),
                overthinking: Math.round((report.overthinking || 0) * 100)
              },

              pattern: report.dominant_pattern || "Mixed",
              prediction: report.future_prediction || "",
              insights: report.insights || [`Weakness: ${weakData.weakness}`]
            };

            console.log("FINAL REPORT => ", finalReport);

            const reportId = saveReport(finalReport);
            navigate(`/report/${reportId}`);
          } catch (err: any) {
            toast({
              title: "Report analysis failed",
              description: err.message || "Could not load final report results.",
              variant: "destructive"
            });
            navigate("/dashboard");
          } finally {
            setIsSubmitting(false);
            setProcessing(false);
          }
        }, 4000);
      }
    } catch (err: any) {
      toast({
        title: "Submission failed",
        description: err.message || "Failed to save quiz answer.",
        variant: "destructive"
      });
      setIsSubmitting(false);
    }
  };

  const progress = useMemo(() => ((idx) / (total || 1)) * 100, [idx, total]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  if (!user) return <Navigate to="/auth" replace />;

  if (isLoading || questions.length === 0) {
    return (
      <InsideLayout>
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-white space-y-6">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
          <div className="text-lg font-medium text-green-400 text-center transition-all duration-300">
            {loadingState}
          </div>
          <p className="text-xs text-muted-foreground">Configuring AI cognitive analytics environment...</p>
        </div>
      </InsideLayout>
    );
  }

  if (!q) {
    return (
      <InsideLayout>
        <div className="text-center mt-20 text-white">No question found</div>
      </InsideLayout>
    );
  }

  return (
    <InsideLayout showNav={!processing}>
      <AnimatePresence mode="wait">
        {processing ? (
          <Processing />
        ) : (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.35 }}
            className="container max-w-3xl py-12 lg:py-16"
          >
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Analyzing cognitive signals</span>
              <span>Question {idx + 1} of {total}</span>
            </div>

            <div className="mt-3 h-1 w-full bg-gray-700 rounded">
              <div
                className="h-full bg-green-400"
                style={{ width: `${progress}%` }}
              />
            </div>

            <div className="mt-8 bg-gray-900 p-8 rounded-xl space-y-6">
              <div className="flex justify-between items-center pb-2 border-b border-white/5">
                <span className="px-2.5 py-1 text-xs rounded bg-white/5 border border-white/10 uppercase font-semibold text-gray-300">
                  Difficulty: {q.difficulty ? q.difficulty : "medium"}
                </span>
                <span className="text-sm font-mono text-rose-400 font-bold">
                  Time Remaining: {formatTime(timeLeft)}
                </span>
              </div>

              <h2 className="text-xl font-semibold leading-relaxed">{q.prompt}</h2>

              <div className="mt-5 space-y-3">
                {q.options.map((opt: string, i: number) => (
                  <button
                    key={i}
                    onMouseEnter={() => {
                      if (!hoveredOptionsRef.current.has(i)) {
                        hoveredOptionsRef.current.add(i);
                        hoverCountRef.current += 1;
                      }
                      lastInteract.current = Date.now();
                    }}
                    onClick={() => choose(i)}
                    className={`w-full text-left p-4 rounded-xl border transition-all duration-200 ${
                      selected === i 
                        ? "bg-green-500/20 text-green-300 border-green-500 font-medium shadow-lg shadow-green-500/5" 
                        : "bg-gray-800 border-white/5 text-gray-300 hover:bg-gray-700/80 hover:border-white/10"
                    }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>

              {/* Confidence Selector */}
              <div className="mt-6 border-t border-white/5 pt-4 space-y-2">
                <label className="text-xs uppercase text-muted-foreground font-semibold block">
                  How confident are you with this answer?
                </label>
                <div className="flex gap-2">
                  {[
                    { label: "Unsure (Low)", value: 0.3 },
                    { label: "Somewhat (Medium)", value: 0.7 },
                    { label: "Certain (High)", value: 1.0 }
                  ].map((item) => (
                    <button
                      key={item.value}
                      type="button"
                      onClick={() => setManualConfidence(item.value)}
                      className={`flex-1 py-2.5 text-xs rounded-xl border transition-all duration-200 ${
                        manualConfidence === item.value
                          ? "bg-green-500/10 text-green-300 border-green-500 shadow-md shadow-green-500/5 font-semibold"
                          : "bg-black/40 border-white/10 text-muted-foreground hover:border-white/20 hover:text-white"
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              {idx === total - 1 && (
                <div className="mt-6 border-t border-white/5 pt-4">
                  <label className="text-sm text-gray-400 font-medium">
                    In 2–3 lines, explain the concept you found most difficult:
                  </label>

                  <textarea
                    value={reflection}
                    onChange={(e) => {
                      setReflection(e.target.value);
                      lastInteract.current = Date.now();
                      if (e.nativeEvent instanceof InputEvent && e.nativeEvent.inputType === "deleteContentBackward") {
                        backspaceRef.current += 1;
                      }
                    }}
                    className="w-full mt-2 p-4 rounded-xl bg-black text-white border border-white/10 focus:border-green-500 focus:outline-none transition-colors"
                    rows={3}
                    placeholder="Provide your cognitive reflection to enable deep insight extraction..."
                  />
                </div>
              )}

              <div className="mt-6 flex justify-end">
                <Button
                  onClick={submit}
                  disabled={selected === null || isSubmitting || (idx === total - 1 && reflection.trim() === "")}
                  className="bg-green-500 hover:bg-green-600 text-black font-semibold rounded-xl px-6 py-2.5 transition-colors disabled:opacity-50"
                >
                  {isSubmitting 
                    ? "Submitting..." 
                    : idx + 1 === total 
                      ? "Finish & Analyze" 
                      : "Submit Answer"}
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </InsideLayout>
  );
}

function Processing() {
  const stages = [
    "Capturing behavioral hesitation markers...",
    "Mapping confidence-response inconsistencies...",
    "Running conceptual depth inference...",
    "Cross-evaluating memory vs reasoning dependency...",
    "Generating cognitive stability forecast..."
  ];

  const [stage, setStage] = useState(0);

  useEffect(() => {
    const t = setInterval(() => {
      setStage((p) => (p < stages.length - 1 ? p + 1 : p));
    }, 750);

    return () => clearInterval(t);
  }, []);

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-6 relative overflow-hidden">
      <div className="absolute inset-0 bg-black" />
      <div className="absolute w-[500px] h-[500px] rounded-full bg-green-500/10 blur-3xl animate-pulse" />

      <div className="relative text-center max-w-3xl">
        <div className="text-[11px] uppercase tracking-[0.45em] text-green-400 mb-6">
          Cognify Neural Engine v2
        </div>

        <h2 className="text-3xl sm:text-5xl font-bold text-white leading-tight">
          Building your
          <span className="text-green-400"> cognitive fingerprint</span>
        </h2>

        <p className="mt-5 text-gray-400 text-lg leading-8">
          We are not evaluating correctness alone.  
          The system is reconstructing how decisions were formed beneath your answers.
        </p>

        <div className="mt-12 space-y-4 text-left">
          {stages.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0.25 }}
              animate={{ opacity: i <= stage ? 1 : 0.25 }}
              className={`rounded-xl border px-5 py-4 ${
                i <= stage
                  ? "border-green-400/40 bg-green-400/5 text-green-300"
                  : "border-gray-800 bg-gray-900 text-gray-600"
              }`}
            >
              {i <= stage ? "✓ " : "• "} {s}
            </motion.div>
          ))}
        </div>

        <div className="mt-10 h-1 w-full bg-gray-800 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-green-400"
            initial={{ width: "0%" }}
            animate={{ width: "100%" }}
            transition={{ duration: 4, ease: "easeInOut" }}
          />
        </div>
      </div>
    </div>
  );
}