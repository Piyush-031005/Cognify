import { useEffect } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Brain, Sparkles, TrendingUp, Activity, Repeat } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getCurrentUser, getReport } from "@/lib/storage";
import { QUESTIONS } from "../lib/questions";

export default function Report() {
  const { id } = useParams();
  const user = getCurrentUser();

  // Apply editorial report theme (yellow + red)
  useEffect(() => {
    document.documentElement.classList.add("theme-report");
    return () => document.documentElement.classList.remove("theme-report");
  }, []);

  if (!user) return <Navigate to="/auth" replace />;
  const report = id ? getReport(id) : null;
  if (!report) return <Navigate to="/dashboard" replace />;

  const s = report.scores;

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      {/* subtle scanline / paper texture */}
      <div className="pointer-events-none absolute inset-0 opacity-[0.06]"
        style={{ backgroundImage: "repeating-linear-gradient(0deg, hsl(var(--foreground)) 0 1px, transparent 1px 4px)" }} />

      {/* Top bar */}
      <header className="container relative flex h-16 items-center justify-between border-b-2 border-foreground">
        <Link to="/dashboard" className="inline-flex items-center gap-2 text-sm font-semibold hover:text-primary transition-colors">
          <ArrowLeft className="h-4 w-4" /> Back to dashboard
        </Link>
        <div className="text-xs uppercase tracking-[0.3em] font-bold">Cognitive Report · Vol.1</div>
      </header>

      <main className="container max-w-5xl py-10 lg:py-14 space-y-12 relative">
        {/* Header */}
        <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <div className="text-xs uppercase tracking-[0.25em] font-semibold opacity-70">{new Date(report.takenAt).toLocaleString()}</div>
          <h1 className="mt-3 font-display text-5xl sm:text-7xl font-bold tracking-tight leading-[0.95]">
            {user.name.split(" ")[0]},<br />
            <span className="text-primary">here's how</span><br />
            your mind moved.
          </h1>
          <div className="mt-5 inline-flex items-center gap-2 rounded-2xl border border-foreground/20 bg-foreground text-background px-4 py-2 text-sm font-semibold">
            <Brain className="h-4 w-4" /> Pattern: <span className="text-primary">{report.pattern}</span>
          </div>
        </motion.section>

        {/* Section: Understanding */}
        <Section icon={<Brain className="h-4 w-4" />} title="Understanding" subtitle="How you actually grasp ideas">
          <div className="grid gap-4 sm:grid-cols-3">
            <Bar label="Conceptual" v={s.conceptual} accent />
            <Bar label="Memorized" v={s.memorized} />
            <Bar label="Fake understanding" v={s.fakeUnderstanding} accent />
          </div>
        </Section>

        {/* Behavior */}
        <Section icon={<Activity className="h-4 w-4" />} title="Behavior" subtitle="The signals you didn't notice you were sending">
          <div className="grid gap-4 sm:grid-cols-3">
            <Bar label="Hesitation" v={s.hesitation} accent />
            <Bar label="Confidence" v={s.confidence} />
            <Bar label="Overthinking" v={s.overthinking} accent />
          </div>
        </Section>

        {/* Learning pattern */}
        <Section icon={<Repeat className="h-4 w-4" />} title="Learning pattern" subtitle="How you reach answers">
          <div className="rounded-2xl border border-foreground/20 bg-card p-6">
            <div className="font-display text-3xl font-bold">{report.pattern}</div>
            <p className="mt-2 max-w-xl opacity-80">
              {report.pattern === "Concept-based"
                ? "You build on principles — strong foundation, scales well to complex topics."
                : report.pattern === "Trial-based"
                ? "You arrive by elimination and iteration — flexible, but vulnerable under pressure."
                : "A mix of intuition and trial — refine the conceptual side to unlock more depth."}
            </p>
          </div>
        </Section>

        {/* Prediction */}
        <Section icon={<TrendingUp className="h-4 w-4" />} title="Prediction" subtitle="Where you're heading">
          <div className="rounded-2xl border border-foreground/20 bg-foreground text-background p-7">
            <div className="font-display text-2xl sm:text-3xl font-semibold leading-snug">
              <span className="text-primary">"</span>{report.prediction}<span className="text-primary">"</span>
            </div>
          </div>
        </Section>

        {/* Insights */}
        <Section icon={<Sparkles className="h-4 w-4" />} title="Insights" subtitle="Plain-language reflections">
          <ul className="space-y-3">
            {report.insights.map((ins, i) => (
              <motion.li key={i} initial={{ opacity: 0, x: -6 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.06 }}
                className="flex items-start gap-3 rounded-xl border-l-4 border-primary bg-card px-4 py-3">
                <span className="text-base">{ins}</span>
              </motion.li>
            ))}
          </ul>
        </Section>

        {/* Timeline */}
        <Section icon={<Activity className="h-4 w-4" />} title="Question timeline" subtitle="Your moment-by-moment cognition">
          <div className="space-y-2">
          {report.perQuestion.map((p, i) => {
        const tone =
    p.idleTimeMs > 4000 ? "Hesitation spike" :
    p.changedAnswerCount > 0 ? "Reconsidered" :
    p.responseTimeMs < 5000 && p.correct ? "Confident" :
    p.correct ? "Steady" : "Unsure";

    return (
      <div key={i}>
      <div>{p.question}</div>   {/* 🔥 DIRECT USE */}
      <div>{tone}</div>
    </div>
  );
})}
          </div>
        </Section>

        <div className="flex flex-wrap gap-3 pt-4">
          <Button asChild size="lg" className="h-12 rounded-xl bg-primary text-primary-foreground hover:bg-primary-glow px-6 font-semibold">
            <Link to="/quiz">Run another analysis</Link>
          </Button>
          <Button asChild size="lg" variant="ghost" className="h-12 rounded-xl border border-foreground/30 hover:bg-foreground hover:text-background px-6 font-semibold">
            <Link to="/dashboard">Back to dashboard</Link>
          </Button>
        </div>
      </main>
    </div>
  );
}

function Section({ icon, title, subtitle, children }: { icon: React.ReactNode; title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <motion.section initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.55 }}>
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.3em] font-bold">
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-foreground text-background">{icon}</span>
        {title}
      </div>
      {subtitle && <div className="mt-2 opacity-75 text-sm">{subtitle}</div>}
      <div className="mt-5">{children}</div>
    </motion.section>
  );
}

function Bar({ label, v, accent }: { label: string; v: number; accent?: boolean }) {
  return (
    <div className="rounded-2xl border border-foreground/20 bg-card p-5">
      <div className="flex justify-between text-sm font-bold">
        <span>{label}</span><span>{v}%</span>
      </div>
      <div className="mt-2 h-2.5 rounded-full bg-background/50 overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${accent ? "bg-primary" : "bg-foreground"}`}
          initial={{ width: 0 }}
          whileInView={{ width: `${v}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1.1, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}
