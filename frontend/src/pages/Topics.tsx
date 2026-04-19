import React from "react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Topics() {
  const [topics, setTopics] = useState<string[]>([]);
  const subject = localStorage.getItem("selectedSubject");
  const navigate = useNavigate();

  useEffect(() => {
  if (!subject) {
    console.error("❌ Subject missing");
    return;
  }

  fetch(`https://cognify-jkzy.onrender.com/topics/${subject}`)
    .then(res => res.json())
    .then(setTopics)
    .catch(err => console.error(err));
}, [subject]);

    return (
  <div className="min-h-screen bg-gradient-to-br from-[#0f172a] to-[#064e3b] text-white p-10">

    {/* HEADER */}
    <h1 className="text-3xl font-bold mb-2 capitalize">
      {subject} Dashboard
    </h1>
    <p className="text-gray-400 mb-8">
      Choose a topic to begin your cognitive analysis
    </p>

    {/* TOPICS GRID */}
    <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
      {topics.map(t => (
        <div
          key={t}
          onClick={() => {
            localStorage.setItem("selectedTopic", t);
            navigate("/subtopics");
          }}
          className="cursor-pointer p-6 rounded-2xl bg-[#1e293b] hover:bg-[#334155] transition-all shadow-lg"
        >
          <h2 className="text-xl font-semibold capitalize">
  {t === "mechanics" && "⚙️ "}
  {t === "algebra" && "📐 "}
  {t === "dsa" && "💻 "}
  {t === "geometry" && "📏 "}
  {t === "physics" && "🔬 "}
  {t}
</h2>
          <p className="text-sm text-gray-400 mt-2">
            Explore {t} concepts
          </p>
        </div>
      ))}
    </div>
  </div>
  );
}