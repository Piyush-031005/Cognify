import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Subtopics() {
  const [subtopics, setSubtopics] = useState<string[]>([]);
  const navigate = useNavigate();

  const subject = localStorage.getItem("selectedSubject");
  const topic = localStorage.getItem("selectedTopic");

  useEffect(() => {
    fetch(`https://cognify-jkzy.onrender.com/questions/${subject}/${topic}`)
      .then(res => res.json())
      .then(setSubtopics);
  }, [subject, topic]);

  return (
    <div className="p-10">
  <h1 className="text-xl font-bold mb-6">Select Subtopic</h1>

  <div className="flex flex-wrap gap-4">
    {subtopics.map((s) => (
      <button
        key={s}
        onClick={() => {
          localStorage.setItem("selectedSubtopic", s);
          navigate("/quiz");
        }}
        className="px-5 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
      >
        {s}
      </button>
    ))}
  </div>
</div>
  );
}