import { QUESTIONS } from "./questions";
import type { CognifyReport, QuestionAnalytics } from "./storage";

// Convert raw per-question analytics into a cognitive report.
export function analyze(perQuestion: QuestionAnalytics[], userEmail: string): CognifyReport {
  const total = perQuestion.length || 1;

  // averages
  const avgTime = perQuestion.reduce((a, b) => a + b.responseTimeMs, 0) / total;
  const avgIdle = perQuestion.reduce((a, b) => a + b.idleTimeMs, 0) / total;
  const avgChanges = perQuestion.reduce((a, b) => a + b.changedAnswerCount, 0) / total;

  // group by question type
  const byType = (t: string) =>
    perQuestion.filter(p => QUESTIONS.find(q => q.id === p.questionId)?.type === t);

  const conceptualQs = byType("conceptual");
  const memorizedQs  = byType("memorized");
  const applicationQs = byType("application");

  const ratio = (arr: QuestionAnalytics[]) =>
    arr.length === 0 ? 0 : arr.filter(a => a.correct).length / arr.length;

  const conceptual = Math.round(ratio(conceptualQs) * 100);
  const memorized  = Math.round(ratio(memorizedQs)  * 100);
  const applied    = Math.round(ratio(applicationQs) * 100);

  // "fake understanding": got memorized right but failed application/conceptual
  const fakeUnderstanding = Math.max(0, Math.min(100, memorized - Math.round((conceptual + applied) / 2)));

  // hesitation: idle time and answer changes
  const hesitation = Math.min(100, Math.round((avgIdle / 4000) * 60 + avgChanges * 15));
  // confidence: inverse of hesitation, boosted by speed
  const confidence = Math.max(5, Math.min(100, 100 - hesitation + (avgTime < 6000 ? 10 : 0)));
  // overthinking: long response time + multiple changes
  const overthinking = Math.min(100, Math.round((avgTime / 12000) * 60 + avgChanges * 12));

  const pattern: CognifyReport["pattern"] =
    conceptual >= 60 ? "Concept-based" :
    avgChanges >= 1.2 ? "Trial-based" : "Mixed";

  const prediction =
    conceptual < 50
      ? "You may struggle in advanced topics unless conceptual clarity improves."
      : applied < 50
      ? "Strong fundamentals — but practice applying them under pressure."
      : "You're well-positioned for advanced concepts. Keep stretching difficulty.";

  const insights: string[] = [];
  if (hesitation > 55) insights.push("You hesitate before committing answers.");
  if (fakeUnderstanding > 25) insights.push("You rely on memorization under pressure.");
  if (applied > conceptual) insights.push("You perform better on direct questions than application-based ones.");
  if (overthinking > 60) insights.push("You tend to overthink — first instincts are often right.");
  if (confidence > 70 && conceptual > 60) insights.push("You show genuine conceptual confidence.");
  if (insights.length === 0) insights.push("Balanced cognitive profile — keep exploring deeper concepts.");

  return {
    id: crypto.randomUUID(),
    userEmail,
    takenAt: new Date().toISOString(),
    perQuestion,
    scores: { conceptual, memorized, fakeUnderstanding: Math.round(fakeUnderstanding), hesitation, confidence, overthinking },
    pattern,
    prediction,
    insights,
  };
}
