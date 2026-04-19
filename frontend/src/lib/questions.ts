// Hardcoded smart questions — designed to surface conceptual vs memorized thinking.
// `type` helps the analyzer weight responses.
export type Question = {
  id: number;
  prompt: string;
  options: string[];
  correctIndex: number;
  type: "conceptual" | "memorized" | "application" | "trick";
  explanation?: string;
};

export const QUESTIONS: Question[] = [
  {
    id: 1,
    prompt: "If a moving car suddenly stops, why do passengers lurch forward?",
    options: [
      "Because the car pushes them forward",
      "Because of inertia — their body wants to keep moving",
      "Because of gravity acting forward",
      "Because the seatbelt pulls them",
    ],
    correctIndex: 1,
    type: "conceptual",
  },
  {
    id: 2,
    prompt: "Which of these is the chemical formula for water?",
    options: ["HO2", "H2O", "OH2", "H3O"],
    correctIndex: 1,
    type: "memorized",
  },
  {
    id: 3,
    prompt: "A train travels 60 km in 1.5 hours. What is its average speed?",
    options: ["30 km/h", "40 km/h", "45 km/h", "90 km/h"],
    correctIndex: 1,
    type: "application",
  },
  {
    id: 4,
    prompt: "Which statement best describes 'photosynthesis'?",
    options: [
      "Plants breathing oxygen at night",
      "Plants converting light energy into chemical energy",
      "Plants absorbing water from soil",
      "Plants releasing carbon dioxide",
    ],
    correctIndex: 1,
    type: "conceptual",
  },
  {
    id: 5,
    prompt: "If you double the radius of a circle, the area becomes…",
    options: ["2× larger", "3× larger", "4× larger", "Same"],
    correctIndex: 2,
    type: "application",
  },
  {
    id: 6,
    prompt: "A ball is thrown straight up. At its highest point, its acceleration is…",
    options: [
      "Zero",
      "Equal to gravity, pointing down",
      "Equal to gravity, pointing up",
      "Depends on speed",
    ],
    correctIndex: 1,
    type: "trick",
  },
  {
    id: 7,
    prompt: "Which of these is NOT a programming paradigm?",
    options: ["Functional", "Object-oriented", "Procedural", "Photographic"],
    correctIndex: 3,
    type: "memorized",
  },
];
