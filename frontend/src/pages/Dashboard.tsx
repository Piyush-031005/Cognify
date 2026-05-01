import { Link, Navigate, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { getCurrentUser, setSession, getReports} from "@/lib/storage";
import { toast } from "@/hooks/use-toast";
import { motion } from "framer-motion";
import { ArrowRight, Brain, Clock, FileText } from "lucide-react";
import InsideLayout from "@/components/InsideLayout";
import { Button } from "@/components/ui/button";

export default function Dashboard() {
  const user = getCurrentUser();
  const navigate = useNavigate();
  if (!user) return <Navigate to="/auth" replace />;

 const API = "http://127.0.0.1:10000";
const [roomCode, setRoomCode] = useState("");
const [teacherRooms, setTeacherRooms] = useState<any[]>([]);
const [reports, setReports] = useState<any[]>([]);

useEffect(() => {
  const allReports = getReports().filter((r) => r.userEmail === user.email);
  setReports(allReports);
}, [user.email]);

const handleJoinRoom = async () => {
  const user = getCurrentUser();

  if (!roomCode.trim()) {
    toast({
      title: "Enter room code",
      variant: "destructive"
    });
    return;
  }

  const res = await fetch(`${API}/join-room`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      room_code: roomCode,
      student_email: user?.email
    })
  });

  const data = await res.json();

  if (!data.success) {
    toast({
      title: data.message || "Invalid room code",
      variant: "destructive"
    });
    return;
  }

  const room = data.room;

  setSession({
    ...user!,
    roomCode: room.room_code,
    assignedSubject: room.subject,
    assignedTopic: room.topic,
    assignedSubtopic: room.subtopic,
    teacherEmail: room.teacher_email
  });

  toast({
    title: "Room joined successfully"
  });

  navigate("/quiz");
};

