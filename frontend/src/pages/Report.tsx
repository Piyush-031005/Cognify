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
    document.documentElement.classList.add("theme-report");
    return () => document.documentElement.classList.remove("theme-report");
  }, []);

  if (!user) return <Navigate to="/auth" replace />;
  const [report, setReport] = useState<any>(null);

  useEffect(() => {
    const saved = getReport(id || "");
    if (saved) setReport(saved);
  }, [id]);

  if (!report) return <div className="p-10">Loading report...</div>;

  const s = report.scores;

  const riskBadge =
  s.fakeUnderstanding >= 45
    ? "High Surface Familiarity Risk"
    : s.hesitation >= 45
    ? "Moderate Cognitive Distortion"
    : "Stable Cognitive State";

const teacherDiagnostic =
  report.pattern === "Trial-based"
    ? "Student exhibits recurring trial-resolution dependency under medium uncertainty prompts."
    : report.pattern === "Concept-based"
    ? "Student shows principle-led answer commitment with relatively lower recognition dependence."
    : "Student displays alternating concept recall and option-verification dependency.";

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
    ? "Most answers appear to emerge from principle recognition first, which usually means the learner is relying on internal understanding rather than visible guess navigation."
    : report.pattern === "Trial-based"
    ? "The response stream shows repeated elimination behaviour, comparative checking, and delayed certainty — indicating that answers are often reached after internal negotiation rather than immediate clarity."
    : "The learner shifts between partial intuition and concept recall. Some answers show clarity, while others reveal unstable dependence on option-level recognition.";

const finalConclusion =
  s.conceptual >= 60
    ? "Across the full session, Cognify observed a learner with reasonably strong conceptual anchoring and manageable hesitation. The dominant issue is not lack of understanding, but occasional certainty fluctuations under pressure."
    : s.fakeUnderstanding >= 45 && s.overthinking >= 55
    ? "Across the session, the learner showed repeated signs of visible familiarity without fully stable internal certainty. This usually appears when recognition is present, but deep recall remains inconsistent during pressure moments."
    : s.hesitation >= 45
    ? "The overall stream suggests that hesitation, not knowledge absence, is currently interfering with answer quality. The learner appears to know fragments of the concept but loses decisiveness while committing."
    : "The complete cognitive stream indicates a mixed but recoverable understanding pattern, where some answers are concept-led while others still depend on surface verification.";
  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.06]"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, hsl(var(--foreground)) 0 1px, transparent 1px 4px)"
        }}
      />

      <header className="container relative flex h-16 items-center justify-between border-b-2 border-foreground">
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 text-sm font-semibold hover:text-primary transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to dashboard
        </Link>
        <div className="text-xs uppercase tracking-[0.3em] font-bold">
          Cognitive Report · Vol.1
        </div>
      </header>

      <main className="container max-w-5xl py-10 lg:py-14 space-y-12 relative">
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="text-xs uppercase tracking-[0.25em] font-semibold opacity-70">
            {new Date(report.takenAt).toLocaleString()}
          </div>

          <h1 className="mt-3 font-display text-5xl sm:text-7xl font-bold tracking-tight leading-[0.95]">
            {user.name.split(" ")[0]},
            <br />
            <span className="text-primary">here's how</span>
            <br />
            your mind moved.
          </h1>

<div className="mt-5 inline-flex items-center gap-2 rounded-2xl border border-foreground/20 bg-foreground text-background px-4 py-2 text-sm font-semibold">
  <Brain className="h-4 w-4" /> Pattern:
  <span className="text-primary">{report.pattern}</span>
</div>

<div className="mt-4 inline-flex items-center gap-2 rounded-2xl border border-red-400/20 bg-red-400/10 px-4 py-2 text-sm font-semibold text-red-300">
  <ShieldAlert className="h-4 w-4" /> {riskBadge}
</div>
        </motion.section>

 <Section
  icon={<Brain className="h-4 w-4" />}
  title="Understanding"
  subtitle="How you actually grasp ideas"
>
  <div className="grid gap-4 sm:grid-cols-3">
    <Bar label="Conceptual" v={s.conceptual} accent />
    <Bar label="Memorized" v={s.memorized} />
    <Bar label="Fake understanding" v={s.fakeUnderstanding} accent />
  </div>
</Section>    

<Section
  icon={<Activity className="h-4 w-4" />}
  title="Behavior"
  subtitle="The signals you didn't notice you were sending"
>
  <div className="grid gap-4 sm:grid-cols-3">
    <Bar label="Hesitation" v={s.hesitation} accent />
    <Bar label="Confidence" v={s.confidence} />
    <Bar label="Overthinking" v={s.overthinking} accent />
  </div>
