import React from "react";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { z } from "zod";
import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { findUser, saveUser, setSession, type CognifyUser } from "@/lib/storage";
import { toast } from "@/hooks/use-toast";

const SUBJECTS = ["Math", "Physics", "Biology", "CS", "History", "Language", "Logic"];
const EDU = ["High School", "Undergrad", "Postgrad", "Self-learner"];
const STYLES = ["Visual", "Reading", "Practice", "Discussion"];

const signupSchema = z.object({
  name: z.string().trim().min(2).max(60),
  age: z.number().int().min(10).max(100),
  email: z.string().trim().email().max(255),
  password: z.string().min(6).max(100),
  education: z.string().min(1),
  subjects: z.array(z.string()).min(1, "Pick at least one subject"),
  learningStyle: z.string().min(1),
  confidence: z.number().min(1).max(10),
});

export default function Auth() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"signin" | "signup">("signup");

  // signup state
  const [form, setForm] = useState<Omit<CognifyUser, "createdAt">>({
    name: "", age: 18, email: "", password: "",
    education: "Undergrad", subjects: [], learningStyle: "Visual", confidence: 6,
  });

  // signin state
  const [signin, setSignin] = useState({ email: "", password: "" });

  const toggleSubject = (s: string) => {
    setForm(f => ({ ...f, subjects: f.subjects.includes(s) ? f.subjects.filter(x => x !== s) : [...f.subjects, s] }));
  };

  const onSignup = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = signupSchema.safeParse(form);
    if (!parsed.success) {
      toast({ title: "Check your details", description: parsed.error.issues[0]?.message ?? "Invalid input", variant: "destructive" });
      return;
    }
    if (findUser(form.email)) {
      toast({ title: "Account exists", description: "Try signing in instead.", variant: "destructive" });
      return;
    }
    saveUser({ ...form, createdAt: new Date().toISOString() });
    setSession(form.email);
    toast({ title: `Welcome, ${form.name}` });
    navigate("/dashboard");
  };

  const onSignin = (e: React.FormEvent) => {
    e.preventDefault();
    const u = findUser(signin.email);
    if (!u || u.password !== signin.password) {
      toast({ title: "Invalid credentials", variant: "destructive" });
      return;
    }
    setSession(u.email);
    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />

      <div className="container grid lg:grid-cols-2 gap-12 py-14 lg:py-20">
        {/* Left pitch */}
        <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}
          className="hidden lg:flex flex-col gap-6 sticky top-28 h-fit">
          <div className="inline-flex items-center gap-2 self-start rounded-full border border-border bg-card px-4 py-1.5 text-sm">
            <span className="h-2 w-2 rounded-full bg-primary" /> Tell us about you
          </div>
          <h1 className="font-display text-5xl font-bold tracking-tight leading-tight">
            The more we know,<br />the deeper we read your mind.
          </h1>
          <p className="text-muted-foreground max-w-md">
            These details help Cognify calibrate its analysis to your background, subjects, and learning style. Nothing leaves your device — yet.
          </p>
          <div className="rounded-2xl border border-border bg-card p-5">
            <div className="text-xs uppercase tracking-widest text-muted-foreground">Privacy-first</div>
            <div className="mt-1 font-medium">Stored locally on your browser. No server.</div>
          </div>
        </motion.div>

        {/* Right form */}
        <div className="flex flex-col gap-6">
          {/* Tabs */}
          <div className="inline-flex self-start rounded-full border border-border p-1 bg-card">
            {(["signup", "signin"] as const).map(t => (
              <button key={t} onClick={() => setMode(t)}
                className={`px-5 py-2 text-sm font-semibold rounded-full transition-all ${mode === t ? "bg-primary text-primary-foreground shadow-lime" : "text-muted-foreground hover:text-foreground"}`}>
                {t === "signup" ? "Create account" : "Sign in"}
              </button>
            ))}
          </div>

          {mode === "signup" ? (
            <motion.form key="signup" onSubmit={onSignup}
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
              className="rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-soft space-y-5">
              <div className="grid sm:grid-cols-2 gap-4">
                <Field label="Name">
                  <Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Your full name" maxLength={60} />
                </Field>
                <Field label="Age">
                  <Input type="number" value={form.age} onChange={e => setForm({ ...form, age: Number(e.target.value) })} min={10} max={100} />
                </Field>
              </div>
              <Field label="Email">
                <Input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="you@cognify.app" maxLength={255} />
              </Field>
              <Field label="Password">
                <Input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} placeholder="Min 6 characters" maxLength={100} />
              </Field>

              <Field label="Education level">
                <div className="flex flex-wrap gap-2">
                  {EDU.map(ed => (
                    <Chip key={ed} active={form.education === ed} onClick={() => setForm({ ...form, education: ed })}>{ed}</Chip>
                  ))}
                </div>
              </Field>

              <Field label="Preferred subjects" hint="Pick one or more">
                <div className="flex flex-wrap gap-2">
                  {SUBJECTS.map(s => (
                    <Chip key={s} active={form.subjects.includes(s)} onClick={() => toggleSubject(s)}>{s}</Chip>
                  ))}
                </div>
              </Field>

              <Field label="Learning style">
                <div className="flex flex-wrap gap-2">
                  {STYLES.map(s => (
                    <Chip key={s} active={form.learningStyle === s} onClick={() => setForm({ ...form, learningStyle: s })}>{s}</Chip>
                  ))}
                </div>
              </Field>

              <Field label={`Confidence: ${form.confidence}/10`} hint="How confident do you feel learning new topics?">
                <Slider value={[form.confidence]} onValueChange={([v]) => setForm({ ...form, confidence: v })} min={1} max={10} step={1} />
              </Field>

              <Button type="submit" size="lg" className="w-full h-12 rounded-xl bg-primary text-primary-foreground hover:bg-primary-glow shadow-lime font-semibold">
                Create account & continue
              </Button>
            </motion.form>
          ) : (
            <motion.form key="signin" onSubmit={onSignin}
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
              className="rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-soft space-y-5 max-w-md">
              <Field label="Email">
                <Input type="email" value={signin.email} onChange={e => setSignin({ ...signin, email: e.target.value })} />
              </Field>
              <Field label="Password">
                <Input type="password" value={signin.password} onChange={e => setSignin({ ...signin, password: e.target.value })} />
              </Field>
              <Button type="submit" size="lg" className="w-full h-12 rounded-xl bg-primary text-primary-foreground hover:bg-primary-glow shadow-lime font-semibold">
                Sign in
              </Button>
            </motion.form>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <Label className="text-sm font-semibold">{label}</Label>
      {children}
      {hint && <div className="text-xs text-muted-foreground">{hint}</div>}
    </div>
  );
}

function Chip({ active, children, onClick }: { active?: boolean; children: React.ReactNode; onClick?: () => void }) {
  return (
    <button type="button" onClick={onClick}
      className={`px-3.5 py-1.5 rounded-full text-sm border transition-all
        ${active
          ? "bg-primary text-primary-foreground border-primary shadow-lime"
          : "bg-card text-foreground border-border hover:border-primary hover:-translate-y-0.5"}`}>
      {children}
    </button>
  );
}
