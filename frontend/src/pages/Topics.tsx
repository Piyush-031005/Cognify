import { useNavigate } from "react-router-dom";

export default function Topics() {
  const navigate = useNavigate();

  const subject = localStorage.getItem("selectedSubject");

  // ✅ STATIC topics mapping (safe for demo)
  const topicsMap: any = {
    physics: ["mechanics", "thermodynamics", "optics"],
    math: ["algebra", "calculus", "geometry"]
  };

  const topics = topicsMap?.[subject || ""] || [];

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-10">

      {/* TITLE */}
      <div className="text-center mb-16">
  <h1 className="text-5xl font-bold capitalize">
    {subject} Dashboard
  </h1>

  <p className="text-gray-400 mt-3">
    Choose a topic to begin your cognitive analysis
  </p>
</div>

      {/* CARDS */}
      <div className="flex gap-6 flex-wrap justify-center">

        {topics.map((t: string) => (
          <div
            key={t}
            onClick={() => {
              localStorage.setItem("selectedTopic", t);
              navigate("/subtopics");
            }}
            className="
              cursor-pointer 
              bg-[#1a1a1a] 
              border border-[#C6FF33]/30
              px-8 py-6 
              rounded-2xl 
              hover:bg-[#C6FF33] 
              hover:text-black
              transition-all duration-300
              shadow-lg
            "
          >
            <h2 className="text-xl font-semibold capitalize flex gap-2 items-center">
              ⚙️ {t}
            </h2>

            <p className="text-sm opacity-70 mt-2">
              Explore {t} concepts
            </p>
          </div>
        ))}

      </div>

      {/* BOTTOM QUOTE */}
      <div className="mt-24 text-center opacity-60">
        <p className="text-lg italic">
          "The more you think, the sharper you become."
        </p>
      </div>

    </div>
  );
}