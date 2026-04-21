export function getRandomQuestions(
  subject: string,
  topic: string,
  subtopic: string,
  count = 7
) {
  const all =
    questionBank?.[subject]?.[topic]?.[subtopic] || [];

  if (all.length === 0) return [];

  const shuffled = [...all].sort(() => 0.5 - Math.random());

  return shuffled.slice(0, count);
}
export type Question = {
  id: number;
  prompt: string;
  options: string[];
  correctIndex: number;
  type: "conceptual" | "application" | "trick" | "memorized";
};

export const questionBank = {
  physics: {
    mechanics: {
      kinematics: [
        {
          id: 1,
          prompt: "A body moving with constant velocity has...",
          options: [
            "Zero acceleration",
            "Constant acceleration",
            "Increasing velocity",
            "Decreasing velocity"
          ],
          correctIndex: 0,
          type: "conceptual"
        },
        {
          id: 2,
          prompt: "If displacement is zero, what can we say?",
          options: [
            "Distance is zero",
            "Distance may not be zero",
            "Velocity is zero",
            "Acceleration is zero"
          ],
          correctIndex: 1,
          type: "trick"
        },

        // 👉 aur 10–15 strong questions yaha add kar
      ],

      dynamics: [
        {
          id: 1,
          prompt: "Force is defined as...",
          options: [
            "Mass × velocity",
            "Mass × acceleration",
            "Energy × time",
            "Work × distance"
          ],
          correctIndex: 1,
          type: "conceptual"
        }
      ]
    }
  },

  cs: {
    dsa: {
      trees: [
        {
          id: 1,
          prompt: "Height of a binary tree with one node is?",
          options: ["0", "1", "2", "Depends"],
          correctIndex: 1,
          type: "conceptual"
        }
      ]
    }
  }
};
