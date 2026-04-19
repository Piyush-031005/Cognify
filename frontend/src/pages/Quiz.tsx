import { useEffect, useMemo, useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import InsideLayout from "../components/InsideLayout";
import { Button } from "@/components/ui/button";
import { getCurrentUser, saveReport, type QuestionAnalytics } from "@/lib/storage";

export default function Quiz() {
  const API = import.meta.env.VITE_API_URL;

  // 🔥 STATE SABSE PEHLE
  const [questions, setQuestions] = useState<any[]>([]);
  const [idx, setIdx] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [analytics, setAnalytics] = useState<QuestionAnalytics[]>([]);
  const [processing, setProcessing] = useState(false);
  const [reflection, setReflection] = useState("");

  const user = getCurrentUser();
  const navigate = useNavigate();

  const startedAt = useRef<number>(Date.now());
  const lastInteract = useRef<number>(Date.now());
  const idleAccum = useRef<number>(0);
  const changes = useRef<number>(0);

  // 🔥 LOAD QUESTIONS (AB SAHI JAGAH)
  useEffect(() => {
  const subject = localStorage.getItem("selectedSubject");
  const topic = localStorage.getItem("selectedTopic");
  const subtopic = localStorage.getItem("selectedSubtopic");
  console.log("SUBJECT:", subject);
console.log("TOPIC:", topic);
console.log("SUBTOPIC:", subtopic);

  fetch(`${API}/questions/${subject}/${topic}/${subtopic}`)
    .then(res => res.json())
    .then(data => {
      console.log("API QUESTIONS:", data);

      // 🔥 random pick 7
      const shuffled = [...data].sort(() => 0.5 - Math.random());
      setQuestions(shuffled.slice(0, 7));
    })
    .catch(err => console.error(err));
}, []);

  // 🔥 SAFETY CHECK
  if (questions.length === 0) {
    return <div>No questions found for this topic</div>;
  }
  if (!questions || questions.length === 0) {
  return (
    <InsideLayout>
      <div className="text-center mt-20 text-white">
        Loading questions...
      </div>
    </InsideLayout>
  );
}
  // 🔥 CURRENT QUESTION
  const q = questions[idx] || null;
  if (!q) {
  return (
    <InsideLayout>
      <div className="text-center mt-20 text-white">
        No question found
      </div>
    </InsideLayout>
  );
}
  const total = questions.length;

  useEffect(() => {
    startedAt.current = Date.now();
    lastInteract.current = Date.now();
    idleAccum.current = 0;
    changes.current = 0;
    setSelected(null);
  }, [idx]);

  useEffect(() => {
    const t = setInterval(() => {
      const since = Date.now() - lastInteract.current;
      if (since > 1500) idleAccum.current += 500;
    }, 500);
    return () => clearInterval(t);
  }, []);

  const choose = (i: number) => {
    if (selected !== null && selected !== i) changes.current += 1;
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

    const entry: QuestionAnalytics = {
      questionId: q.id,
      question: q.prompt,
      selected: q.options[selected],
      correct,
      responseTimeMs,
      idleTimeMs: idleAccum.current,
      backspaceCount: 0,
      changedAnswerCount: changes.current,
    };

    const next = [...analytics, entry];
    setAnalytics(next);

    // ✅ FIXED BACKEND CALL (CLEAN)
    await fetch(`${API}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        response_time: responseTimeMs / 1000,
        attempts: 1,
        confidence: 0.8,
        is_application: 1,
        correct: correct,

        time_taken: responseTimeMs / 1000,
        idle_time: idleAccum.current / 1000,
        rewrite_count: changes.current,
        backspace_count: 0,
        skipped: false,

        reflection: reflection || "No reflection"
      })
    });

    if (idx + 1 < total) {
      setIdx(idx + 1);
    } else {
      setProcessing(true);

      setTimeout(async () => {
        const res = await fetch(`${API}/report`);
        const report = await res.json();

        const weakRes = await fetch(`${API}/weakness`);
        const weakData = await weakRes.json();

        const finalReport: any = {
          id: "",
          userEmail: "",
          takenAt: new Date().toISOString(),
          perQuestion: next,

          scores: {
            conceptual: Math.round((report.understanding_analysis?.[1] || 0) * 100),
            memorized: Math.round((report.understanding_analysis?.[0] || 0) * 100),
            fakeUnderstanding: Math.round((report.understanding_analysis?.[2] || 0) * 100),

            hesitation: Math.round((report.behavior_analysis?.hesitant || 0) * 100),
            confidence: Math.round((report.behavior_analysis?.confident || 0) * 100),
            overthinking: Math.round((report.behavior_analysis?.overthinking || 0) * 100)
          },

          pattern: report.strategy_analysis?.trial
            ? "Trial-based"
            : "Concept-based",

          prediction: report.future_prediction || "",

          insights: [
            `Weakness: ${weakData.weakness}`,
            `Reflection: ${report.reflection_analysis}`
          ]
        };

        const reportId = saveReport(finalReport);
        navigate(`/report/${reportId}`);
      }, 1800);
    }
  };

  const progress = useMemo(() => ((idx) / total) * 100, [idx, total]);

  if (!user) return <Navigate to="/auth" replace />;

  if (questions.length === 0) {
  return (
    <InsideLayout>
      <div className="text-center mt-20 text-white">
        Loading questions...
      </div>
    </InsideLayout>
  );
}

if (!q) {
  return (
    <InsideLayout>
      <div className="text-center mt-20 text-white">
        No question found
      </div>
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
                {q.options.map((opt, i) => (
                  <button
                    key={i}
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
                    onChange={(e) => setReflection(e.target.value)}
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
  return (
    <div className="min-h-[80vh] flex items-center justify-center text-center">
      <div>
        <h2 className="text-2xl font-bold">Analyzing your thinking...</h2>
      </div>
    </div>
  );
}