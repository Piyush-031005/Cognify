import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Subtopics() {
  const [subtopics, setSubtopics] = useState<string[]>([]);
  const subject = localStorage.getItem("selectedSubject");
  const topic = localStorage.getItem("selectedTopic");
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`https://cognify-jkzy.onrender.com/questions/${subject}/${topic}`)
      .then(res => res.json())
      .then(setSubtopics);
  }, []);

 return (
  <div className="min-h-screen bg-gradient-to-br from-[#0f172a] via-[#064e3b] to-[#022c22] text-white p-10">

    <h1 className="text-4xl font-bold mb-2 capitalize">
      {topic}
    </h1>

    <p className="text-gray-400 mb-10">
      Select a subtopic
    </p>

    <div className="flex gap-4 flex-wrap">

      {subtopics.map(s => (
        <button
          key={s}
          onClick={() => {
            localStorage.setItem("selectedSubtopic", s);
            navigate("/quiz");
          }}
          className="
            px-6 py-3 
            rounded-full 
            bg-green-500/20 
            border border-green-400/30
            hover:bg-green-500/40 
            transition-all
            backdrop-blur-md
          "
        >
          {s}
        </button>
      ))}

    </div>
  </div>
);
}