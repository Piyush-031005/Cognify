import { useState, useEffect, useRef } from "react";

interface TextScramblerProps {
  text: string;
  className?: string;
  triggerOn?: "hover" | "mount" | "both";
}

export default function TextScrambler({ text, className, triggerOn = "both" }: TextScramblerProps) {
  const [display, setDisplay] = useState(text);
  const intervalRef = useRef<number | null>(null);
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%-+*[]{}";

  const trigger = () => {
    let iteration = 0;
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
    }
    
    intervalRef.current = window.setInterval(() => {
      setDisplay(
        text
          .split("")
          .map((char, index) => {
            if (char === " ") return " ";
            if (index < iteration) return text[index];
            return chars[Math.floor(Math.random() * chars.length)];
          })
          .join("")
      );
      
      if (iteration >= text.length) {
        if (intervalRef.current !== null) {
          window.clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
      iteration += 1 / 3;
    }, 25);
  };

  useEffect(() => {
    if (triggerOn === "mount" || triggerOn === "both") {
      trigger();
    }
    return () => {
      if (intervalRef.current !== null) {
        window.clearInterval(intervalRef.current);
      }
    };
  }, [text, triggerOn]);

  const handleMouseEnter = () => {
    if (triggerOn === "hover" || triggerOn === "both") {
      trigger();
    }
  };

  return (
    <span onMouseEnter={handleMouseEnter} className={className}>
      {display}
    </span>
  );
}
