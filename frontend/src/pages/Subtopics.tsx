import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Subtopics() {
  const [subtopics, setSubtopics] = useState<string[]>([]);
  const subject = localStorage.getItem("selectedSubject");
  const topic = localStorage.getItem("selectedTopic");

  const navigate = useNavigate();

  useEffect(() => {
    if (!subject || !topic) return;

    fetch(`https://cognify-jkzy.onrender.com/subtopics/${subject}/${topic}`)
      .then(res => res.json())
      .then(data => {
        console.log("SUBTOPICS:", data);
        setSubtopics(data);
      })
      .catch(err => console.error(err));
  }, [subject, topic]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0f2027] via-[#203a43] to-[#2c5364] text-white p-10">

      {/* TITLE */}
      <h1 className="text-4xl font-bold mb-2 capitalize">
        {topic}
      </h1>

      <p className="text-gray-300 mb-8">
        Choose a concept to analyze your thinking
      </p>

      {/* CARDS */}
      <div className="flex gap-6 flex-wrap">
        {subtopics.map(s => (
          <div
            key={s}
            onClick={() => {
              localStorage.setItem("selectedSubtopic", s);
              navigate("/quiz");
            }}
            className="cursor-pointer bg-white/10 backdrop-blur-md border border-white/20 
                       px-6 py-4 rounded-2xl hover:bg-green-400/20 
                       hover:scale-105 transition-all duration-300 
                       hover:shadow-[0_0_20px_rgba(34,197,94,0.5)]"
          >
            <h2 className="text-xl font-semibold flex items-center gap-2 capitalize">
              ⚡ {s}
            </h2>

            <p className="text-sm text-gray-300">
              Explore {s} concepts
            </p>
          </div>
        ))}
      </div>

      {/* BOTTOM TEXT */}
      <div className="mt-16 text-center opacity-80">
        <p className="text-lg italic text-gray-300">
          "Understanding comes from thinking, not memorizing."
        </p>
      </div>

    </div>
  );
}