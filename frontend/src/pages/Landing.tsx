import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Brain, Activity, Eye, Sparkles } from "lucide-react";
import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";

const features = [
  { icon: Brain, title: "Cognitive Mapping", desc: "We measure how you think — conceptual vs memorized vs applied." },
  { icon: Activity, title: "Behavioral Signals", desc: "Hesitation, confidence, overthinking — silently tracked." },
  { icon: Eye, title: "Learning Pattern", desc: "Trial-based or concept-based — your true style emerges." },
  { icon: Sparkles, title: "Future Prediction", desc: "Where you'll struggle next, and how to fix it early." },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      {/* ambient lime glows for more lime presence */}
      <div className="pointer-events-none absolute -top-32 -left-32 h-[480px] w-[480px] rounded-full bg-primary/40 blur-[120px]" />
      <div className="pointer-events-none absolute top-[40%] -right-40 h-[520px] w-[520px] rounded-full bg-primary/25 blur-[140px]" />
      <div className="pointer-events-none absolute bottom-0 left-1/3 h-[360px] w-[360px] rounded-full bg-primary-glow/30 blur-[120px]" />
      <Navbar />

      {/* HERO */}
      <section className="relative overflow-hidden grid-bg">
        <div className="container relative grid lg:grid-cols-12 gap-10 py-24 lg:py-32">
          <div className="lg:col-span-7 flex flex-col gap-8">
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
              className="inline-flex items-center gap-2 self-start rounded-full border border-border bg-card px-4 py-1.5 text-sm font-medium">
              <span className="h-2 w-2 rounded-full bg-primary shadow-[0_0_12px_hsl(var(--lime))]" />
              Cognitive Analysis System · v1
            </motion.div>

            <motion.h1 initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.05 }}
              className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold leading-[1.02] tracking-tight">
              Understand <span className="relative inline-block">
                <span className="relative z-10">how</span>
                <span className="absolute inset-x-0 bottom-2 h-4 bg-primary -z-0" />
              </span> you think.
              <br />
              Not just what you answer.
            </motion.h1>

            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.7, delay: 0.15 }}
              className="max-w-xl text-lg text-muted-foreground">
              Cognify silently observes your reasoning patterns — hesitation, confidence, conceptual depth — and turns them into a report that actually understands you.
            </motion.p>

            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.25 }}
              className="flex flex-wrap items-center gap-3">
              <Button asChild size="lg"
                className="group h-14 rounded-2xl bg-primary text-primary-foreground px-7 text-base font-semibold shadow-lime hover:scale-[1.03] hover:bg-primary-glow transition-all">
                <Link to="/auth">
                  Start Analysis
                  <ArrowRight className="ml-1 h-5 w-5 transition-transform group-hover:translate-x-1" />
                </Link>
              </Button>
              <Button asChild variant="ghost" size="lg" className="h-14 rounded-2xl px-6 text-base">
                <a href="#how">How it works</a>
              </Button>
            </motion.div>

            <div className="flex items-center gap-6 pt-4 text-sm text-muted-foreground">
              <div><span className="font-display text-2xl font-bold text-foreground">7</span> smart questions</div>
              <div className="h-8 w-px bg-border" />
              <div><span className="font-display text-2xl font-bold text-foreground">12+</span> behavioral signals</div>
              <div className="h-8 w-px bg-border" />
              <div><span className="font-display text-2xl font-bold text-foreground">1</span> mind-blowing report</div>
            </div>
          </div>

          {/* Visual card */}
          <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8, delay: 0.2 }}
            className="lg:col-span-5 relative">
            <div className="relative rounded-3xl border-2 border-foreground bg-primary p-2 shadow-lime float-soft">
              <div className="rounded-[20px] bg-foreground p-8 text-background">
                <div className="text-xs uppercase tracking-widest text-primary">Cognitive Report</div>
                <div className="mt-1 font-display text-2xl font-bold">Your mind, mapped.</div>

                <div className="mt-6 space-y-4">
                  {[
                    { label: "Conceptual", v: 72 },
                    { label: "Memorized", v: 41 },
                    { label: "Confidence", v: 65 },
                  ].map((m) => (
                    <div key={m.label}>
                      <div className="flex justify-between text-xs font-medium opacity-90">
                        <span>{m.label}</span><span>{m.v}%</span>
                      </div>
                      <div className="mt-1 h-2 rounded-full bg-background/15 overflow-hidden">
                        <motion.div initial={{ width: 0 }} animate={{ width: `${m.v}%` }} transition={{ duration: 1.2, delay: 0.6 }}
                          className="h-full bg-primary" />
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 rounded-xl bg-primary/15 border border-primary/40 p-4 text-sm">
                  <div className="text-primary text-xs uppercase tracking-wider">Insight</div>
                  <div className="mt-1 font-medium">You rely on memorization under pressure.</div>
                </div>
              </div>
            </div>
            <div className="absolute -inset-x-10 -inset-y-6 -z-10 rounded-[40px] bg-primary/40 blur-3xl" />
          </motion.div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="how" className="container py-24">
        <div className="max-w-2xl">
          <div className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">How it works</div>
          <h2 className="mt-2 font-display text-4xl sm:text-5xl font-bold tracking-tight">Silent observation. Loud insight.</h2>
        </div>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((f, i) => (
            <motion.div key={f.title}
              initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.06 }}
              className="group relative rounded-2xl border border-border bg-card p-6 transition-all hover:-translate-y-1 hover:shadow-lime hover:border-primary">
              <div className="grid h-11 w-11 place-items-center rounded-xl bg-primary text-primary-foreground shadow-lime">
                <f.icon className="h-5 w-5" />
              </div>
              <div className="mt-4 font-display text-lg font-semibold">{f.title}</div>
              <div className="mt-1 text-sm text-muted-foreground">{f.desc}</div>
              <div className="absolute inset-x-6 bottom-0 h-px bg-gradient-to-r from-transparent via-primary to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA STRIP */}
      <section className="container pb-24">
        <div className="relative overflow-hidden rounded-3xl bg-foreground text-background p-10 lg:p-14">
          <div className="absolute -right-20 -top-20 h-72 w-72 rounded-full bg-primary blur-3xl opacity-40" />
          <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">Ready to meet your mind?</h3>
              <p className="mt-2 text-background/70 max-w-lg">7 questions. ~3 minutes. One report you'll actually want to read.</p>
            </div>
            <Button asChild size="lg" className="h-14 rounded-2xl bg-primary text-primary-foreground hover:bg-primary-glow shadow-lime px-7 self-start text-base font-semibold">
              <Link to="/auth">Start Analysis <ArrowRight className="ml-1 h-5 w-5" /></Link>
            </Button>
          </div>
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="container py-6 text-sm text-muted-foreground flex justify-between">
          <span>© Cognify</span>
          <span>Designed to reflect cognitive insights, not performance scores.</span>
        </div>
      </footer>
    </div>
  );
}
