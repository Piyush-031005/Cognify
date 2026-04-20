import { useNavigate } from "react-router-dom";

export default function Subtopics() {
  const navigate = useNavigate();

  const subject = localStorage.getItem("selectedSubject");
  const topic = localStorage.getItem("selectedTopic");

  // ✅ STATIC mapping (safe for demo)
  const subtopicsMap: any = {
    physics: {
      mechanics: ["kinematics", "motion", "laws"]
    },
    math: {
      algebra: ["linear", "quadratic", "polynomials"]
    }
  };

  const subtopics =
    subtopicsMap?.[subject || ""]?.[topic || ""] || [];

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-10">

      {/* TITLE */}
      <h1 className="text-5xl font-bold mb-2 capitalize">
        {topic}
      </h1>

      <p className="text-gray-400 mb-10">
        Choose a concept to analyze your thinking
      </p>

      {/* CARDS */}
      <div className="flex gap-6 flex-wrap justify-center">

        {subtopics.map((s: string) => (
          <div
            key={s}
            onClick={() => {
              localStorage.setItem("selectedSubtopic", s);
              navigate("/quiz");
            }}
            className="
              cursor-pointer 
              bg-[#1a1a1a] 
              border border-[#C6FF33]/30
              px-8 py-5 
              rounded-2xl 
              hover:bg-[#C6FF33] 
              hover:text-black
              transition-all duration-300
              shadow-lg
            "
          >
            <h2 className="text-xl font-semibold capitalize">
              {s}
            </h2>

            <p className="text-sm opacity-70">
              Explore {s}
            </p>
          </div>
        ))}

      </div>

      {/* BOTTOM */}
      <div className="mt-24 text-center opacity-60">
        <p className="text-lg italic">
          "Understanding comes from thinking, not memorizing."
        </p>
      </div>

    </div>
  );
}