</Section>

        <Section
          icon={<Repeat className="h-4 w-4" />}
          title="Learning pattern"
          subtitle="How you reach answers"
        >
          <div className="rounded-2xl border border-foreground/20 bg-card p-6">
            <div className="font-display text-3xl font-bold">{report.pattern}</div>

            <p className="mt-3 max-w-3xl opacity-80 leading-8 text-lg">
             {learningNarrative}
            </p>
          </div>
        </Section>

        <Section
          icon={<TrendingUp className="h-4 w-4" />}
          title="Prediction"
          subtitle="Where you're heading"
        >
          <div className="rounded-2xl border border-foreground/20 bg-foreground text-background p-7">
            <div className="font-display text-xl sm:text-2xl font-semibold leading-10">
              {predictionText}
            </div>
          </div>
        </Section>

        <Section
  icon={<Brain className="h-4 w-4" />}
  title="Teacher Diagnostic"
  subtitle="Professional classroom interpretation"
>
  <div className="rounded-2xl border border-foreground/20 bg-card p-7 leading-8 text-lg">
    {teacherDiagnostic}
  </div>
</Section>

        <Section
          icon={<Sparkles className="h-4 w-4" />}
          title="Insights"
          subtitle="Plain-language reflections"
        >
          <ul className="space-y-3">
            {(report.insights || []).map((ins: string, i: number) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -6 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.06 }}
                className="flex items-start gap-3 rounded-xl border-l-4 border-primary bg-card px-4 py-3"
              >
                <span className="text-base leading-7">
                  • {ins}
                </span>
              </motion.li>
            ))}
          </ul>
        </Section>

        <Section
          icon={<Activity className="h-4 w-4" />}
          title="Question timeline"
          subtitle="Your moment-by-moment cognition"
        >
          <div className="space-y-4">
            {report.perQuestion && report.perQuestion.length > 0 ? (
              (report.perQuestion || []).filter(Boolean).map((p: any, i: number) => (
                <div
                  key={i}
                  className="rounded-2xl border border-foreground/20 bg-card px-5 py-4"
                >
                  <div className="font-semibold text-lg">
                    Q{i + 1}: {p.question_text || p.question || "No question"}
                  </div>

                  <div className="mt-2 text-sm opacity-80">
                    {p.cognitive_flag || "No cognitive flag"}
                  </div>

                  <div className="mt-3 text-sm leading-7 opacity-75">
                    {p.cognitive_flag?.includes("Measured")
  ? "This response arrived with comparatively stable certainty and lower visible friction than the surrounding questions."
  : p.cognitive_flag?.includes("Recovered")
  ? "The learner appears to have reached the answer after comparative elimination, but eventually regained directional control."
  : p.cognitive_flag?.includes("Surface")
  ? "Topic familiarity was visible here, though the internal reasoning depth did not appear fully secure."
  : p.cognitive_flag?.includes("iteration")
  ? "Repeated option scanning and delayed commitment suggest the answer was assembled through elimination."
  : p.cognitive_flag?.includes("turbulence")
  ? "This question triggered visible internal instability, with confidence shifting during commitment."
  : p.cognitive_flag?.includes("drag")
  ? "The learner stayed cognitively engaged but showed prolonged internal resistance before settling."
  : "The response markers indicate a fluctuating certainty profile during this answer."}
                  </div>

                  <div className="mt-2 text-xs opacity-60">
                    Time: {p.response_time?.toFixed?.(1) || p.responseTimeMs / 1000 || 0}s
                    {" • "}
                    Confidence: {Math.round((p.confidence || 0) * 100)}%
                    {" • "}
                    {p.correct ? "Correct" : "Wrong"}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm opacity-70">No per-question timeline data found.</div>
            )}
          </div>
        </Section>

        <Section
  icon={<ShieldAlert className="h-4 w-4" />}
  title="Cognitive Vulnerability"
  subtitle="Where this learner is most likely to break"
>
  <div className="grid sm:grid-cols-3 gap-4">
    <div className="rounded-2xl border p-5 bg-card">
      <div className="text-xs uppercase opacity-60">Main Weakness Area</div>
      <div className="mt-2 text-lg font-bold">{vulnerability.area}</div>
    </div>

    <div className="rounded-2xl border p-5 bg-card">
      <div className="text-xs uppercase opacity-60">Likely Failure Under</div>
      <div className="mt-2 text-lg font-bold">{vulnerability.fail}</div>
    </div>

    <div className="rounded-2xl border p-5 bg-card">
      <div className="text-xs uppercase opacity-60">Recommended Intervention</div>
      <div className="mt-2 text-lg font-bold">{vulnerability.remedy}</div>
    </div>
  </div>
</Section>

        <Section
          icon={<Brain className="h-4 w-4" />} 
          title="System conclusion"
          subtitle="Cognify final psychological interpretation"
        >
          <div className="rounded-2xl border border-foreground/20 bg-card p-7 leading-8 text-lg">
          {finalConclusion}
          </div>
        </Section>

        <div className="flex flex-wrap gap-3 pt-4">
          <Button
            asChild
            size="lg"
            className="h-12 rounded-xl bg-primary text-primary-foreground hover:bg-primary-glow px-6 font-semibold"
          >
            <Link to="/dashboard">Run another analysis</Link>
          </Button>

          <Button
            asChild
            size="lg"
            variant="ghost"
            className="h-12 rounded-xl border border-foreground/30 hover:bg-foreground hover:text-background px-6 font-semibold"
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