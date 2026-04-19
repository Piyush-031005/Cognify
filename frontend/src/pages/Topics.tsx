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
    <div className="p-10">
      <h1>Select Topic</h1>

      {topics.map(t => (
        <button
          key={t}
          onClick={() => {
  localStorage.setItem("selectedSubject", subject || "");
  localStorage.setItem("selectedTopic", t);

  // TEMP: abhi subtopic same hi maan le
  localStorage.setItem("selectedSubtopic", t);

  navigate("/quiz");
}}
        >
          {t}
        </button>
      ))}
    </div>
  );
}