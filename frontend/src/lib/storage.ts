// Lightweight localStorage helpers for Cognify

export type CognifyUser = {
  name: string;
  age: number;
  email: string;
  password: string;
  education: string;
  subjects: string[];
  learningStyle: string;
  confidence: number;
  createdAt: string;
  role?: string;
  difficulty?: string;
  questionMix?: string;
  questionCount?: number;

  roomCode?: string;
  assignedSubject?: string;
  assignedTopic?: string;
  assignedSubtopic?: string;
  teacherEmail?: string;
};

export type QuestionAnalytics = {
  questionId: number;
  question: string;
  selected: string | null;
  correct: boolean;
  responseTimeMs: number;
  idleTimeMs: number;
  backspaceCount: number;
  changedAnswerCount: number;
};

export type CognifyReport = {
  id: string;
  userEmail: string;
  takenAt: string;
  perQuestion: any[];
  scores: {
    conceptual: number;
    memorized: number;
    fakeUnderstanding: number;
    hesitation: number;
    confidence: number;
    overthinking: number;
  };
  pattern: "Concept-based" | "Trial-based" | "Mixed";
  prediction: string;
  insights: string[];
};

const SESSION_KEY = "cognify.session";
const REPORTS_KEY = "cognify.reports";


// ================= SESSION =================

export const setSession = (user: CognifyUser) =>
  localStorage.setItem(SESSION_KEY, JSON.stringify(user));

export const getSession = (): CognifyUser | null => {
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
  } catch {
    return null;
  }
};

export const clearSession = () => localStorage.removeItem(SESSION_KEY);

export const getCurrentUser = (): CognifyUser | null => {
  return getSession();
};


// ================= REPORTS =================

export const getReports = (): CognifyReport[] => {
  try {
    return JSON.parse(localStorage.getItem(REPORTS_KEY) || "[]");
  } catch {
    return [];
  }
};

export const saveReport = (r: any) => {
  const id = Date.now().toString();
  const user = getCurrentUser();

  const normalizedReport: CognifyReport = {
    id,
    userEmail: user?.email || "",
    takenAt: new Date().toISOString(),

    perQuestion: r.perQuestion || [],

    scores: {
      conceptual: r.scores?.conceptual ?? 0,
      memorized: r.scores?.memorized ?? 0,
      fakeUnderstanding: r.scores?.fakeUnderstanding ?? 0,
      hesitation: r.scores?.hesitation ?? 0,
      confidence: r.scores?.confidence ?? 0,
      overthinking: r.scores?.overthinking ?? 0
    },

    pattern: r.pattern || "Mixed",
    prediction: r.prediction || "Stable",
    insights: r.insights || []
  };

  const all = getReports();
  all.unshift(normalizedReport);

  localStorage.setItem(REPORTS_KEY, JSON.stringify(all));
  return id;
};

export const getReport = (id: string) => {
  return getReports().find((r) => r.id === id);
};