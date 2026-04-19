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
      <h1>Select Subtopic</h1>

      {subtopics.map(s => (
        <button
          key={s}
          onClick={() => {
            localStorage.setItem("selectedSubtopic", s);
            navigate("/quiz");
          }}
        >
          {s}
        </button>
      ))}
    </div>
  );
}