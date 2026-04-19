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
    <div className="min-h-screen bg-gradient-to-br from-[#0f172a] to-[#064e3b] text-white p-10">

      <h1 className="text-3xl font-bold mb-2 capitalize">
        {topic}
      </h1>

      <p className="text-gray-400 mb-8">
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
            className="px-6 py-3 bg-green-600 rounded-full hover:bg-green-700"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}