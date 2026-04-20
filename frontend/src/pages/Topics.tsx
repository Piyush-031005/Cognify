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
  <div className="min-h-screen bg-gradient-to-br from-[#0f172a] via-[#064e3b] to-[#022c22] text-white p-10">

    {/* HEADER */}
    <h1 className="text-4xl font-bold mb-2">
      {subject?.toUpperCase()} Dashboard
    </h1>

    <p className="text-gray-400 mb-10">
      Choose a topic to begin your cognitive analysis
    </p>

    {/* GRID */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">

      {topics.map(t => (
        <div
          key={t}
          onClick={() => {
            localStorage.setItem("selectedTopic", t);
            navigate("/subtopics");
          }}
          className="
            cursor-pointer 
            rounded-2xl 
            p-6 
            bg-white/5 
            backdrop-blur-md 
            border border-white/10
            hover:bg-white/10 
            transition-all 
            shadow-lg 
            hover:scale-105
          "
        >
          <h2 className="text-xl font-semibold flex items-center gap-2">
            ⚙️ {t}
          </h2>

          <p className="text-gray-400 mt-2 text-sm">
            Explore {t} concepts
          </p>
        </div>
      ))}

    </div>
  </div>
);
}