// Lightweight localStorage helpers for Cognify (frontend-only)
export type CognifyUser = {
  name: string;
  age: number;
  email: string;
  password: string; // demo only — replace with real auth later
  education: string;
  subjects: string[];
  learningStyle: string;
  confidence: number; // 1-10
  createdAt: string;
};

export type QuestionAnalytics = {
  questionId: number;
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
  perQuestion: QuestionAnalytics[];
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

const USERS_KEY = "cognify.users";
const SESSION_KEY = "cognify.session";
const REPORTS_KEY = "cognify.reports";

export const getUsers = (): CognifyUser[] => {
  try { return JSON.parse(localStorage.getItem(USERS_KEY) || "[]"); } catch { return []; }
};
export const saveUser = (u: CognifyUser) => {
  const all = getUsers().filter(x => x.email !== u.email);
  all.push(u);
  localStorage.setItem(USERS_KEY, JSON.stringify(all));
};
export const findUser = (email: string) => getUsers().find(u => u.email === email);

export const setSession = (email: string) => localStorage.setItem(SESSION_KEY, email);
export const getSession = () => localStorage.getItem(SESSION_KEY);
export const clearSession = () => localStorage.removeItem(SESSION_KEY);
export const getCurrentUser = (): CognifyUser | null => {
  const e = getSession();
  return e ? findUser(e) ?? null : null;
};

export const getReports = (): CognifyReport[] => {
  try { return JSON.parse(localStorage.getItem(REPORTS_KEY) || "[]"); } catch { return []; }
};
export const saveReport = (r: CognifyReport) => {
  const id = Date.now().toString();

  const newReport = {
    ...r,
    id,   // 🔥 ADD THIS
    takenAt: new Date().toISOString()
  };

  const all = getReports();
  all.unshift(newReport);

  localStorage.setItem(REPORTS_KEY, JSON.stringify(all));

  return id;   // 🔥 VERY IMPORTANT
};
export const getReport = (id: string) => 
  getReports().find(r => r.id === id);