import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Brain, Sparkles, TrendingUp, Activity, Repeat, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getCurrentUser, getReport } from "@/lib/storage";

export default function Report() {
  const { id } = useParams();
  const user = getCurrentUser();

  useEffect(() => {
    const currentTheme = localStorage.getItem("theme") || "light";
    const themeClass = currentTheme === "light" ? "theme-light-report" : "theme-inside";
    document.documentElement.classList.add(themeClass);
    return () => {
      document.documentElement.classList.remove("theme-inside", "theme-light-pop", "theme-light-report");
    };
  }, []);

  if (!user) return <Navigate to="/auth" replace />;
  const [report, setReport] = useState<any>(null);
  const [activeReportTab, setActiveReportTab] = useState<string>("overview");

  useEffect(() => {
    const saved = getReport(id || "");
    if (saved) setReport(saved);
  }, [id]);

  if (!report) return <div className="p-10 text-white">Loading report...</div>;

  const s = report.scores;

  const riskBadge =
    s.fakeUnderstanding >= 45
      ? "High Surface Familiarity Risk"
      : s.hesitation >= 45
      ? "Moderate Cognitive Distortion"
      : "Stable Cognitive State";

  const teacherDiagnostic =
    report.pattern === "Trial-based"
      ? "We observed that the learner exhibits recurring trial-resolution dependency under medium uncertainty prompts."
      : report.pattern === "Concept-based"
      ? "We observed that the learner shows principle-led answer commitment with relatively lower recognition dependence."
      : "We observed that the learner displays alternating concept recall and option-verification dependency.";

  const vulnerability =
    s.fakeUnderstanding >= 40
      ? {
          area: "Internal Concept Stability",
          fail: "Indirect application questions",
          remedy: "Deep why-based reinforcement required"
        }
      : s.hesitation >= 45
      ? {
          area: "Decision Commitment",
          fail: "Timed multi-option pressure",
          remedy: "Rapid confidence drills recommended"
        }
      : {
          area: "Mixed Cognitive Consistency",
          fail: "Difficulty spikes",
          remedy: "Progressive layered practice advised"
        };

  const predictionText =
    report.prediction === "Decline"
      ? "Current answer behaviour suggests that deeper questions may continue to feel unstable unless conceptual reinforcement improves."
      : report.prediction === "Stable"
      ? "The learner shows a relatively steady response rhythm, but growth will depend on whether conceptual confidence rises beyond pattern familiarity."
      : "There are visible signs that the learner can improve quickly once concept certainty becomes more consistent.";

  const learningNarrative =
    report.pattern === "Concept-based"
      ? "Most responses suggest answers emerge from principle recognition first, which usually means the learner is relying on internal understanding rather than visible guess navigation."
      : report.pattern === "Trial-based"
      ? "The response stream shows repeated elimination behaviour, comparative checking, and delayed certainty — indicating that answers are often reached after internal negotiation rather than immediate clarity."
      : "The learner shifts between partial intuition and concept recall. Some answers show clarity, while others reveal unstable dependence on option-level recognition.";

  const finalConclusion =
    s.conceptual >= 60
      ? "Across the full session, we observed reasonably strong conceptual anchoring and manageable hesitation. The dominant issue is not lack of understanding, but occasional certainty fluctuations under pressure."
      : s.fakeUnderstanding >= 45 && s.overthinking >= 55
      ? "Across the session, we observed repeated signs of visible familiarity without fully stable internal certainty. This usually appears when recognition is present, but deep recall remains inconsistent during pressure moments."
      : s.hesitation >= 45
      ? "The overall stream suggests that hesitation, not knowledge absence, is currently interfering with answer quality. The learner appears to know fragments of the concept but loses decisiveness while committing."
      : "The complete cognitive stream indicates a mixed but recoverable understanding pattern, where some answers are concept-led while others still depend on surface verification.";

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.06] print:hidden"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, hsl(var(--foreground)) 0 1px, transparent 1px 4px)"
        }}
      />

      <header className="container relative flex h-16 items-center justify-between border-b border-white/5 print:hidden">
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider hover:text-mint transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to dashboard
        </Link>
        <div className="flex items-center gap-4">
          <button
            onClick={() => window.print()}
            className="px-3 py-1.5 rounded-lg border border-white/10 hover:border-white/20 text-xs font-bold text-white transition-all bg-card btn-active-push"
          >
            Export to PDF
          </button>
          <div className="text-[10px] uppercase tracking-[0.3em] font-bold text-muted-foreground hidden sm:block">
            Cognitive Report · Vol.1
          </div>
        </div>
      </header>

      <main className="container max-w-6xl py-10 lg:py-14 space-y-8 relative">
        {/* Cover Section (Always printed first) */}
        <section className="border-b border-white/5 pb-6">
          <div className="text-[10px] uppercase tracking-[0.25em] font-bold text-muted-foreground">
            Session Analysis • {new Date(report.takenAt).toLocaleString()}
          </div>

          <h1 className="mt-3 font-display text-5xl sm:text-6xl font-extrabold tracking-tight leading-[0.95] text-white">
            {user.name},
            <br />
            <span className="opacity-70">here's how</span> your mind moved.
          </h1>

          <div className="mt-5 flex flex-wrap gap-2 print:flex">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/5 border border-white/10 text-white px-3.5 py-1 text-xs font-bold uppercase">
              <Brain className="h-3 w-3 text-muted-foreground" /> Pattern: <span className="text-white font-bold">{report.pattern}</span>
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/5 border border-white/10 text-white px-3.5 py-1 text-xs font-bold uppercase">
              <ShieldAlert className="h-3 w-3 text-rose-400" /> {riskBadge}
            </span>
          </div>
        </section>

        {/* Left Navigation Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Left Sidebar Menu */}
          <div className="lg:col-span-1 space-y-6 print:hidden">
            <div className="rounded-2xl border border-white/10 p-5 bg-card relative overflow-hidden">
              <span className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground block">Cognitive Profile</span>
              <h3 className="text-xs font-bold text-white mt-1 uppercase">100% Completed</h3>
              <div className="flex items-center gap-2 mt-3">
                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-white/60" style={{ width: "100%" }} />
                </div>
              </div>
            </div>

            <nav className="space-y-1">
              {[
                { id: "overview", label: "Overview", icon: <Brain className="h-3.5 w-3.5" /> },
                { id: "understanding", label: "Understanding", icon: <Activity className="h-3.5 w-3.5" /> },
                { id: "behavior", label: "Behavior", icon: <TrendingUp className="h-3.5 w-3.5" /> },
                { id: "prediction", label: "Prediction", icon: <Repeat className="h-3.5 w-3.5" /> },
                { id: "recommendations", label: "Recommendations", icon: <Sparkles className="h-3.5 w-3.5" /> }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveReportTab(tab.id)}
                  className={`w-full text-left px-4 py-3 rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-2.5 relative btn-active-push ${
                    activeReportTab === tab.id
                      ? "bg-white/5 text-white font-bold"
                      : "text-muted-foreground hover:text-white hover:bg-white/5"
                  }`}
                >
                  {tab.icon}
                  {tab.label}
                  {activeReportTab === tab.id && (
                    <span className="absolute left-0 top-1/4 bottom-1/4 w-0.5 bg-white rounded" />
                  )}
                </button>
              ))}
            </nav>
          </div>

          {/* Right Content Panel */}
          <div className="lg:col-span-3 space-y-10 print-content">
            
            {/* 1. OVERVIEW VIEW */}
            <div className={`${activeReportTab === "overview" ? "block" : "hidden"} print:block space-y-6`}>
              <div className="flex items-center justify-between border-b border-white/5 pb-2">
                <h2 className="text-lg font-bold uppercase tracking-wider text-white font-display">Session Overview</h2>
                <span className="text-[10px] text-muted-foreground hidden print:inline">Section 1.0</span>
              </div>
              
              <div className="rounded-2xl border border-white/10 bg-card p-6 leading-relaxed text-sm text-gray-300">
                <h3 className="font-bold text-white mb-2 uppercase text-xs tracking-wider">Final System Conclusion</h3>
                {finalConclusion}
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-card p-6 space-y-2">
                  <h4 className="text-xs uppercase font-bold text-white tracking-wider">Teacher Diagnostic Interpretation</h4>
                  <p className="text-xs text-gray-400 leading-relaxed">{teacherDiagnostic}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-card p-6 space-y-2">
                  <h4 className="text-xs uppercase font-bold text-white tracking-wider">Decision Assembly Narrative</h4>
                  <p className="text-xs text-gray-400 leading-relaxed">{learningNarrative}</p>
                </div>
              </div>
            </div>

            {/* 2. UNDERSTANDING VIEW */}
            <div className={`${activeReportTab === "understanding" ? "block" : "hidden"} print:block space-y-6`}>
              <div className="flex items-center justify-between border-b border-white/5 pb-2">
                <h2 className="text-lg font-bold uppercase tracking-wider text-white font-display">Conceptual Understanding Profile</h2>
                <span className="text-[10px] text-muted-foreground hidden print:inline">Section 2.0</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Calculated metrics mapping depth of grasp, memorization bias, and surface-level familiarity risks.
              </p>

              <div className="grid gap-4 sm:grid-cols-3">
                {/* Conceptual Bar */}
                <div className="rounded-2xl border border-white/10 bg-card p-6 space-y-3">
                  <div className="flex justify-between items-center text-xs font-bold">
                    <span className="text-white">Conceptual Depth</span>
                    <span className="text-white font-bold">{s.conceptual}%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-white/70" style={{ width: `${s.conceptual}%` }} />
                  </div>
                  <div className="pt-2 border-t border-white/5 space-y-1 text-[11px] text-gray-400 font-mono">
                    <span className="font-bold text-white block uppercase text-[9px] tracking-wider mb-1">Evidence Summary</span>
                    <p>✓ Low decision latency</p>
                    <p>✓ Stable response rhythm</p>
                    <p>✓ High correctness on applications</p>
                  </div>
                </div>

                {/* Memorized Bar */}
                <div className="rounded-2xl border border-white/10 bg-card p-6 space-y-3">
                  <div className="flex justify-between items-center text-xs font-bold">
                    <span className="text-white">Memory Dependency</span>
                    <span className="text-white">{s.memorized}%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-white" style={{ width: `${s.memorized}%` }} />
                  </div>
                  <div className="pt-2 border-t border-white/5 space-y-1 text-[11px] text-gray-400 font-mono">
                    <span className="font-bold text-white block uppercase text-[9px] tracking-wider mb-1">Evidence Summary</span>
                    <p>✓ Rapid immediate recall</p>
                    <p>✓ Minimal option switching</p>
                    <p>✓ Terms recognition matches</p>
                  </div>
                </div>

                {/* Fake Understanding Bar */}
                <div className="rounded-2xl border border-white/10 bg-card p-6 space-y-3">
                  <div className="flex justify-between items-center text-xs font-bold">
                    <span className="text-white">Surface Familiarity</span>
                    <span className="text-orange-400">{s.fakeUnderstanding}%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-orange-500" style={{ width: `${s.fakeUnderstanding}%` }} />
                  </div>
                  <div className="pt-2 border-t border-white/5 space-y-1 text-[11px] text-gray-400 font-mono">
                    <span className="font-bold text-white block uppercase text-[9px] tracking-wider mb-1">Evidence Summary</span>
                    <p>✓ High hover times</p>
                    <p>✓ Multi-option scans</p>
                    <p>✓ Drop-off on deep prompts</p>
                  </div>
                </div>
              </div>
            </div>

            {/* 3. BEHAVIOR VIEW */}
            <div className={`${activeReportTab === "behavior" ? "block" : "hidden"} print:block space-y-6`}>
              <div className="flex items-center justify-between border-b border-white/5 pb-2">
                <h2 className="text-lg font-bold uppercase tracking-wider text-white font-display">Decision-Making Behavior</h2>
                <span className="text-[10px] text-muted-foreground hidden print:inline">Section 3.0</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Biometric behavioral signatures tracked transparently during question evaluation.
              </p>

              <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-2xl border border-white/10 bg-card p-5 space-y-3">
                  <div className="flex justify-between items-center text-xs font-bold text-white">
                    <span>Hesitation Index</span>
                    <span className="text-orange-400">{s.hesitation}%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-orange-500" style={{ width: `${s.hesitation}%` }} />
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-card p-5 space-y-3">
                  <div className="flex justify-between items-center text-xs font-bold text-white">
                    <span>Confidence Score</span>
                    <span className="text-white font-bold">{s.confidence}%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-white/70" style={{ width: `${s.confidence}%` }} />
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-card p-5 space-y-3">
                  <div className="flex justify-between items-center text-xs font-bold text-white">
                    <span>Overthinking Rate</span>
                    <span className="text-yellow-400">{s.overthinking}%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-yellow-500" style={{ width: `${s.overthinking}%` }} />
                  </div>
                </div>
              </div>

              {/* Question Timeline */}
              <div className="mt-8 space-y-4">
                <h3 className="text-sm font-bold uppercase tracking-wider text-white font-display">Moment-by-Moment Question Timeline</h3>
                <div className="space-y-3">
                  {report.perQuestion && report.perQuestion.length > 0 ? (
                    report.perQuestion.filter(Boolean).map((p: any, i: number) => (
                      <div key={i} className="rounded-2xl border border-white/10 bg-card p-5 space-y-2">
                        <div className="flex items-center justify-between border-b border-white/5 pb-2">
                          <span className="text-xs font-bold text-white">Q{i + 1}: {p.question_text || p.question || "No prompt available"}</span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${p.correct ? "bg-white/10 text-white" : "bg-red-400/10 text-red-300"}`}>
                            {p.correct ? "CORRECT" : "WRONG"}
                          </span>
                        </div>
                        <p className="text-[11px] text-gray-400 leading-relaxed font-mono">
                          {p.cognitive_flag || "No detailed cognitive flag"}
                        </p>
                        <div className="text-[10px] text-muted-foreground flex gap-4">
                          <span>Decision Latency: <strong>{p.response_time?.toFixed(1) || 0}s</strong></span>
                          <span>Confidence Level: <strong>{Math.round((p.confidence || 0) * 100)}%</strong></span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-muted-foreground">No per-question timeline items recorded.</p>
                  )}
                </div>
              </div>
            </div>

            {/* 4. PREDICTION VIEW */}
            <div className={`${activeReportTab === "prediction" ? "block" : "hidden"} print:block space-y-6`}>
              <div className="flex items-center justify-between border-b border-white/5 pb-2">
                <h2 className="text-lg font-bold uppercase tracking-wider text-white font-display">Cognitive Stability Forecast</h2>
                <span className="text-[10px] text-muted-foreground hidden print:inline">Section 4.0</span>
              </div>

              <div className="rounded-2xl border border-white/10 bg-card p-6 space-y-3">
                <h3 className="text-xs uppercase font-bold text-white tracking-wider">Long-Term Growth Predictor</h3>
                <p className="text-sm text-gray-300 leading-relaxed">{predictionText}</p>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-2xl border border-white/10 bg-card p-5 space-y-1">
                  <span className="text-[9px] uppercase tracking-wider text-muted-foreground block font-bold">Vulnerability Area</span>
                  <span className="text-sm font-bold text-white block capitalize">{vulnerability.area}</span>
                </div>
                <div className="rounded-2xl border border-white/10 bg-card p-5 space-y-1">
                  <span className="text-[9px] uppercase tracking-wider text-muted-foreground block font-bold">Breakdown Trigger</span>
                  <span className="text-sm font-bold text-white block capitalize">{vulnerability.fail}</span>
                </div>
                <div className="rounded-2xl border border-white/10 bg-card p-5 space-y-1">
                  <span className="text-[9px] uppercase tracking-wider text-muted-foreground block font-bold">Targeted Remedy</span>
                  <span className="text-sm font-bold text-white block capitalize">{vulnerability.remedy}</span>
                </div>
              </div>
            </div>

            {/* 5. RECOMMENDATIONS VIEW */}
            <div className={`${activeReportTab === "recommendations" ? "block" : "hidden"} print:block space-y-6`}>
              <div className="flex items-center justify-between border-b border-white/5 pb-2">
                <h2 className="text-lg font-bold uppercase tracking-wider text-white font-display">Clinical Action Plan & Recommendations</h2>
                <span className="text-[10px] text-muted-foreground hidden print:inline">Section 5.0</span>
              </div>

              {/* Insights List */}
              <div className="space-y-3">
                <h3 className="text-xs uppercase font-bold text-white tracking-wider">Investigator Telemetry Insights</h3>
                <ul className="space-y-2">
                  {(report.insights || []).map((ins: string, i: number) => (
                    <li key={i} className="rounded-xl border-l-2 border-white/20 bg-card px-4 py-3 text-xs leading-relaxed text-gray-300 font-mono">
                      {ins}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

          </div>
        </div>

        {/* Navigation CTAs footer (Screen only) */}
        <div className="flex flex-wrap gap-3 pt-6 border-t border-white/5 print:hidden">
          <Button
            asChild
            className="rounded-xl bg-white text-black hover:bg-white/90 px-6 font-bold text-xs btn-active-push"
          >
            <Link to="/dashboard">Run another analysis</Link>
          </Button>

          <Button
            asChild
            variant="ghost"
            className="rounded-xl border border-white/10 hover:bg-white/5 text-xs font-bold text-white px-6 btn-active-push"
          >
            <Link to="/dashboard">Back to dashboard</Link>
          </Button>
        </div>
      </main>
    </div>
  );
}

function Section({
  icon,
  title,
  subtitle,
  children
}: {
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.55 }}
    >
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.3em] font-bold">
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-foreground text-background">
          {icon}
        </span>
        {title}
      </div>
      {subtitle && <div className="mt-2 opacity-75 text-sm">{subtitle}</div>}
      <div className="mt-5">{children}</div>
    </motion.section>
  );
}

function MetricCard({ title, value }: { title: string; value: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="rounded-3xl border border-foreground/20 bg-card p-6 shadow-[0_0_30px_rgba(255,255,255,0.03)]"
    >
      <div className="text-[11px] uppercase tracking-[0.25em] text-primary/70">{title}</div>
      <div className="mt-3 text-5xl font-bold font-display">{value}%</div>
      <div className="mt-3 h-1.5 rounded-full bg-background/40 overflow-hidden">
        <motion.div
          className="h-full bg-primary"
          initial={{ width: 0 }}
          whileInView={{ width: `${value}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1 }}
        />
      </div>
    </motion.div>
  );
}

function Bar({ label, v, accent }: { label: string; v: number; accent?: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="rounded-2xl border border-foreground/20 bg-card px-5 py-4"
    >
      <div className="flex justify-between items-center text-sm font-bold">
        <span>{label}</span>
        <span>{v}%</span>
      </div>

      <div className="mt-3 h-2 rounded-full bg-background/40 overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${accent ? "bg-primary" : "bg-foreground"}`}
          initial={{ width: 0 }}
          whileInView={{ width: `${v}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1 }}
        />
      </div>
    </motion.div>
  );
}