import React from "react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Topics() {
  const [topics, setTopics] = useState<string[]>([]);
  const subject = localStorage.getItem("selectedSubject");
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`http://127.0.0.1:5000/topics/${subject}`)
      .then(res => res.json())
      .then(setTopics);
  }, []);

  return (
    <div className="p-10">
      <h1>Select Topic</h1>

      {topics.map(t => (
        <button
          key={t}
          onClick={() => {
            localStorage.setItem("selectedTopic", t);
            navigate("/quiz");
          }}
        >
          {t}
        </button>
      ))}
    </div>
  );
}