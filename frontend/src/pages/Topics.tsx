import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Topics() {
  const [topics, setTopics] = useState<string[]>([]);
  const subject = localStorage.getItem("selectedSubject");

  const navigate = useNavigate();

  useEffect(() => {
    if (!subject) return;

    fetch(`https://cognify-jkzy.onrender.com/topics/${subject}`)
      .then(res => res.json())
      .then(data => {
        console.log("TOPICS:", data);
        setTopics(data);
      })
      .catch(err => console.error(err));
  }, [subject]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0f2027] via-[#203a43] to-[#2c5364] text-white p-10">

      {/* TITLE */}
      <h1 className="text-4xl font-bold mb-2 capitalize">
        {subject} Dashboard
      </h1>

      <p className="text-gray-300 mb-10">
        Choose a topic to begin your cognitive analysis
      </p>

      {/* CARDS */}
      <div className="flex gap-6 flex-wrap">
        {topics.map(t => (
          <div
            key={t}
            onClick={() => {
              localStorage.setItem("selectedTopic", t);
              navigate("/subtopics");
            }}
            className="cursor-pointer bg-white/10 backdrop-blur-md border border-white/20 
                       px-6 py-4 rounded-2xl hover:bg-green-400/20 
                       hover:scale-105 transition-all duration-300 
                       hover:shadow-[0_0_20px_rgba(34,197,94,0.5)]"
          >
            <h2 className="text-xl font-semibold flex items-center gap-2 capitalize">
              ⚙️ {t}
            </h2>

            <p className="text-sm text-gray-300">
              Explore {t} concepts
            </p>
          </div>
        ))}
      </div>

      {/* BOTTOM */}
      <div className="mt-16 text-center opacity-80">
        <p className="text-lg italic text-gray-300">
          "The more you think, the sharper you become."
        </p>
      </div>

    </div>
  );
}