useEffect(() => {
  let mounted = true;

  async function loadRooms() {
    if (user.role === "teacher") {
      const res = await fetch(`${API}/teacher-rooms/${user.email}`);
      const data = await res.json();

      if (mounted) setTeacherRooms(data);

      useEffect(() => {
  const allReports = getReports().filter((r) => r.userEmail === user.email);
  setReports(allReports);
}, [user.email]);
    }
  }

  loadRooms();

  return () => {
    mounted = false;
  };
}, [user.email, user.role]);

  if (user.role === "teacher") {
  return (
    <InsideLayout>
      <div className="container py-12 lg:py-16">
        <div className="text-sm text-muted-foreground">Teacher Control Panel</div>
        <h1 className="mt-1 font-display text-4xl font-bold">
          Welcome, <span className="text-mint">{user.name}</span>
        </h1>

        <div className="mt-8 rounded-3xl border p-8 bg-card">
          <h2 className="text-2xl font-bold">Create Cognitive Exam Room</h2>
          <p className="text-muted-foreground mt-2">Generate a live room for students to join.</p>

          <Button
            className="mt-5"
            onClick={async () => {
              const res = await fetch(`${API}/create-room`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  teacher_email: user.email,
                  subject: "physics",
                  topic: "mechanics",
                  subtopic: "kinematics"
                })
              });

              const data = await res.json();
              alert("Room Created: " + data.room_code);
              window.location.reload();
            }}
          >
            Create New Room
          </Button>
        </div>

        <div className="mt-10">
          <h3 className="text-2xl font-bold">Your Created Rooms</h3>

          {teacherRooms.length === 0 ? (
            <div className="mt-4 text-muted-foreground">No rooms yet.</div>
          ) : (
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              {teacherRooms.map((room: any) => (
                <div key={room.room_code} className="rounded-2xl border p-5 bg-card">
                  <div className="font-bold text-xl">Room Code: {room.room_code}</div>
                  <div className="text-sm text-muted-foreground mt-1">
                    {room.subject} / {room.topic} / {room.subtopic}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </InsideLayout>
  );
}

return (
    <InsideLayout>
      <div className="container py-12 lg:py-16">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="text-sm text-muted-foreground">Welcome back</div>
          <h1 className="mt-1 font-display text-4xl sm:text-5xl font-bold tracking-tight">
            Hello, <span className="text-mint">{user.name.split(" ")[0]}</span>.
          </h1>
          <p className="mt-2 text-muted-foreground max-w-xl">Ready to meet your mind again? Each session sharpens the picture.</p>
        </motion.div>

        {/* Start card */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.05 }}
          className="mt-10 relative overflow-hidden rounded-3xl border border-mint/20 bg-card p-8 lg:p-10 shadow-mint">
          <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-mint/30 blur-3xl" />
          <div className="relative flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div className="max-w-xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-mint/30 bg-mint/10 px-3 py-1 text-xs text-mint">
                <Brain className="h-3.5 w-3.5" /> 7 questions · ~3 min
              </div>
              <h2 className="mt-3 font-display text-3xl sm:text-4xl font-bold tracking-tight">Start a new analysis</h2>
              <p className="mt-2 text-muted-foreground">We'll silently observe how you think — hesitation, confidence, depth — and turn it into a report.</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-4 self-start">
  <input
    value={roomCode}
    onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
    placeholder="Enter Teacher Room Code"
    className="px-5 h-14 rounded-2xl bg-cyan-deep border border-mint/30 text-white outline-none"
  />

  <button
    onClick={handleJoinRoom}
    className="group h-14 rounded-2xl bg-mint text-cyan-deep hover:bg-mint-glow shadow-mint px-7 text-base font-semibold transition-all hover:scale-[1.03] flex items-center"
  >
    Join Analysis
    <ArrowRight className="ml-1 h-5 w-5 transition-transform group-hover:translate-x-1" />
  </button>
</div>
          </div>
        </motion.div>

        {/* Previous reports */}
        <div className="mt-14">
          <div className="flex items-end justify-between">
            <h3 className="font-display text-2xl font-bold tracking-tight">Previous reports</h3>
            <span className="text-sm text-muted-foreground">{reports.length} total</span>
          </div>

          {reports.length === 0 ? (
            <div className="mt-6 rounded-2xl border border-dashed border-mint/20 p-10 text-center text-muted-foreground">
              No reports yet. Your first analysis will appear here.
            </div>
          ) : (
            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {reports.map(r => (
                <Link key={r.id} to={`/report/${r.id}`}
                  className="group glass-mint rounded-2xl p-5 transition-all hover:-translate-y-1 hover:shadow-mint">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1.5"><Clock className="h-3.5 w-3.5" />{new Date(r.takenAt).toLocaleString()}</span>
                    <FileText className="h-4 w-4 text-mint" />
                  </div>
                  <div className="mt-3 font-display text-lg font-semibold">{r.pattern}</div>
                  <div className="mt-3 font-display text-lg font-semibold">{r.pattern}</div>

<div className="mt-2 inline-flex rounded-full border border-mint/20 px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-mint">
  {r.scores.conceptual >= 60
    ? "High Concept"
    : r.scores.fakeUnderstanding >= 40
    ? "Surface Familiarity"
    : "Mixed Signals"}
</div>

<div className="mt-1 text-sm text-muted-foreground line-clamp-2"></div>
                  <div className="mt-1 text-sm text-muted-foreground line-clamp-2">
  {r.prediction === "Decline"
    ? "Concept strain detected"
    : r.prediction === "Stable"
    ? "Moderate cognitive consistency"
    : "Positive adaptability visible"}
</div>
                  <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
                    <Mini label="Concept" v={r.scores.conceptual} />
                    <Mini label="Confid." v={r.scores.confidence} />
                    <Mini label="Hesit." v={r.scores.hesitation} />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </InsideLayout>
  );
}

function Mini({ label, v }: { label: string; v: number }) {
  return (
    <div className="rounded-lg bg-cyan-deep/60 p-2">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="font-display text-base font-bold text-mint">{v}%</div>
    </div>
  );
}
