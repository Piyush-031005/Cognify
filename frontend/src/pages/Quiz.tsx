import { useEffect, useMemo, useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import InsideLayout from "../components/InsideLayout";
import { Button } from "@/components/ui/button";
import { getCurrentUser, saveReport, type QuestionAnalytics } from "@/lib/storage";

export default function Quiz() {
  const API = "http://127.0.0.1:10000";

  const [questions, setQuestions] = useState<any[]>([]);
  const [idx, setIdx] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const analyticsRef = useRef<any[]>([]);
  const [processing, setProcessing] = useState(false);
  const [reflection, setReflection] = useState("");

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


  useEffect(() => {
  const currentUser = getCurrentUser();

  const subject = currentUser?.assignedSubject;
  const topic = currentUser?.assignedTopic;
  const subtopic = currentUser?.assignedSubtopic;
  const difficulty = (currentUser as any)?.difficulty || "mixed";
  const qtype = (currentUser as any)?.questionMix || "mixed";
  const count = (currentUser as any)?.questionCount || 5;

  console.log("LOADING ROOM QUESTIONS => ", subject, topic, subtopic, difficulty, qtype, count);

  if (!subject || !topic || !subtopic) {
    alert("No teacher room assigned.");
    navigate("/dashboard");
    return;
  }

  fetch(`${API}/questions/${subject}/${topic}/${subtopic}/${difficulty}/${qtype}/${count}`)
    .then((res) => res.json())
    .then((data) => {
      setQuestions(data);
    })
    .catch((err) => console.error(err));
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
  attemptsRef.current += 1;

  if (selected === i) {
    sameOptionClicksRef.current += 1;
  }

  if (selected !== null && selected !== i) {
    changes.current += 1;
  }

  setSelected(i);
  lastInteract.current = Date.now();
};

  const submit = async () => {
    if (idx === total - 1 && reflection.trim() === "") {
      alert("Please write your reflection (2-3 lines)");
      return;
    }

    if (selected === null) return;

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

   const submitRes = await fetch(`${API}/submit`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    question_id: q.id,
    question_text: q.prompt,
    student_email: user?.email,
    attempt_id: attemptIdRef.current,

    response_time: responseTimeMs / 1000,
    attempts: attemptsRef.current || 1,
    confidence: dynamicConfidence,
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

const processedResponse = await submitRes.json();
const processedSession = processedResponse.session;

if (processedSession) {
  analyticsRef.current.push(processedSession);
}

console.log("ANALYTICS REF => ", analyticsRef.current);

if (idx + 1 < total) {
  setIdx(idx + 1);
} else {
  setProcessing(true);

  const analyticsSnapshot = [...analyticsRef.current]; 

  setTimeout(async () => {
    const reportRes = await fetch(`${API}/report?student_email=${user?.email}&attempt_id=${attemptIdRef.current}`);
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
  }, 4000);
}
  };

  const progress = useMemo(() => ((idx) / total) * 100, [idx, total]);

  if (!user) return <Navigate to="/auth" replace />;

  if (questions.length === 0) {
    return (
      <InsideLayout>
        <div className="text-center mt-20 text-white">Loading questions...</div>
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

            <div className="mt-8 bg-gray-900 p-8 rounded-xl">
              <h2 className="text-xl font-semibold">{q.prompt}</h2>

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
                    className={`w-full text-left p-3 rounded border ${
                      selected === i ? "bg-green-500" : "bg-gray-800"
                    }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>

              {idx === total - 1 && (
                <div className="mt-6">
                  <label className="text-sm text-gray-400">
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
                    className="w-full mt-2 p-3 rounded bg-black text-white border"
                    rows={3}
                  />
                </div>
              )}

              <div className="mt-6 flex justify-end">
                <Button
                  onClick={submit}
                  disabled={selected === null || (idx === total - 1 && reflection.trim() === "")}
                >
                  {idx + 1 === total ? "Finish & analyze" : "Submit"}
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