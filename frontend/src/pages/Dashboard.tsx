import { Link, Navigate, useNavigate } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { getCurrentUser, setSession, getReports } from "@/lib/storage";
import { toast } from "@/hooks/use-toast";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ArrowRight, Brain, Clock, FileText, Sparkles, AlertTriangle, 
  TrendingUp, Plus, Check, X, Layers, Settings, Users, 
  BarChart2, ShieldAlert, Award, Search, Filter, Eye, Save, RotateCcw, Activity, HelpCircle
} from "lucide-react";
import InsideLayout from "@/components/InsideLayout";
import { Button } from "@/components/ui/button";
import TextScrambler from "@/components/TextScrambler";

const SUBJECT_MAP: Record<string, { label: string; topics: Record<string, { label: string; subtopics: Record<string, string> }> }> = {
  math: {
    label: "Mathematics",
    topics: {
      algebra: {
        label: "Algebra",
        subtopics: { quadratic: "Quadratic" }
      },
      calculus: {
        label: "Calculus",
        subtopics: { derivatives: "Derivatives" }
      },
      probability: {
        label: "Probability",
        subtopics: { distributions: "Distributions" }
      }
    }
  },
  physics: {
    label: "Physics",
    topics: {
      classical_mechanics: {
        label: "Classical Mechanics",
        subtopics: { laws_of_motion: "Laws of Motion" }
      },
      thermodynamics: {
        label: "Thermodynamics",
        subtopics: { heat_transfer: "Heat Transfer" }
      },
      electromagnetism: {
        label: "Electromagnetism",
        subtopics: { circuits: "Circuits" }
      }
    }
  },
  dsa: {
    label: "DSA",
    topics: {
      arrays: {
        label: "Arrays",
        subtopics: { basics: "Basics" }
      },
      linked_lists: {
        label: "Linked Lists",
        subtopics: { singly_linked: "Singly Linked" }
      },
      graphs: {
        label: "Graphs",
        subtopics: { traversals: "Traversals" }
      }
    }
  },
  chemistry: {
    label: "Chemistry",
    topics: {
      organic_chemistry: {
        label: "Organic Chemistry",
        subtopics: { functional_groups: "Functional Groups" }
      },
      physical_chemistry: {
        label: "Physical Chemistry",
        subtopics: { rates: "Rates" }
      },
      inorganic_chemistry: {
        label: "Inorganic Chemistry",
        subtopics: { bonding: "Bonding" }
      }
    }
  },
  biology: {
    label: "Biology",
    topics: {
      genetics: {
        label: "Genetics",
        subtopics: { mendelian_inheritance: "Mendelian Inheritance" }
      },
      cell_biology: {
        label: "Cell Biology",
        subtopics: { organelles: "Organelles" }
      },
      ecology: {
        label: "Ecology",
        subtopics: { ecosystems: "Ecosystems" }
      }
    }
  },
  english: {
    label: "English",
    topics: {
      grammar: {
        label: "Grammar",
        subtopics: { sentence_structure: "Sentence Structure" }
      },
      vocabulary: {
        label: "Vocabulary",
        subtopics: { context_clues: "Context Clues" }
      }
    }
  },
  programming: {
    label: "Programming",
    topics: {
      python: {
        label: "Python",
        subtopics: { core_concepts: "Core Concepts" }
      },
      java: {
        label: "Java",
        subtopics: { oop: "OOP" }
      },
      cpp: {
        label: "C++",
        subtopics: { pointers: "Pointers" }
      }
    }
  },
  dbms: {
    label: "DBMS",
    topics: {
      sql: {
        label: "SQL",
        subtopics: { joins: "Joins" }
      },
      normalization: {
        label: "Normalization",
        subtopics: { normal_forms: "Normal Forms" }
      }
    }
  },
  os: {
    label: "Operating Systems",
    topics: {
      processes: {
        label: "Processes",
        subtopics: { scheduling: "Scheduling" }
      },
      memory_management: {
        label: "Memory Management",
        subtopics: { paging: "Paging" }
      }
    }
  },
  cn: {
    label: "Computer Networks",
    topics: {
      protocols: {
        label: "Protocols",
        subtopics: { tcp_ip: "TCP/IP" }
      }
    }
  },
  ml: {
    label: "Machine Learning",
    topics: {
      supervised_learning: {
        label: "Supervised Learning",
        subtopics: { classification: "Classification" }
      }
    }
  },
  ai: {
    label: "Artificial Intelligence",
    topics: {
      search_algorithms: {
        label: "Search Algorithms",
        subtopics: { heuristics: "Heuristics" }
      }
    }
  },
  aptitude: {
    label: "Aptitude",
    topics: {
      quantitative: {
        label: "Quantitative",
        subtopics: { arithmetic: "Arithmetic" }
      }
    }
  }
};

export default function Dashboard() {
  const user = getCurrentUser();
  const navigate = useNavigate();
  if (!user) return <Navigate to="/auth" replace />;

  const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:10000";
  
  // Navigation tabs for Teacher Workspace
  const [activeMode, setActiveMode] = useState<"observe" | "assess" | "intervene" | "improve" | "designer" | "lifecycle" | "explorer" | "validation">("observe");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // State
  const [reports, setReports] = useState<any[]>([]);
  const [roomCode, setRoomCode] = useState("");
  const [teacherRooms, setTeacherRooms] = useState<any[]>([]);
  const [blueprints, setBlueprints] = useState<any[]>([]);
  const [stats, setStats] = useState({
    total_assessments: 0,
    total_students: 0,
    total_reports: 0,
    average_cognitive_health: 0
  });
  const [loadingStats, setLoadingStats] = useState(true);
  const [wizardStep, setWizardStep] = useState(1);
  
  // Room Creation state
  const [selectedBlueprintId, setSelectedBlueprintId] = useState("");
  
  // Student Telemetry / Room Monitor
  const [selectedMonitorRoom, setSelectedMonitorRoom] = useState("");
  const [monitorStudents, setMonitorStudents] = useState<any[]>([]);
  const [monitorReports, setMonitorReports] = useState<any[]>([]);

  // Assessment Quality Engine state
  const [qualityMetrics, setQualityMetrics] = useState<any[]>([]);

  // Cohort comparison state
  const [cohorts, setCohorts] = useState<any[]>([]);
  const [compareRoomA, setCompareRoomA] = useState("");
  const [compareRoomB, setCompareRoomB] = useState("");

  // Question Lifecycle manager state
  const [lifecycleStatus, setLifecycleStatus] = useState<"Draft" | "AI Validation" | "Teacher Review">("AI Validation");
  const [lifecycleQuestions, setLifecycleQuestions] = useState<any[]>([]);

  // ==========================================
  // QUESTION INTELLIGENCE WORKSPACE STATES
  // ==========================================
  const [selectedQuestionId, setSelectedQuestionId] = useState<number | null>(null);
  const [questionDetail, setQuestionDetail] = useState<any | null>(null);
  const [workspaceLoading, setWorkspaceLoading] = useState(false);
  const [changeReason, setChangeReason] = useState("");
  const [activeAnalyticsTab, setActiveAnalyticsTab] = useState<"qqi" | "telemetry" | "versions" | "concepts" | "audit">("qqi");
  
  // Editor values
  const [editPrompt, setEditPrompt] = useState("");
  const [editOptA, setEditOptA] = useState("");
  const [editOptB, setEditOptB] = useState("");
  const [editOptC, setEditOptC] = useState("");
  const [editOptD, setEditOptD] = useState("");
  const [editCorrectIdx, setEditCorrectIdx] = useState(0);
  const [editExplanation, setEditExplanation] = useState("");
  const [editDifficulty, setEditDifficulty] = useState("medium");
  const [editCognitiveType, setEditCognitiveType] = useState("conceptual");
  const [editConcepts, setEditConcepts] = useState("");
  
  // Preview and prediction states
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [predictingImpact, setPredictingImpact] = useState(false);
  const [impactPrediction, setImpactPrediction] = useState<any | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterSubject, setFilterSubject] = useState("all");
  const [filterDifficulty, setFilterDifficulty] = useState("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [allQuestions, setAllQuestions] = useState<any[]>([]);

  // ==========================================
  // KNOWLEDGE GRAPH STATES
  // ==========================================
  const [kgSubject, setKgSubject] = useState("dsa");
  const [kgGraphData, setKgGraphData] = useState<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] });
  const [selectedKgNodeId, setSelectedKgNodeId] = useState<string | null>(null);
  const [kgNodeDetails, setKgNodeDetails] = useState<any | null>(null);
  const [kgHealth, setKgHealth] = useState<any | null>(null);
  const [kgDeadNodes, setKgDeadNodes] = useState<any[]>([]);
  const [kgSearchQuery, setKgSearchQuery] = useState("");
  const [kgSearchResults, setKgSearchResults] = useState<any[]>([]);
  const [kgLearningPath, setKgLearningPath] = useState<any[]>([]);
  const [kgLoading, setKgLoading] = useState(false);
  const [showCreateNodeDialog, setShowCreateNodeDialog] = useState(false);
  const [showLinkQuestionDialog, setShowLinkQuestionDialog] = useState(false);
  
  // Create Node dialog fields
  const [newNodeName, setNewNodeName] = useState("");
  const [newNodeType, setNewNodeType] = useState("concept");
  const [newNodeDesc, setNewNodeDesc] = useState("");
  const [newNodeTopic, setNewNodeTopic] = useState("");
  const [newNodeSubtopic, setNewNodeSubtopic] = useState("");
  const [newNodeParentId, setNewNodeParentId] = useState("");
  const [newNodePrereqId, setNewNodePrereqId] = useState("");
  
  // Link Question dialog fields
  const [linkQuestionId, setLinkQuestionId] = useState("");
  const [selectedInterveneStudent, setSelectedInterveneStudent] = useState<string>("");

  // Validation and SIH Demo states (Week 5 Refinements)
  const [demoMode, setDemoMode] = useState(false);
  const [validationKPIs, setValidationKPIs] = useState<any | null>(null);
  const [validationQQI, setValidationQQI] = useState<any[]>([]);
  const [validationTelemetry, setValidationTelemetry] = useState<any | null>(null);
  const [pilotSessions, setPilotSessions] = useState<any[]>([]);
  const [validationSnapshots, setValidationSnapshots] = useState<any[]>([]);
  const [showCreateSessionDialog, setShowCreateSessionDialog] = useState(false);
  
  // Create Pilot Session dialog fields
  const [newSessionClassroomId, setNewSessionClassroomId] = useState("");
  const [newSessionTeacher, setNewSessionTeacher] = useState("");
  const [newSessionSubject, setNewSessionSubject] = useState("");
  const [newSessionTopic, setNewSessionTopic] = useState("");
  const [newSessionType, setNewSessionType] = useState("Standard Diagnostic");
  const [newSessionDevice, setNewSessionDevice] = useState("desktop");
  const [newSessionBrowser, setNewSessionBrowser] = useState("Chrome");
  const [newSessionNetwork, setNewSessionNetwork] = useState("Excellent");
  const [newSessionDuration, setNewSessionDuration] = useState("45");

  // Structured Notes Form state
  const [noteRoomCode, setNoteRoomCode] = useState("");
  const [noteObs, setNoteObs] = useState("");
  const [noteReason, setNoteReason] = useState("");
  const [noteAction, setNoteAction] = useState("");
  const [noteOutcome, setNoteOutcome] = useState("");
  const [noteHistory, setNoteHistory] = useState<any[]>([]);

  // Blueprint Designer Form state
  const [bpName, setBpName] = useState("");
  const [bpSubject, setBpSubject] = useState("math");
  const [bpTopic, setBpTopic] = useState("algebra");
  const [bpSubtopic, setBpSubtopic] = useState("quadratic");
  const [bpPurpose, setBpPurpose] = useState("diagnostic");
  const [bpDuration, setBpDuration] = useState(30);
  const [bpQuestionCount, setBpQuestionCount] = useState(10);
  const [bpDifficulty, setBpDifficulty] = useState("medium");
  const [bpStrategy, setBpStrategy] = useState("balanced");
  const [bpConceptual, setBpConceptual] = useState(25);
  const [bpApplication, setBpApplication] = useState(25);
  const [bpReasoning, setBpReasoning] = useState(25);
  const [bpMemory, setBpMemory] = useState(25);

  const handleSubjectChange = (newSub: string) => {
    setBpSubject(newSub);
    const subData = SUBJECT_MAP[newSub];
    if (subData) {
      const firstTopic = Object.keys(subData.topics)[0];
      setBpTopic(firstTopic);
      const firstSubtopic = Object.keys(subData.topics[firstTopic].subtopics)[0];
      setBpSubtopic(firstSubtopic);
    }
  };

  const handleTopicChange = (newTopic: string) => {
    setBpTopic(newTopic);
    const subData = SUBJECT_MAP[bpSubject];
    if (subData && subData.topics[newTopic]) {
      const firstSubtopic = Object.keys(subData.topics[newTopic].subtopics)[0];
      setBpSubtopic(firstSubtopic);
    }
  };

  // Question Builder Form state
  const [customPrompt, setCustomPrompt] = useState("");
  const [optA, setOptA] = useState("");
  const [optB, setOptB] = useState("");
  const [optC, setOptC] = useState("");
  const [optD, setOptD] = useState("");
  const [correctIdx, setCorrectIdx] = useState(0);
  const [customExpl, setCustomExpl] = useState("");
  const [customTags, setCustomTags] = useState("");
  const [customConcepts, setCustomConcepts] = useState("");
  const [customCategory, setCustomCategory] = useState("conceptual");
  const [customLoad, setCustomLoad] = useState("medium");

  // Dynamic recommendations from Evidence Fusion
  const [copilotRecs, setCopilotRecs] = useState<any[]>([]);

  // Load basic data and demo mode status
  useEffect(() => {
    if (user.role !== "teacher") {
      const allReports = getReports().filter((r) => r.userEmail === user.email);
      setReports(allReports);
      return;
    }

    async function loadTeacherData() {
      try {
        const roomsRes = await fetch(`${API}/teacher-rooms/${user.email}`);
        const roomsData = await roomsRes.json();
        setTeacherRooms(roomsData);

        const bpRes = await fetch(`${API}/assessment-blueprints/${user.email}`);
        const bpData = await bpRes.json();
        setBlueprints(bpData);

        const cohortRes = await fetch(`${API}/cohort-comparison`);
        const cohortData = await cohortRes.json();
        setCohorts(cohortData);

        // Load dynamic copilot recommendations
        const recsRes = await fetch(`${API}/copilot/recommendations`);
        if (recsRes.ok) {
          const recsData = await recsRes.json();
          setCopilotRecs(recsData);
        }

        // Load Demo Mode status
        const demoRes = await fetch(`${API}/demo-mode`);
        if (demoRes.ok) {
          const demoData = await demoRes.json();
          setDemoMode(demoData.demo_mode);
        }

        // Load Teacher dashboard stats
        try {
          setLoadingStats(true);
          const statsRes = await fetch(`${API}/api/v1/teacher/dashboard-stats/${user.email}`);
          if (statsRes.ok) {
            const statsData = await statsRes.json();
            setStats(statsData);
          }
        } catch (sErr) {
          console.error("Error fetching stats:", sErr);
        } finally {
          setLoadingStats(false);
        }
      } catch (err) {
        console.error("Error loading teacher data:", err);
      }
    }
    loadTeacherData();
  }, [user.email, user.role]);

  // Load validation metrics when active mode is validation
  useEffect(() => {
    if (activeMode === "validation") {
      loadValidationData();
    }
  }, [activeMode]);

  // Load room monitor details when active monitor room changes
  useEffect(() => {
    if (!selectedMonitorRoom) return;

    async function loadMonitorDetails() {
      try {
        const studentRes = await fetch(`${API}/room-students/${selectedMonitorRoom}`);
        const studentData = await studentRes.json();
        setMonitorStudents(studentData);

        const reportRes = await fetch(`${API}/room-reports/${selectedMonitorRoom}`);
        const reportData = await reportRes.json();
        setMonitorReports(reportData);

        const qualityRes = await fetch(`${API}/room-quality-metrics/${selectedMonitorRoom}`);
        const qualityData = await qualityRes.json();
        setQualityMetrics(qualityData);

        const notesRes = await fetch(`${API}/teacher-notes?room_code=${selectedMonitorRoom}`);
        const notesData = await notesRes.json();
        setNoteHistory(notesData);

        // Load dynamic room recommendations
        const recsRes = await fetch(`${API}/copilot/recommendations?room_code=${selectedMonitorRoom}`);
        if (recsRes.ok) {
          const recsData = await recsRes.json();
          setCopilotRecs(recsData);
        }
      } catch (err) {
        console.error("Error loading monitor room details:", err);
      }
    }
    loadMonitorDetails();
  }, [selectedMonitorRoom]);

  // Load Lifecycle questions when active status tab changes
  useEffect(() => {
    if (user.role !== "teacher") return;

    async function loadLifecycleQuestions() {
      try {
        const res = await fetch(`${API}/questions/status/${lifecycleStatus}`);
        const data = await res.json();
        setLifecycleQuestions(data);
      } catch (err) {
        console.error("Error loading lifecycle questions:", err);
      }
    }
    loadLifecycleQuestions();
  }, [lifecycleStatus]);

  // Join Room for Students
  const handleJoinRoom = async () => {
    if (!roomCode.trim()) {
      toast({ title: "Enter room code", variant: "destructive" });
      return;
    }

    const res = await fetch(`${API}/join-room`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ room_code: roomCode, student_email: user.email })
    });

    const data = await res.json();
    if (!data.success) {
      toast({ title: data.message || "Invalid room code", variant: "destructive" });
      return;
    }

    const room = data.room;
    setSession({
      ...user,
      roomCode: room.room_code,
      assignedSubject: room.subject,
      assignedTopic: room.topic,
      assignedSubtopic: room.subtopic,
      teacherEmail: room.teacher_email,
      difficulty: room.difficulty,
      questionMix: room.question_mix,
      questionCount: room.question_count,
      assessmentStrategy: room.assessment_strategy,
      roomDuration: room.duration
    });

    toast({ title: "Room joined successfully!" });
    navigate("/quiz");
  };

  // Create Blueprint Action
  const handleCreateBlueprint = async () => {
    if (!bpName.trim()) {
      toast({ title: "Please enter a blueprint name", variant: "destructive" });
      return;
    }

    const totalPct = Number(bpConceptual) + Number(bpApplication) + Number(bpReasoning) + Number(bpMemory);
    if (totalPct !== 100) {
      toast({ title: `Cognitive Distribution must sum to 100% (Current: ${totalPct}%)`, variant: "destructive" });
      return;
    }

    const payload = {
      name: bpName,
      teacher_email: user.email,
      subject: bpSubject,
      topic: bpTopic,
      subtopic: bpSubtopic,
      purpose: bpPurpose,
      duration: bpDuration,
      question_count: bpQuestionCount,
      difficulty: bpDifficulty,
      assessment_strategy: bpStrategy,
      conceptual_pct: bpConceptual,
      application_pct: bpApplication,
      reasoning_pct: bpReasoning,
      memory_pct: bpMemory
    };

    const res = await fetch(`${API}/assessment-blueprints`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (result.success) {
      toast({ title: "Assessment Blueprint Locked Successfully!" });
      setBpName("");
      // reload blueprints
      const bpRes = await fetch(`${API}/assessment-blueprints/${user.email}`);
      const bpData = await bpRes.json();
      setBlueprints(bpData);
      setActiveMode("observe");
    } else {
      toast({ title: "Failed to create blueprint", variant: "destructive" });
    }
  };

  // Create Room from Blueprint
  const handleLaunchRoom = async () => {
    if (!selectedBlueprintId) {
      toast({ title: "Please select a blueprint", variant: "destructive" });
      return;
    }

    const res = await fetch(`${API}/create-room`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        teacher_email: user.email,
        blueprint_id: Number(selectedBlueprintId)
      })
    });
    const data = await res.json();

    if (data.success) {
      toast({ title: `Room Launched: ${data.room_code}` });
      // reload rooms
      const roomsRes = await fetch(`${API}/teacher-rooms/${user.email}`);
      const roomsData = await roomsRes.json();
      setTeacherRooms(roomsData);
      setSelectedMonitorRoom(data.room_code);
      setActiveMode("assess");
    } else {
      toast({ title: data.message || "Failed to create room", variant: "destructive" });
    }
  };

  // Structured Notes Submit
  const handleSaveNotes = async () => {
    if (!noteRoomCode) {
      toast({ title: "Please select a room code", variant: "destructive" });
      return;
    }
    if (!noteObs || !noteReason || !noteAction || !noteOutcome) {
      toast({ title: "All structured note fields are required", variant: "destructive" });
      return;
    }

    const res = await fetch(`${API}/teacher-notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room_code: noteRoomCode,
        teacher_email: user.email,
        observation: noteObs,
        reason: noteReason,
        action_taken: noteAction,
        outcome: noteOutcome
      })
    });

    if (res.ok) {
      toast({ title: "Feedback logged to retraining layer!" });
      setNoteObs("");
      setNoteReason("");
      setNoteAction("");
      setNoteOutcome("");
      // reload notes history
      if (selectedMonitorRoom === noteRoomCode) {
        const notesRes = await fetch(`${API}/teacher-notes?room_code=${selectedMonitorRoom}`);
        const notesData = await notesRes.json();
        setNoteHistory(notesData);
      }
    }
  };

  // Custom Question Builder Submit
  const handleAddQuestion = async () => {
    if (!customPrompt || !optA || !optB || !optC || !optD) {
      toast({ title: "Fill all question fields", variant: "destructive" });
      return;
    }

    const payload = {
      subject: bpSubject,
      topic: bpTopic,
      subtopic: bpSubtopic,
      difficulty: bpDifficulty,
      question_category: customCategory,
      prompt: customPrompt,
      options: [optA, optB, optC, optD],
      correct_index: correctIdx,
      explanation: customExpl,
      teacher_email: user.email,
      tags: customTags,
      concepts: customConcepts.split(",").map(c => c.trim()),
      cognitive_load: customLoad,
      estimated_time: 30
    };

    const res = await fetch(`${API}/add-custom-question`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (result.success) {
      toast({ 
        title: result.validated ? "Passed AI duplicate validation!" : "Failed AI validation",
        description: result.message
      });
      setCustomPrompt("");
      setOptA("");
      setOptB("");
      setOptC("");
      setOptD("");
      setCustomExpl("");
      setCustomTags("");
      setCustomConcepts("");
      
      // refresh lifecycle questions
      const statusRes = await fetch(`${API}/questions/status/${lifecycleStatus}`);
      const data = await statusRes.json();
      setLifecycleQuestions(data);
    }
  };

  // Change Question Lifecycle status
  const handleUpdateQuestionStatus = async (qid: number, newStatus: string) => {
    const res = await fetch(`${API}/questions/update-status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: qid, status: newStatus })
    });
    if (res.ok) {
      toast({ title: `Question status updated to ${newStatus}` });
      // refresh
      const statusRes = await fetch(`${API}/questions/status/${lifecycleStatus}`);
      const data = await statusRes.json();
      setLifecycleQuestions(data);
    }
  };

  // Question Workspace Handlers
  const loadQuestionDetail = async (qid: number) => {
    setWorkspaceLoading(true);
    try {
      const res = await fetch(`${API}/question/${qid}`);
      if (res.ok) {
        const data = await res.json();
        setQuestionDetail(data);
        setSelectedQuestionId(qid);
        
        // Populate editor fields
        setEditPrompt(data.question.prompt || "");
        setEditOptA(data.options[0] || "");
        setEditOptB(data.options[1] || "");
        setEditOptC(data.options[2] || "");
        setEditOptD(data.options[3] || "");
        setEditCorrectIdx(data.question.correct_index ?? 0);
        setEditExplanation(data.question.explanation || "");
        setEditDifficulty(data.question.difficulty || "medium");
        setEditCognitiveType(data.question.cognitive_type || "conceptual");
        
        const conceptNames = data.concepts.map((c: any) => c.name).join(", ");
        setEditConcepts(conceptNames);
        
        setImpactPrediction(null);
        setIsPreviewMode(false);
      } else {
        toast({ title: "Failed to load question details", variant: "destructive" });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setWorkspaceLoading(false);
    }
  };

  const handlePredictImpact = async () => {
    if (!selectedQuestionId) return;
    setPredictingImpact(true);
    try {
      const res = await fetch(`${API}/question/predict-impact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: selectedQuestionId,
          prompt: editPrompt,
          explanation: editExplanation,
          concepts: editConcepts.split(",").map(c => c.trim()).filter(Boolean)
        })
      });
      if (res.ok) {
        const data = await res.json();
        setImpactPrediction(data);
        toast({ title: "Impact analysis complete!" });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setPredictingImpact(false);
    }
  };

  const handleSaveQuestionEdit = async () => {
    if (!selectedQuestionId) return;
    if (changeReason.trim() === "") {
      toast({ title: "Please provide a change reason for the audit trail", variant: "destructive" });
      return;
    }
    
    try {
      const res = await fetch(`${API}/question/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: selectedQuestionId,
          prompt: editPrompt,
          options: [editOptA, editOptB, editOptC, editOptD],
          correct_index: editCorrectIdx,
          explanation: editExplanation,
          difficulty: editDifficulty,
          cognitive_type: editCognitiveType,
          concepts: editConcepts.split(",").map(c => c.trim()).filter(Boolean),
          edited_by: user.email,
          change_reason: changeReason
        })
      });
      if (res.ok) {
        toast({ title: "Question successfully updated and versioned!" });
        setChangeReason("");
        await loadQuestionDetail(selectedQuestionId);
        await loadAllQuestions();
      } else {
        toast({ title: "Failed to update question", variant: "destructive" });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRollbackVersion = async (targetVer: number) => {
    if (!selectedQuestionId) return;
    try {
      const res = await fetch(`${API}/question/rollback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: selectedQuestionId,
          target_version: targetVer,
          edited_by: user.email
        })
      });
      if (res.ok) {
        toast({ title: `Successfully rolled back to version ${targetVer}!` });
        await loadQuestionDetail(selectedQuestionId);
        await loadAllQuestions();
      } else {
        toast({ title: "Rollback failed", variant: "destructive" });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadAllQuestions = async () => {
    try {
      const res = await fetch(`${API}/questions/all`);
      if (res.ok) {
        const data = await res.json();
        setAllQuestions(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateWorkspaceQuestionStatus = async (qid: number, newStatus: string) => {
    const res = await fetch(`${API}/question/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: qid, status: newStatus })
    });
    if (res.ok) {
      toast({ title: `Question status updated to ${newStatus}` });
      await loadQuestionDetail(qid);
      await loadAllQuestions();
    }
  };

  useEffect(() => {
    if (activeMode === "lifecycle") {
      loadAllQuestions();
    }
  }, [activeMode]);

  const filteredQuestions = useMemo(() => {
    return allQuestions.filter((q) => {
      const promptMatch = q.prompt.toLowerCase().includes(searchQuery.toLowerCase());
      const subjectMatch = filterSubject === "all" || q.subject.toLowerCase() === filterSubject.toLowerCase();
      const diffMatch = filterDifficulty === "all" || q.difficulty.toLowerCase() === filterDifficulty.toLowerCase();
      const statusMatch = filterStatus === "all" || q.status.toLowerCase() === filterStatus.toLowerCase();
      return promptMatch && subjectMatch && diffMatch && statusMatch;
    });
  }, [allQuestions, searchQuery, filterSubject, filterDifficulty, filterStatus]);

  // ==========================================
  // KNOWLEDGE GRAPH HANDLERS & EFFECTS
  // ==========================================
  const loadKgData = async (subject: string) => {
    setKgLoading(true);
    try {
      // 1. Fetch graph node-edge data
      const gRes = await fetch(`${API}/kg/graph?subject=${subject}`);
      if (gRes.ok) {
        const gData = await gRes.json();
        setKgGraphData(gData);
      }
      
      // 2. Fetch graph health report
      const hRes = await fetch(`${API}/kg/health?subject=${subject}`);
      if (hRes.ok) {
        const hData = await hRes.json();
        setKgHealth(hData);
      }
      
      // 3. Fetch dead nodes list
      const dRes = await fetch(`${API}/kg/dead-nodes?subject=${subject}`);
      if (dRes.ok) {
        const dData = await dRes.json();
        setKgDeadNodes(dData);
      }
    } catch (err) {
      console.error(err);
      toast({ title: "Failed to load Knowledge Graph data", variant: "destructive" });
    } finally {
      setKgLoading(false);
    }
  };

  const loadKgNodeDetails = async (nodeId: string) => {
    try {
      const res = await fetch(`${API}/kg/node/${nodeId}`);
      if (res.ok) {
        const data = await res.json();
        setKgNodeDetails(data);
        setSelectedKgNodeId(nodeId);
        
        // Load learning path for this node
        const pRes = await fetch(`${API}/kg/path?node_id=${nodeId}&student_email=${user.email}`);
        if (pRes.ok) {
          const pData = await pRes.json();
          setKgLearningPath(pData.learning_path || []);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateKgNode = async () => {
    if (!newNodeName.trim()) {
      toast({ title: "Node name cannot be empty", variant: "destructive" });
      return;
    }
    try {
      const res = await fetch(`${API}/kg/create-node`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newNodeName,
          type: newNodeType,
          description: newNodeDesc,
          subject: kgSubject,
          topic: newNodeTopic,
          subtopic: newNodeSubtopic,
          parent_id: newNodeParentId ? newNodeParentId : null,
          prereq_id: newNodePrereqId ? newNodePrereqId : null
        })
      });
      if (res.ok) {
        toast({ title: "Knowledge Graph node created!" });
        setShowCreateNodeDialog(false);
        setNewNodeName("");
        setNewNodeDesc("");
        setNewNodeTopic("");
        setNewNodeSubtopic("");
        setNewNodeParentId("");
        setNewNodePrereqId("");
        
        await loadKgData(kgSubject);
      } else {
        const errData = await res.json();
        toast({ title: errData.error || "Failed to create node", variant: "destructive" });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleLinkQuestionToNode = async () => {
    if (!selectedKgNodeId || !linkQuestionId.trim()) {
      toast({ title: "Please specify a question ID", variant: "destructive" });
      return;
    }
    try {
      const res = await fetch(`${API}/kg/link-question`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: Number(linkQuestionId),
          node_id: selectedKgNodeId
        })
      });
      if (res.ok) {
        toast({ title: "Question successfully linked to Knowledge node!" });
        setShowLinkQuestionDialog(false);
        setLinkQuestionId("");
        
        await loadKgNodeDetails(selectedKgNodeId);
        await loadKgData(kgSubject);
      } else {
        const errData = await res.json();
        toast({ title: errData.error || "Link failed", variant: "destructive" });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadValidationData = async () => {
    try {
      const kRes = await fetch(`${API}/validation/kpis`);
      if (kRes.ok) {
        setValidationKPIs(await kRes.json());
      }
      const qRes = await fetch(`${API}/validation/qqi`);
      if (qRes.ok) {
        setValidationQQI(await qRes.json());
      }
      const tRes = await fetch(`${API}/validation/telemetry`);
      if (tRes.ok) {
        setValidationTelemetry(await tRes.json());
      }
      const sRes = await fetch(`${API}/pilot-sessions`);
      if (sRes.ok) {
        setPilotSessions(await sRes.json());
      }
      const snRes = await fetch(`${API}/validation/snapshots`);
      if (snRes.ok) {
        setValidationSnapshots(await snRes.json());
      }
    } catch (err) {
      console.error("Error loading validation metrics:", err);
    }
  };

  const handleCreatePilotSession = async () => {
    if (!newSessionClassroomId.trim() || !newSessionTeacher.trim() || !newSessionSubject.trim()) {
      toast({ title: "Classroom ID, Teacher, and Subject are required", variant: "destructive" });
      return;
    }
    try {
      const res = await fetch(`${API}/pilot-sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          classroom_id: newSessionClassroomId,
          teacher: newSessionTeacher,
          subject: newSessionSubject,
          topic: newSessionTopic,
          assessment_type: newSessionType,
          device_type: newSessionDevice,
          browser: newSessionBrowser,
          network_quality: newSessionNetwork,
          session_duration: Number(newSessionDuration)
        })
      });
      if (res.ok) {
        toast({ title: "Pilot classroom session started!" });
        setShowCreateSessionDialog(false);
        setNewSessionClassroomId("");
        setNewSessionTeacher("");
        setNewSessionSubject("");
        setNewSessionTopic("");
        await loadValidationData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearchKgNodes = async (query: string) => {
    setKgSearchQuery(query);
    if (!query.trim()) {
      setKgSearchResults([]);
      return;
    }
    try {
      const res = await fetch(`${API}/kg/search?query=${query}&subject=${kgSubject}`);
      if (res.ok) {
        const data = await res.json();
        setKgSearchResults(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (activeMode === "explorer") {
      loadKgData(kgSubject);
      setSelectedKgNodeId(null);
      setKgNodeDetails(null);
    }
  }, [activeMode, kgSubject]);

  // Save Copilot Feedback Action
  const handleCopilotAction = async (recId: number, action: "Accept" | "Modify" | "Ignore") => {
    const res = await fetch(`${API}/copilot/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        recommendation_id: recId,
        teacher_email: user.email,
        action: action,
        reason: `Teacher clicked ${action} on copilot lesson recommendation`
      })
    });
    if (res.ok) {
      toast({ title: `Copilot action [${action}] recorded!` });
    }
  };

  // Mock list of Copilot recommendations with structured format
  const copilotRecommendations = [
    {
      id: 101,
      concept: "Roots",
      reasoning: "High hesitation and overthinking detected during visual quadratic graph questions.",
      evidence: "5 students flagged for high hesitation. Average reflection time exceeded 12s on roots calculation.",
      suggestedAction: "Conduct 15-minute visual parabola graphing demonstration to trace roots physically.",
      expectedGain: "+25% increase in Application-type question commitment rate.",
      priority: "HIGH"
    },
    {
      id: 102,
      concept: "Discriminant",
      reasoning: "High memory reliance flag triggered. Students answer formulas immediately but fail application prompts.",
      evidence: "4 students showed high memory dependence, with 90% correct index on recall and <20% on application.",
      suggestedAction: "Run a 10-minute game comparing discriminant values to root behavior physically.",
      expectedGain: "+15% in transfer ability index on next assessment.",
      priority: "MEDIUM"
    }
  ];

  // Observe Mode aggregate calculation helper
  const classStats = useMemo(() => {
    return {
      conceptual: 68,
      guessing: 12,
      overthinking: 24,
      classSize: 28,
      conceptualDelta: "+3%",
      guessingDelta: "-2%",
      overthinkingDelta: "+1%"
    };
  }, []);

  // Concept nodes average score (mocked for heatmap visual representation of Academic Knowledge Graph)
  const conceptHeatmap = [
    { name: "Formula Recall", subject: "Math", rating: 88, status: "stable" },
    { name: "Discriminant", subject: "Math", rating: 44, status: "critical" },
    { name: "Roots", subject: "Math", rating: 52, status: "warning" },
    { name: "Graph Interpretation", subject: "Math", rating: 61, status: "warning" },
    { name: "Inertia", subject: "Physics", rating: 82, status: "stable" },
    { name: "Force Dynamics", subject: "Physics", rating: 49, status: "critical" },
    { name: "Action Reaction", subject: "Physics", rating: 76, status: "stable" },
    { name: "Array Indexing", subject: "DSA", rating: 85, status: "stable" },
    { name: "Contiguous Memory", subject: "DSA", rating: 38, status: "critical" },
    { name: "Complexity Analysis", subject: "DSA", rating: 59, status: "warning" }
  ];

  // Compare Cohorts
  const activeComparison = useMemo(() => {
    if (!compareRoomA || !compareRoomB) return null;
    const rA = cohorts.find(c => c.room_code === compareRoomA);
    const rB = cohorts.find(c => c.room_code === compareRoomB);
    return { rA, rB };
  }, [compareRoomA, compareRoomB, cohorts]);

  if (user.role === "teacher") {
    return (
      <InsideLayout showNav={false}>
        <div className="flex min-h-screen text-foreground relative">
          {/* Collapsible Left Sidebar */}
          {sidebarOpen && (
            <aside className="w-64 border-r border-white/10 bg-card/60 backdrop-blur-md flex flex-col justify-between shrink-0 h-screen sticky top-0 z-50">
              <div className="flex flex-col">
                {/* Logo Area */}
                <div className="h-16 border-b border-white/5 flex items-center justify-between px-6">
                  <div className="flex items-center gap-2">
                    <Brain className="h-6 w-6 text-primary animate-pulse" />
                    <span className="font-display font-bold text-lg text-white">Cognify</span>
                  </div>
                  <button 
                    onClick={() => setSidebarOpen(false)}
                    className="p-1.5 hover:bg-white/5 rounded-lg text-muted-foreground hover:text-white transition-fast"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                {/* Sidebar Navigation Links */}
                <nav className="p-4 space-y-1.5">
                  {[
                    { id: "overview", label: "Overview", icon: Layers, mode: "observe" },
                    { id: "assessments", label: "Assessments", icon: Plus, mode: "designer" },
                    { id: "students", label: "Students", icon: Users, mode: "assess" },
                    { id: "question-bank", label: "Question Bank", icon: FileText, mode: "lifecycle" },
                    { id: "analytics", label: "Analytics", icon: Activity, mode: "intervene" },
                    { id: "kg", label: "Knowledge Graph", icon: Brain, mode: "explorer" },
                    { id: "research", label: "Pilot Research", icon: Award, mode: "validation" },
                  ].map((item) => {
                    const isActive = activeMode === item.mode || 
                      (item.id === "analytics" && ["observe", "assess", "intervene", "improve"].includes(activeMode));
                    return (
                      <button
                        key={item.id}
                        onClick={() => {
                          if (item.id === "analytics") {
                            setActiveMode("intervene");
                          } else {
                            setActiveMode(item.mode as any);
                          }
                        }}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${
                          isActive
                            ? "bg-primary/10 text-primary border-l-2 border-primary"
                            : "text-muted-foreground hover:bg-white/5 hover:text-white"
                        }`}
                      >
                        <item.icon className="h-4 w-4" />
                        <span>{item.label}</span>
                      </button>
                    );
                  })}
                </nav>
              </div>

              {/* Sidebar Footer */}
              <div className="p-6 border-t border-white/5 text-xs text-muted-foreground flex flex-col gap-2">
                <a href="#docs" className="hover:text-white flex items-center gap-1.5 font-semibold font-sans">
                  <HelpCircle className="h-4 w-4" /> Documentation
                </a>
                <div>v1.0.0 • Connected</div>
              </div>
            </aside>
          )}

          {/* Main workspace */}
          <div className="flex-1 flex flex-col min-w-0 min-h-screen">
            {/* Top Workspace Header */}
            <header className="h-16 border-b border-white/5 flex items-center justify-between px-8 bg-card/25 backdrop-blur-md sticky top-0 z-40">
              <div className="flex items-center gap-4">
                {!sidebarOpen && (
                  <button
                    onClick={() => setSidebarOpen(true)}
                    className="p-2 hover:bg-white/5 rounded-xl border border-white/10 transition-fast"
                  >
                    <Plus className="h-4 w-4 rotate-45" /> {/* Hamburger simulation */}
                  </button>
                )}
                <div className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-mono">
                  Teacher Workspace
                </div>
              </div>

              <div className="flex items-center gap-4">
                {/* SIH Demo Mode Trigger */}
                <div className="flex items-center gap-2 bg-black/40 border border-white/10 rounded-2xl px-3 py-1.5 text-xs">
                  <span className="font-bold text-gray-300">SIH Demo Mode:</span>
                  <button
                    onClick={async () => {
                      const nextMode = !demoMode;
                      setDemoMode(nextMode);
                      try {
                        const res = await fetch(`${API}/demo-mode`, {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ enable: nextMode })
                        });
                        if (res.ok) {
                          toast({ title: `SIH Demo Mode ${nextMode ? "Enabled" : "Disabled"}` });
                          window.location.reload();
                        }
                      } catch (err) {
                        console.error(err);
                      }
                    }}
                    className={`px-2 py-0.5 rounded-full font-bold text-[10px] tracking-wider transition-all ${
                      demoMode ? "bg-emerald-500 text-black shadow-lg shadow-emerald-500/25 animate-pulse" : "bg-white/10 text-white/50"
                    }`}
                  >
                    {demoMode ? "ACTIVE" : "OFF"}
                  </button>
                </div>

                <div className="flex items-center gap-3 bg-white/5 border border-white/10 rounded-2xl p-2 shadow-inner">
                  <select
                    value={selectedBlueprintId}
                    onChange={(e) => setSelectedBlueprintId(e.target.value)}
                    className="p-1 rounded-xl bg-black border text-white text-xs"
                  >
                    <option value="">Select Blueprint</option>
                    {blueprints.map((bp) => (
                      <option key={bp.id} value={bp.id}>
                        {bp.name} (v{bp.version})
                      </option>
                    ))}
                  </select>
                  <Button onClick={handleLaunchRoom} size="xs" className="bg-mint hover:bg-mint-glow text-black font-bold h-7 text-[10px]">
                    Launch Room
                  </Button>
                </div>
              </div>
            </header>

            {/* Content area */}
            <div className="flex-1 overflow-y-auto px-8 py-6">
              {/* Primary View */}
              <div className="mt-2">
            <AnimatePresence mode="wait">
              
              {/* Observe View (Redesigned Dashboard Home) */}
              {activeMode === "observe" && (
                <motion.div
                  key="observe"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-8"
                >
                  {/* Welcome Banner */}
                  <div className="py-6 border-b border-white/5 mb-4">
                    <h1 className="font-display text-5xl font-extrabold tracking-tight">
                      Good Afternoon, <span className="text-mint">{user.name}</span>
                    </h1>
                    <p className="text-muted-foreground text-xs mt-1.5 tracking-wider uppercase">
                      Understand how you think. • Beyond scores.
                    </p>
                  </div>

                  {/* Metrics Cards Grid */}
                  <div className="grid gap-4 sm:grid-cols-4">
                    {/* Assessments Count */}
                    <div className="rounded-2xl border border-white/10 p-5 bg-card flex flex-col justify-between card-hover-lift">
                      <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold"><TextScrambler text="Assessments" /></div>
                      <div className="mt-3">
                        {loadingStats ? (
                          <div className="h-9 w-16 skeleton-pulse rounded-md" />
                        ) : (
                          <span className="text-4xl font-bold font-display text-mint">{stats.total_assessments}</span>
                        )}
                      </div>
                      <p className="mt-2 text-[10px] text-muted-foreground">Total diagnostic test rooms.</p>
                    </div>

                    {/* Enrolled Students */}
                    <div className="rounded-2xl border border-white/10 p-5 bg-card flex flex-col justify-between card-hover-lift">
                      <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold"><TextScrambler text="Students Enrolled" /></div>
                      <div className="mt-3">
                        {loadingStats ? (
                          <div className="h-9 w-16 skeleton-pulse rounded-md" />
                        ) : (
                          <span className="text-4xl font-bold font-display text-white">{stats.total_students}</span>
                        )}
                      </div>
                      <p className="mt-2 text-[10px] text-muted-foreground">Unique student sessions.</p>
                    </div>

                    {/* Cognitive Reports */}
                    <div className="rounded-2xl border border-white/10 p-5 bg-card flex flex-col justify-between card-hover-lift">
                      <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold"><TextScrambler text="Reports Compiled" /></div>
                      <div className="mt-3">
                        {loadingStats ? (
                          <div className="h-9 w-16 skeleton-pulse rounded-md" />
                        ) : (
                          <span className="text-4xl font-bold font-display text-white">{stats.total_reports}</span>
                        )}
                      </div>
                      <p className="mt-2 text-[10px] text-muted-foreground">Cognitive profiles generated.</p>
                    </div>

                    {/* Average Cognitive Health */}
                    <div className="rounded-2xl border border-white/10 p-5 bg-card flex flex-col justify-between card-hover-lift">
                      <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold"><TextScrambler text="Avg Cognitive Health" /></div>
                      <div className="mt-3">
                        {loadingStats ? (
                          <div className="h-9 w-16 skeleton-pulse rounded-md" />
                        ) : (
                          <span className="text-4xl font-bold font-display text-orange-500">{stats.average_cognitive_health}%</span>
                        )}
                      </div>
                      <p className="mt-2 text-[10px] text-muted-foreground">Calculated average understanding.</p>
                    </div>
                  </div>

                  {/* Main Grid: Assessments vs Analytics Side panels */}
                  <div className="grid gap-6 lg:grid-cols-3 mt-8">
                    {/* Left 2 Columns: Recent Assessments Cards */}
                    <div className="lg:col-span-2 space-y-6">
                      <div className="flex items-center justify-between border-b border-white/5 pb-3">
                        <h2 className="text-lg font-bold tracking-tight uppercase text-white font-display"><TextScrambler text="Recent Assessments" /></h2>
                        <button
                          onClick={() => setActiveMode("designer")}
                          className="text-xs font-bold text-mint hover:text-mint-glow flex items-center gap-1 transition-fast btn-active-push"
                        >
                          + <TextScrambler text="Create Assessment" />
                        </button>
                      </div>

                      {loadingStats ? (
                        <div className="space-y-4">
                          {[1, 2].map((i) => (
                            <div key={i} className="h-28 w-full skeleton-pulse rounded-2xl" />
                          ))}
                        </div>
                      ) : teacherRooms.length === 0 ? (
                        <div className="text-center py-12 rounded-2xl border border-dashed border-white/10 text-muted-foreground">
                          <Brain className="h-8 w-8 mx-auto mb-3 text-white/20" />
                          <p className="text-sm">No assessments launched yet.</p>
                          <button
                            onClick={() => setActiveMode("designer")}
                            className="text-xs text-mint hover:underline font-bold mt-2"
                          >
                            Create your first assessment.
                          </button>
                        </div>
                      ) : (
                        <div className="grid gap-4">
                          {teacherRooms.map((r) => (
                            <div
                              key={r.room_code}
                              className="rounded-2xl border border-white/10 p-5 bg-card flex flex-col justify-between card-hover-lift"
                            >
                              <div className="flex items-center justify-between">
                                <div>
                                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground bg-white/5 px-2 py-0.5 rounded-md border border-white/5 mr-2">
                                    {r.subject.toUpperCase()}
                                  </span>
                                  <span className="text-[10px] font-mono bg-mint/10 text-mint px-2 py-0.5 rounded-md">
                                    ROOM: {r.room_code}
                                  </span>
                                </div>
                                <span className="text-[10px] text-muted-foreground">
                                  {r.created_at ? r.created_at.split('T')[0] : 'Recently'}
                                </span>
                              </div>

                              <h3 className="mt-3 text-base font-bold font-display text-white capitalize">
                                {r.topic ? r.topic.replace(/_/g, ' ') : 'General Assessment'}
                              </h3>
                              
                              <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-4">
                                <div className="flex gap-4 text-xs text-muted-foreground">
                                  <span>
                                    <strong className="text-white">{r.question_count || 5}</strong> Questions
                                  </span>
                                  <span>
                                    <strong className="text-white font-capitalize">{r.difficulty || 'medium'}</strong> Difficulty
                                  </span>
                                </div>

                                <div className="flex gap-2">
                                  <button
                                    onClick={() => {
                                      setSelectedMonitorRoom(r.room_code);
                                      setActiveMode("assess");
                                    }}
                                    className="px-3 py-1.5 rounded-lg bg-mint text-black text-xs font-bold transition-fast btn-active-push"
                                  >
                                    Monitor
                                  </button>
                                  <button
                                    onClick={() => {
                                      setSelectedMonitorRoom(r.room_code);
                                      setActiveMode("intervene");
                                    }}
                                    className="px-3 py-1.5 rounded-lg bg-secondary text-white text-xs font-bold border border-white/5 hover:border-white/20 transition-fast btn-active-push"
                                  >
                                    AI Copilot
                                  </button>
                                  <button
                                    onClick={() => {
                                      setNoteRoomCode(r.room_code);
                                      setActiveMode("improve");
                                    }}
                                    className="px-3 py-1.5 rounded-lg bg-secondary text-white text-xs font-bold border border-white/5 hover:border-white/20 transition-fast btn-active-push"
                                  >
                                    Notes
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Right 1 Column: Cognitive Analytics status panels */}
                    <div className="space-y-6">
                      <div className="flex items-center justify-between border-b border-white/5 pb-3">
                        <h2 className="text-lg font-bold tracking-tight uppercase text-white font-display">Cognitive Health</h2>
                      </div>

                      <div className="grid gap-4">
                        <div className="rounded-2xl border border-white/10 p-5 bg-card flex flex-col justify-between">
                          <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">Guessing Ratio</div>
                          <div className="mt-1 flex items-baseline gap-2">
                            <span className="text-2xl font-bold font-display text-red-400">{classStats.guessing}%</span>
                            <span className="text-xs text-green-400 font-semibold">{classStats.guessingDelta}</span>
                          </div>
                          <p className="mt-1 text-[10px] text-muted-foreground">Responses entered in under 4s with high hesitation.</p>
                        </div>

                        <div className="rounded-2xl border border-white/10 p-5 bg-card flex flex-col justify-between">
                          <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">Overthinking Rate</div>
                          <div className="mt-1 flex items-baseline gap-2">
                            <span className="text-2xl font-bold font-display text-yellow-400">{classStats.overthinking}%</span>
                            <span className="text-xs text-yellow-400 font-semibold">{classStats.overthinkingDelta}</span>
                          </div>
                          <p className="mt-1 text-[10px] text-muted-foreground">Option re-clicks and hesitation on simple items.</p>
                        </div>
                      </div>

                      {/* Heatmap Widget */}
                      <div className="rounded-2xl border border-white/10 p-5 bg-card">
                        <h3 className="text-[10px] uppercase font-bold text-white tracking-wider mb-3">Topic Mastery Matrix</h3>
                        <div className="grid gap-2 grid-cols-2">
                          {conceptHeatmap.slice(0, 6).map((c) => (
                            <div
                              key={c.name}
                              className={`rounded-lg border p-2 flex flex-col justify-between text-[11px] transition-fast ${
                                c.status === "stable" 
                                  ? "bg-emerald-950/10 border-emerald-500/10 text-emerald-300"
                                  : c.status === "warning"
                                  ? "bg-amber-950/10 border-amber-500/10 text-amber-300"
                                  : "bg-rose-950/10 border-rose-500/10 text-rose-300"
                              }`}
                            >
                              <span className="font-semibold truncate">{c.name}</span>
                              <span className="text-[9px] opacity-75 mt-1 font-mono">{c.rating}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Assess View */}
              {activeMode === "assess" && (
                <motion.div
                  key="assess"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-8"
                >
                  <div className="flex items-center justify-between border-b border-white/10 pb-4">
                    <div className="flex items-center gap-3">
                      <select
                        value={selectedMonitorRoom}
                        onChange={(e) => setSelectedMonitorRoom(e.target.value)}
                        className="p-3 rounded-xl bg-black border text-white font-semibold"
                      >
                        <option value="">Select Live Room Monitor</option>
                        {teacherRooms.map((r) => (
                          <option key={r.room_code} value={r.room_code}>
                            Room Code: {r.room_code} ({r.subject})
                          </option>
                        ))}
                      </select>
                      {selectedMonitorRoom && (
                        <span className="inline-flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 text-xs px-2.5 py-1 rounded-full border border-emerald-500/20">
                          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" /> Active
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Total Student sessions: {monitorStudents.length}
                    </div>
                  </div>

                  {!selectedMonitorRoom ? (
                    <div className="text-center py-12 rounded-3xl border border-dashed border-white/10 text-muted-foreground">
                      Select a room code from the selector above to monitor telemetry in real-time.
                    </div>
                  ) : (
                    <div className="grid gap-8">
                      {/* Student Telemetry Table */}
                      <div className="rounded-3xl border border-white/10 p-6 bg-card">
                        <h3 className="text-lg font-bold">Student Cognitive Telemetry Monitor</h3>
                        <div className="mt-4 overflow-x-auto">
                          <table className="w-full text-left text-sm">
                            <thead>
                              <tr className="border-b border-white/10 text-muted-foreground text-xs uppercase tracking-wider">
                                <th className="pb-3">Student</th>
                                <th className="pb-3">Dominant Pattern</th>
                                <th className="pb-3">Hesitation</th>
                                <th className="pb-3">Fake Understanding</th>
                                <th className="pb-3 text-center">Attention Status</th>
                                <th className="pb-3 text-center">Action Required</th>
                                <th className="pb-3 text-right">Cognitive Report</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                              {monitorStudents.map((stud) => {
                                const sReport = monitorReports.find(r => r.student_email === stud.student_email)?.report || {};
                                const scores = sReport.scores || {};
                                const isFlagged = (scores.hesitation >= 45 || scores.fakeUnderstanding >= 45);
                                
                                // Dynamic intervention estimates based on cognitive patterns
                                let interventionTime = "N/A";
                                let actionMethod = "None";
                                let priority = "LOW";
                                if (isFlagged) {
                                  priority = scores.hesitation >= 55 ? "HIGH" : "MEDIUM";
                                  interventionTime = scores.hesitation >= 55 ? "15 mins" : "10 mins";
                                  actionMethod = scores.fakeUnderstanding >= 45 ? "Visual revision" : "Concept drill";
                                }

                                return (
                                  <tr key={stud.student_email} className="hover:bg-white/5 transition-all">
                                    <td className="py-3.5">
                                      <div className="font-semibold">{stud.name || stud.student_email.split("@")[0]}</div>
                                      <div className="text-xs text-muted-foreground">{stud.student_email}</div>
                                    </td>
                                    <td className="py-3.5">
                                      <span className={`inline-block px-2 py-0.5 rounded text-xs ${
                                        sReport.pattern === "Concept-based" ? "bg-emerald-500/10 text-emerald-400" :
                                        sReport.pattern === "Trial-based" ? "bg-amber-500/10 text-amber-400" : "bg-white/5 text-muted-foreground"
                                      }`}>{sReport.pattern || "Analyzing..."}</span>
                                    </td>
                                    <td className="py-3.5 font-display">{scores.hesitation ?? "-"}%</td>
                                    <td className="py-3.5 font-display">{scores.fakeUnderstanding ?? "-"}%</td>
                                    <td className="py-3.5 text-center">
                                      {isFlagged ? (
                                        <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                                          priority === "HIGH" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                        }`}>
                                          <ShieldAlert className="h-3.5 w-3.5" /> Needs Attention
                                        </span>
                                      ) : (
                                        <span className="text-xs text-emerald-400">✓ Healthy</span>
                                      )}
                                    </td>
                                    <td className="py-3.5 text-center">
                                      {isFlagged ? (
                                        <div className="text-xs">
                                          <div className="font-semibold text-white">{actionMethod}</div>
                                          <div className="text-muted-foreground">{interventionTime} (Priority: {priority})</div>
                                        </div>
                                      ) : (
                                        <span className="text-xs text-muted-foreground">-</span>
                                      )}
                                    </td>
                                    <td className="py-3.5 text-right">
                                      <Link to={`/report/${stud.student_email}`} className="text-mint hover:underline text-xs flex items-center justify-end gap-1">
                                        View Report <ArrowRight className="h-3 w-3" />
                                      </Link>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* Assessment Quality Engine */}
                      <div className="rounded-3xl border border-white/10 p-6 bg-card">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="text-lg font-bold flex items-center gap-1.5"><Award className="h-5 w-5 text-mint" /> Phase B.5 Assessment Quality Engine</h3>
                            <p className="text-xs text-muted-foreground mt-1">
                              Automatically gauges question validity, ambiguity errors, cognitive drift, and guess parameters.
                            </p>
                          </div>
                        </div>

                        {qualityMetrics.length === 0 ? (
                          <div className="text-center py-8 text-muted-foreground text-sm">
                            No student responses recorded in this room yet to run Quality Analysis.
                          </div>
                        ) : (
                          <div className="mt-6 overflow-x-auto">
                            <table className="w-full text-left text-sm">
                              <thead>
                                <tr className="border-b border-white/10 text-muted-foreground text-xs uppercase tracking-wider">
                                  <th className="pb-3">Question Prompt</th>
                                  <th className="pb-3">Success Rate</th>
                                  <th className="pb-3 text-center">Guess Rate</th>
                                  <th className="pb-3 text-center">Ambiguity Rate</th>
                                  <th className="pb-3 text-center">Discrim. Index</th>
                                  <th className="pb-3 text-center">Difficulty Drift</th>
                                  <th className="pb-3 text-center">Behavior Var</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-white/5">
                                {qualityMetrics.map((q) => (
                                  <tr key={q.question_id} className="hover:bg-white/5 transition-all text-xs">
                                    <td className="py-3">
                                      <div className="font-semibold text-white line-clamp-1">{q.prompt}</div>
                                      <div className="text-muted-foreground">Type: {q.cognitive_type} | Concept: {q.concept_coverage}</div>
                                    </td>
                                    <td className="py-3">
                                      <div className="font-semibold font-display">{q.success_rate}%</div>
                                      <div className={`text-[10px] ${
                                        q.difficulty_category === "Too Easy" ? "text-emerald-400" :
                                        q.difficulty_category === "Too Hard" ? "text-rose-400" : "text-muted-foreground"
                                      }`}>{q.difficulty_category}</div>
                                    </td>
                                    <td className="py-3 text-center font-display">
                                      <span className={q.guess_rate > 35 ? "text-red-400 font-bold" : "text-white"}>{q.guess_rate}%</span>
                                    </td>
                                    <td className="py-3 text-center font-display">
                                      <span className={q.ambiguous_rate > 30 ? "text-red-400 font-bold" : "text-white"}>{q.ambiguous_rate}%</span>
                                    </td>
                                    <td className="py-3 text-center">
                                      <div className="font-display font-semibold">{q.discrimination_index}</div>
                                      <div className={`text-[10px] uppercase ${
                                        q.discrimination_label === "High" ? "text-emerald-400" :
                                        q.discrimination_label === "Low" ? "text-red-400 font-bold" : "text-muted-foreground"
                                      }`}>{q.discrimination_label}</div>
                                    </td>
                                    <td className="py-3 text-center">
                                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                        q.difficulty_drift !== "Stable" ? "bg-red-400/10 text-red-300" : "bg-white/5 text-muted-foreground"
                                      }`}>{q.difficulty_drift}</span>
                                    </td>
                                    <td className="py-3 text-center font-display text-muted-foreground">
                                      {q.behavior_variance}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

              {/* Intervene View */}
              {activeMode === "intervene" && (
                <motion.div
                  key="intervene"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-8"
                >
                  <div className="rounded-3xl border border-white/10 p-6 bg-card">
                    <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/5 pb-4 mb-4">
                      <div>
                        <h3 className="text-xl font-bold flex items-center gap-1.5"><Sparkles className="h-5 w-5 text-mint" /> AI Copilot Workspace Recommendations</h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          Targeted pedagogical actions derived from student commitment times, backspaces, and option hover vectors.
                        </p>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-muted-foreground">Focus Student:</span>
                        <select
                          value={selectedInterveneStudent}
                          onChange={async (e) => {
                            const email = e.target.value;
                            setSelectedInterveneStudent(email);
                            try {
                              let url = `${API}/copilot/recommendations`;
                              if (email) {
                                url += `?student_email=${email}`;
                              } else if (selectedMonitorRoom) {
                                url += `?room_code=${selectedMonitorRoom}`;
                              }
                              const r = await fetch(url);
                              if (r.ok) {
                                const d = await r.json();
                                setCopilotRecs(d);
                              }
                            } catch (err) {
                              console.error(err);
                            }
                          }}
                          className="bg-black/50 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-mint"
                        >
                          <option value="">-- All Room Students --</option>
                          {monitorStudents.map((stud) => (
                            <option key={stud.student_email} value={stud.student_email}>
                              {stud.name || stud.student_email.split("@")[0]} ({stud.student_email})
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="space-y-6 mt-6">
                      {(copilotRecs && copilotRecs.length > 0 ? copilotRecs : copilotRecommendations).map((rec) => (
                        <div key={rec.id} className="border border-white/10 rounded-2xl p-6 bg-black relative overflow-hidden">
                          {/* Top Badges Row */}
                          <div className="flex flex-wrap items-center gap-2 mb-4">
                            <span className={`text-[10px] uppercase px-2.5 py-0.5 rounded-full font-bold border ${
                              rec.source === "Template Recommendation"
                                ? "bg-white/5 border-white/10 text-white/50"
                                : "bg-mint/10 border-mint/20 text-mint"
                            }`}>
                              {rec.source || "Template Recommendation"}
                            </span>
                            
                            <span className={`text-[10px] uppercase px-2.5 py-0.5 rounded-full font-bold border ${
                              rec.priority === "HIGH" ? "bg-rose-500/10 border-rose-500/20 text-rose-300" : "bg-amber-500/10 border-amber-500/20 text-amber-300"
                            }`}>
                              {rec.priority} PRIORITY
                            </span>

                            {rec.confidence && (
                              <span className="text-[10px] uppercase px-2.5 py-0.5 rounded-full font-bold border bg-indigo-500/10 border-indigo-500/20 text-indigo-300">
                                Calibration: {rec.confidence} Confidence
                              </span>
                            )}

                            {rec.estimatedTime && (
                              <span className="text-[10px] uppercase px-2.5 py-0.5 rounded-full font-bold border bg-sky-500/10 border-sky-500/20 text-sky-300">
                                {rec.estimatedTime}
                              </span>
                            )}
                          </div>

                          <div className="grid md:grid-cols-2 gap-4 mt-2">
                            <div>
                              <div className="text-xs text-muted-foreground uppercase">Target Concept Node</div>
                              <div className="text-lg font-bold text-mint mt-1">{rec.concept}</div>
                              
                              <div className="text-xs text-muted-foreground uppercase mt-4">Reasoning</div>
                              <p className="text-sm text-gray-300 mt-1">{rec.reason || rec.reasoning}</p>

                              <div className="text-xs text-muted-foreground uppercase mt-4">Evidence Summary</div>
                              <div className="text-sm text-gray-400 mt-1 font-mono bg-white/5 p-2 rounded">{rec.evidence}</div>
                            </div>

                            <div className="border-t md:border-t-0 md:border-l border-white/10 md:pl-6 pt-4 md:pt-0 flex flex-col justify-between">
                              <div>
                                <div className="text-xs text-muted-foreground uppercase">Suggested Action</div>
                                <p className="text-sm text-white font-semibold mt-1 leading-relaxed bg-mint/5 p-3 rounded-xl border border-mint/20">{rec.suggestedAction}</p>

                                <div className="grid grid-cols-2 gap-2 mt-3">
                                  <div>
                                    <div className="text-xs text-muted-foreground uppercase">Expected Cognitive Gain</div>
                                    <div className="text-xs text-emerald-400 font-semibold mt-1">{rec.expectedGain}</div>
                                  </div>
                                  {rec.validationExercise && (
                                    <div>
                                      <div className="text-xs text-muted-foreground uppercase">Validation Exercise</div>
                                      <div className="text-xs text-indigo-300 font-semibold mt-1">{rec.validationExercise}</div>
                                    </div>
                                  )}
                                </div>
                              </div>

                              <div className="flex items-center gap-2 mt-6">
                                <Button onClick={() => handleCopilotAction(rec.id, "Accept")} size="sm" className="bg-emerald-500 hover:bg-emerald-600 text-black font-bold">
                                  Accept Recommendation
                                </Button>
                                <Button onClick={() => handleCopilotAction(rec.id, "Modify")} size="sm" variant="outline" className="border-white/10 text-white font-bold">
                                  Modify
                                </Button>
                                <Button onClick={() => handleCopilotAction(rec.id, "Ignore")} size="sm" variant="ghost" className="text-muted-foreground hover:text-white">
                                  Ignore
                                </Button>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Improve View */}
              {activeMode === "improve" && (
                <motion.div
                  key="improve"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-8"
                >
                  <div className="grid gap-6 md:grid-cols-2">
                    
                    {/* Structured notes form (Learn Layer) */}
                    <div className="rounded-3xl border border-white/10 p-6 bg-card">
                      <h3 className="text-lg font-bold">Log Retraining Telemetry Notes</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Teacher notes build dataset feedback loops to retrain cognitive classification models.
                      </p>

                      <div className="space-y-4 mt-6">
                        <select
                          value={noteRoomCode}
                          onChange={(e) => setNoteRoomCode(e.target.value)}
                          className="p-3 rounded-xl bg-black border text-white w-full text-sm"
                        >
                          <option value="">Select room code</option>
                          {teacherRooms.map((r) => (
                            <option key={r.room_code} value={r.room_code}>
                              {r.room_code} ({r.subject})
                            </option>
                          ))}
                        </select>

                        <div className="space-y-2">
                          <label className="text-xs uppercase text-muted-foreground">1. Observation</label>
                          <input
                            value={noteObs}
                            onChange={(e) => setNoteObs(e.target.value)}
                            placeholder="e.g. Students answered roots calculation instantly but failed graph interpretations."
                            className="p-3 rounded-xl bg-black border text-white w-full text-sm"
                          />
                        </div>

                        <div className="space-y-2">
                          <label className="text-xs uppercase text-muted-foreground">2. Underlying Reason</label>
                          <input
                            value={noteReason}
                            onChange={(e) => setNoteReason(e.target.value)}
                            placeholder="e.g. Formula memorization is high but coordinate mapping links are weak."
                            className="p-3 rounded-xl bg-black border text-white w-full text-sm"
                          />
                        </div>

                        <div className="space-y-2">
                          <label className="text-xs uppercase text-muted-foreground">3. Action Taken</label>
                          <input
                            value={noteAction}
                            onChange={(e) => setNoteAction(e.target.value)}
                            placeholder="e.g. Conducted a 15 min interactive graphing demonstration."
                            className="p-3 rounded-xl bg-black border text-white w-full text-sm"
                          />
                        </div>

                        <div className="space-y-2">
                          <label className="text-xs uppercase text-muted-foreground">4. Expected Outcome</label>
                          <input
                            value={noteOutcome}
                            onChange={(e) => setNoteOutcome(e.target.value)}
                            placeholder="e.g. Committing to graphing tasks faster with lower hovering drift."
                            className="p-3 rounded-xl bg-black border text-white w-full text-sm"
                          />
                        </div>

                        <Button onClick={handleSaveNotes} className="bg-mint hover:bg-mint-glow text-black font-bold w-full mt-4">
                          Log Notes to ML Training Layer
                        </Button>
                      </div>
                    </div>

                    {/* Historical Notes Feed */}
                    <div className="rounded-3xl border border-white/10 p-6 bg-card">
                      <h3 className="text-lg font-bold">Feedback Dataset Logs (Retraining Pool)</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Active feedback dataset containing validated human inputs.
                      </p>

                      <div className="mt-6 space-y-4 max-h-[460px] overflow-y-auto pr-2">
                        {noteHistory.length === 0 ? (
                          <div className="text-center py-12 text-muted-foreground text-sm">
                            Select a room code above with notes to view dataset records.
                          </div>
                        ) : (
                          noteHistory.map((note) => (
                            <div key={note.id} className="border border-white/10 rounded-xl p-4 bg-black text-xs space-y-2">
                              <div className="flex justify-between items-center text-muted-foreground">
                                <span>Room: {note.room_code}</span>
                                <span>{new Date(note.created_at).toLocaleDateString()}</span>
                              </div>
                              <div><strong className="text-mint">Observation:</strong> {note.observation}</div>
                              <div><strong className="text-white">Reason:</strong> {note.reason}</div>
                              <div><strong className="text-white">Action:</strong> {note.action_taken}</div>
                              <div><strong className="text-white">Outcome:</strong> {note.outcome}</div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Cohort Batch Comparison (Longitudinal Trends) */}
                  <div className="rounded-3xl border border-white/10 p-6 bg-card">
                    <h3 className="text-lg font-bold flex items-center gap-1.5"><BarChart2 className="h-5 w-5 text-mint" /> Cohort Intelligence (Batch Comparison)</h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      Compare conceptual mastery rates and cognitive hesitation metrics longitudinally across batches or classroom sections.
                    </p>

                    <div className="flex flex-wrap items-center gap-4 mt-6">
                      <select
                        value={compareRoomA}
                        onChange={(e) => setCompareRoomA(e.target.value)}
                        className="p-3 rounded-xl bg-black border text-white text-sm"
                      >
                        <option value="">Select Cohort Room A</option>
                        {cohorts.map((c) => (
                          <option key={c.room_code} value={c.room_code}>
                            {c.label} ({c.student_count} students)
                          </option>
                        ))}
                      </select>

                      <span className="text-muted-foreground text-sm">VS</span>

                      <select
                        value={compareRoomB}
                        onChange={(e) => setCompareRoomB(e.target.value)}
                        className="p-3 rounded-xl bg-black border text-white text-sm"
                      >
                        <option value="">Select Cohort Room B</option>
                        {cohorts.map((c) => (
                          <option key={c.room_code} value={c.room_code}>
                            {c.label} ({c.student_count} students)
                          </option>
                        ))}
                      </select>
                    </div>

                    {activeComparison && activeComparison.rA && activeComparison.rB ? (
                      <div className="grid md:grid-cols-2 gap-6 mt-6 border-t border-white/10 pt-6">
                        <div className="bg-black/50 border border-white/10 rounded-2xl p-5">
                          <h4 className="text-sm font-semibold text-mint">{activeComparison.rA.label}</h4>
                          <div className="mt-4 grid grid-cols-2 gap-4">
                            <div>
                              <div className="text-[10px] text-muted-foreground uppercase">Mastery Success Rate</div>
                              <div className="text-2xl font-bold font-display mt-1 text-white">{activeComparison.rA.success_rate}%</div>
                            </div>
                            <div>
                              <div className="text-[10px] text-muted-foreground uppercase">Avg Cognitive Hesitation</div>
                              <div className="text-2xl font-bold font-display mt-1 text-white">{activeComparison.rA.avg_hesitation}%</div>
                            </div>
                          </div>
                        </div>

                        <div className="bg-black/50 border border-white/10 rounded-2xl p-5">
                          <h4 className="text-sm font-semibold text-mint">{activeComparison.rB.label}</h4>
                          <div className="mt-4 grid grid-cols-2 gap-4">
                            <div>
                              <div className="text-[10px] text-muted-foreground uppercase">Mastery Success Rate</div>
                              <div className="text-2xl font-bold font-display mt-1 text-white">{activeComparison.rB.success_rate}%</div>
                            </div>
                            <div>
                              <div className="text-[10px] text-muted-foreground uppercase">Avg Cognitive Hesitation</div>
                              <div className="text-2xl font-bold font-display mt-1 text-white">{activeComparison.rB.avg_hesitation}%</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-10 text-muted-foreground text-sm">
                        Select two cohort rooms from above to trigger cross-cohort comparative analysis.
                      </div>
                    )}
                  </div>
                </motion.div>
              )}

              {/* Assessment Designer (Blueprint Form) */}
              {activeMode === "designer" && (
                <motion.div
                  key="designer"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="grid gap-6 md:grid-cols-2"
                >
                  <div className="rounded-3xl border border-white/10 p-6 bg-card">
                    {/* Step Wizard Header */}
                    <div className="flex items-center justify-between border-b border-white/5 pb-4 mb-6">
                      <div className="flex items-center gap-2">
                        {[1, 2, 3, 4].map((step) => (
                          <div key={step} className="flex items-center gap-1.5">
                            <span
                              className={`h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                                wizardStep === step
                                  ? "bg-mint text-black"
                                  : wizardStep > step
                                  ? "bg-mint/20 text-mint"
                                  : "bg-white/5 text-muted-foreground border border-white/10"
                              }`}
                            >
                              {step}
                            </span>
                            <span
                              className={`text-[10px] uppercase font-bold tracking-wider hidden sm:inline ${
                                wizardStep === step ? "text-white" : "text-muted-foreground"
                              }`}
                            >
                              {step === 1 ? "Subject" : step === 2 ? "Topic" : step === 3 ? "Params" : "Launch"}
                            </span>
                            {step < 4 && <span className="h-px w-4 bg-white/10 mx-1 hidden sm:inline" />}
                          </div>
                        ))}
                      </div>
                      <span className="text-[10px] uppercase font-bold text-mint tracking-wider">
                        Assessment Builder
                      </span>
                    </div>

                    {/* Step 1: Choose Subject */}
                    {wizardStep === 1 && (
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-base font-bold text-white uppercase tracking-wider font-display">CREATE YOUR TEST</h4>
                          <p className="text-xs text-muted-foreground mt-0.5">Configure how Cognify evaluates thinking.</p>
                        </div>
                        <div className="grid gap-2 grid-cols-2">
                          {Object.entries(SUBJECT_MAP).map(([key, val]) => (
                            <button
                              key={key}
                              onClick={() => {
                                handleSubjectChange(key);
                                setWizardStep(2);
                              }}
                              className={`p-4 rounded-xl border text-left transition-all card-hover-lift btn-active-push ${
                                bpSubject === key
                                  ? "border-mint bg-transparent text-mint font-bold"
                                  : "border-white/10 bg-black/40 text-gray-300 hover:border-white/20 hover:text-white"
                              }`}
                            >
                              <span className="text-[9px] uppercase font-bold block opacity-75">Domain</span>
                              <span className="text-sm font-bold block mt-1">{val.label}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Step 2: Choose Topic & Subtopic */}
                    {wizardStep === 2 && (
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-base font-bold text-white uppercase tracking-wider font-display">SELECT TOPIC & SUBTOPIC</h4>
                          <p className="text-xs text-muted-foreground mt-0.5">Choose diagnostic parameters.</p>
                        </div>
                        <div className="grid gap-2 max-h-[300px] overflow-y-auto pr-2">
                          {SUBJECT_MAP[bpSubject] && Object.entries(SUBJECT_MAP[bpSubject].topics).map(([key, val]) => (
                            <div
                              key={key}
                              className={`p-3 rounded-xl border transition-all ${
                                bpTopic === key
                                  ? "border-mint bg-transparent"
                                  : "border-white/10 bg-black/40"
                              }`}
                            >
                              <div className="flex items-center justify-between border-b border-white/5 pb-2 mb-2">
                                <span className="text-xs font-bold text-white">{val.label}</span>
                                <button
                                  onClick={() => handleTopicChange(key)}
                                  className={`px-2 py-0.5 rounded text-[10px] font-bold transition-all ${
                                    bpTopic === key ? "bg-mint text-black" : "bg-white/10 text-white"
                                  }`}
                                >
                                  Select Topic
                                </button>
                              </div>
                              
                              <div className="flex flex-wrap gap-2 mt-2">
                                {Object.entries(val.subtopics).map(([subKey, subVal]) => (
                                  <button
                                    key={subKey}
                                    onClick={() => {
                                      handleTopicChange(key);
                                      setBpSubtopic(subKey);
                                    }}
                                    className={`px-3 py-1 rounded-lg border text-[11px] font-semibold transition-all ${
                                      bpTopic === key && bpSubtopic === subKey
                                        ? "border-orange-500 bg-transparent text-orange-400"
                                        : "border-white/10 bg-black/20 text-gray-400 hover:text-white"
                                    }`}
                                  >
                                    {subVal}
                                  </button>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                        <div className="flex justify-between pt-4 border-t border-white/5">
                          <button onClick={() => setWizardStep(1)} className="px-4 py-2 rounded-lg bg-secondary border border-white/10 text-xs font-bold text-white btn-active-push">
                            Back
                          </button>
                          <button
                            onClick={() => setWizardStep(3)}
                            className="px-4 py-2 rounded-lg bg-mint text-black text-xs font-bold btn-active-push"
                          >
                            Next
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Step 3: Configure Parameters */}
                    {wizardStep === 3 && (
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-base font-bold text-white uppercase tracking-wider font-display">DIAGNOSTIC TARGETS</h4>
                          <p className="text-xs text-muted-foreground mt-0.5">Control evaluation metrics.</p>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-3">
                          <div className="space-y-1">
                            <label className="text-[10px] uppercase text-muted-foreground font-bold">Purpose</label>
                            <select
                              value={bpPurpose}
                              onChange={(e) => setBpPurpose(e.target.value)}
                              className="p-2.5 rounded-xl bg-black border border-white/10 text-white w-full text-xs focus:outline-none focus:border-mint"
                            >
                              <option value="diagnosis">Diagnosis</option>
                              <option value="practice">Practice</option>
                              <option value="exam">Exam</option>
                            </select>
                          </div>

                          <div className="space-y-1">
                            <label className="text-[10px] uppercase text-muted-foreground font-bold">Difficulty</label>
                            <select
                              value={bpDifficulty}
                              onChange={(e) => setBpDifficulty(e.target.value)}
                              className="p-2.5 rounded-xl bg-black border border-white/10 text-white w-full text-xs focus:outline-none focus:border-mint"
                            >
                              <option value="easy">Easy</option>
                              <option value="medium">Medium</option>
                              <option value="hard">Hard</option>
                              <option value="adaptive">Adaptive</option>
                            </select>
                          </div>
                        </div>

                        <div className="grid grid-cols-3 gap-2">
                          <div className="space-y-1">
                            <label className="text-[10px] uppercase text-muted-foreground font-bold">Duration (Min)</label>
                            <input
                              type="number"
                              value={bpDuration}
                              onChange={(e) => setBpDuration(Number(e.target.value))}
                              className="p-2.5 rounded-xl bg-black border border-white/10 text-white w-full text-xs focus:outline-none focus:border-mint"
                            />
                          </div>

                          <div className="space-y-1">
                            <label className="text-[10px] uppercase text-muted-foreground font-bold">Questions</label>
                            <input
                              type="number"
                              value={bpQuestionCount}
                              onChange={(e) => setBpQuestionCount(Number(e.target.value))}
                              className="p-2.5 rounded-xl bg-black border border-white/10 text-white w-full text-xs focus:outline-none focus:border-mint"
                            />
                          </div>

                          <div className="space-y-1">
                            <label className="text-[10px] uppercase text-muted-foreground font-bold">Strategy</label>
                            <select
                              value={bpStrategy}
                              onChange={(e) => setBpStrategy(e.target.value)}
                              className="p-2.5 rounded-xl bg-black border border-white/10 text-white w-full text-[10px] focus:outline-none focus:border-mint"
                            >
                              <option value="balanced">Balanced</option>
                              <option value="random">Random</option>
                              <option value="adaptive_mixed">Adaptive</option>
                            </select>
                          </div>
                        </div>

                        <div className="border border-white/5 rounded-2xl p-4 bg-black/40 space-y-3 text-[11px]">
                          <div className="font-bold flex justify-between">
                            <span>Cognitive Type Distribution</span>
                            <span className={Number(bpConceptual)+Number(bpApplication)+Number(bpReasoning)+Number(bpMemory) !== 100 ? "text-rose-400 font-bold" : "text-mint font-bold"}>
                              {Number(bpConceptual)+Number(bpApplication)+Number(bpReasoning)+Number(bpMemory)}% (Target: 100%)
                            </span>
                          </div>
                          
                          <div className="space-y-1">
                            <div className="flex justify-between text-gray-300">
                              <span>Conceptual</span>
                              <span>{bpConceptual}%</span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max={100 - (Number(bpApplication) + Number(bpReasoning) + Number(bpMemory))}
                              value={bpConceptual}
                              onChange={(e) => setBpConceptual(Number(e.target.value))}
                              className="w-full h-1 bg-white/10 accent-mint rounded"
                            />
                          </div>
                          
                          <div className="space-y-1">
                            <div className="flex justify-between text-gray-300">
                              <span>Application</span>
                              <span>{bpApplication}%</span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max={100 - (Number(bpConceptual) + Number(bpReasoning) + Number(bpMemory))}
                              value={bpApplication}
                              onChange={(e) => setBpApplication(Number(e.target.value))}
                              className="w-full h-1 bg-white/10 accent-mint rounded"
                            />
                          </div>

                          <div className="space-y-1">
                            <div className="flex justify-between text-gray-300">
                              <span>Reasoning</span>
                              <span>{bpReasoning}%</span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max={100 - (Number(bpConceptual) + Number(bpApplication) + Number(bpMemory))}
                              value={bpReasoning}
                              onChange={(e) => setBpReasoning(Number(e.target.value))}
                              className="w-full h-1 bg-white/10 accent-mint rounded"
                            />
                          </div>

                          <div className="space-y-1">
                            <div className="flex justify-between text-gray-300">
                              <span>Memory</span>
                              <span>{bpMemory}%</span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max={100 - (Number(bpConceptual) + Number(bpApplication) + Number(bpReasoning))}
                              value={bpMemory}
                              onChange={(e) => setBpMemory(Number(e.target.value))}
                              className="w-full h-1 bg-white/10 accent-mint rounded"
                            />
                          </div>
                        </div>

                        <div className="flex justify-between pt-4 border-t border-white/5">
                          <button onClick={() => setWizardStep(2)} className="px-4 py-2 rounded-lg bg-secondary border border-white/10 text-xs font-bold text-white btn-active-push">
                            Back
                          </button>
                          <button
                            onClick={() => setWizardStep(4)}
                            className="px-4 py-2 rounded-lg bg-mint text-black text-xs font-bold btn-active-push"
                          >
                            Next
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Step 4: Review & Launch */}
                    {wizardStep === 4 && (
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-base font-bold text-white uppercase tracking-wider font-display">REVIEW & LAUNCH</h4>
                          <p className="text-xs text-muted-foreground mt-0.5">Deploy diagnostic test room.</p>
                        </div>
                        
                        <div className="rounded-xl border border-white/10 p-4 bg-black/40 space-y-2 text-xs">
                          <div>
                            <span className="text-muted-foreground uppercase text-[9px] font-bold">Selected Domain</span>
                            <p className="text-sm font-bold text-white capitalize">{bpSubject} ➔ {bpTopic.replace(/_/g, ' ')} ➔ {bpSubtopic.replace(/_/g, ' ')}</p>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-white/5">
                            <div>
                              <span className="text-muted-foreground uppercase text-[9px] font-bold">Assess Strategy</span>
                              <p className="font-semibold text-white capitalize">{bpStrategy}</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground uppercase text-[9px] font-bold">Questions Count</span>
                              <p className="font-semibold text-white">{bpQuestionCount} Items ({bpDuration} mins)</p>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-1">
                          <label className="text-xs uppercase text-muted-foreground font-bold">Name this Blueprint</label>
                          <input
                            value={bpName}
                            onChange={(e) => setBpName(e.target.value)}
                            placeholder="e.g. Mid Semester Diagnostic"
                            className="p-3 rounded-xl bg-black border border-white/10 text-white w-full text-sm focus:outline-none focus:border-mint"
                          />
                        </div>

                        <div className="flex justify-between pt-4 border-t border-white/5">
                          <button onClick={() => setWizardStep(3)} className="px-4 py-2 rounded-lg bg-secondary border border-white/10 text-xs font-bold text-white btn-active-push">
                            Back
                          </button>
                          <Button
                            onClick={async (e) => {
                              if (!bpName.trim()) {
                                toast({ title: "Please name this blueprint", variant: "destructive" });
                                return;
                              }
                              await handleCreateBlueprint(e);
                              setWizardStep(1); // Reset step on success
                            }}
                            className="bg-mint hover:bg-mint-glow text-black font-bold px-6 py-2 rounded-lg btn-active-push"
                          >
                            Launch Assessment Room
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Add Custom Question Builder */}
                  <div className="rounded-3xl border border-white/10 p-6 bg-card space-y-4">
                    <div>
                      <h3 className="text-xl font-bold">Custom MCQ Repository Builder</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Build and seed custom questions into the database subject to automatic AI Validation duplicate checking.
                      </p>
                    </div>

                    <div className="space-y-3 mt-4 text-xs">
                      <div className="space-y-1">
                        <label className="text-muted-foreground uppercase text-[10px]">Prompt / Question Text</label>
                        <textarea
                          rows={2}
                          value={customPrompt}
                          onChange={(e) => setCustomPrompt(e.target.value)}
                          placeholder="e.g. What is the nature of roots when discriminant equals zero?"
                          className="p-2.5 rounded-xl bg-black border text-white w-full"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div className="space-y-1">
                          <label className="text-muted-foreground uppercase text-[10px]">Option A</label>
                          <input value={optA} onChange={(e) => setOptA(e.target.value)} className="p-2 bg-black border text-white w-full rounded-lg" />
                        </div>
                        <div className="space-y-1">
                          <label className="text-muted-foreground uppercase text-[10px]">Option B</label>
                          <input value={optB} onChange={(e) => setOptB(e.target.value)} className="p-2 bg-black border text-white w-full rounded-lg" />
                        </div>
                        <div className="space-y-1">
                          <label className="text-muted-foreground uppercase text-[10px]">Option C</label>
                          <input value={optC} onChange={(e) => setOptC(e.target.value)} className="p-2 bg-black border text-white w-full rounded-lg" />
                        </div>
                        <div className="space-y-1">
                          <label className="text-muted-foreground uppercase text-[10px]">Option D</label>
                          <input value={optD} onChange={(e) => setOptD(e.target.value)} className="p-2 bg-black border text-white w-full rounded-lg" />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-2">
                        <div className="space-y-1">
                          <label className="text-muted-foreground uppercase text-[10px]">Correct Answer Index</label>
                          <select value={correctIdx} onChange={(e) => setCorrectIdx(Number(e.target.value))} className="p-2 bg-black border text-white w-full rounded-lg">
                            <option value={0}>Option A</option>
                            <option value={1}>Option B</option>
                            <option value={2}>Option C</option>
                            <option value={3}>Option D</option>
                          </select>
                        </div>

                        <div className="space-y-1">
                          <label className="text-muted-foreground uppercase text-[10px]">Cognitive Category</label>
                          <select value={customCategory} onChange={(e) => setCustomCategory(e.target.value)} className="p-2 bg-black border text-white w-full rounded-lg">
                            <option value="conceptual">Conceptual</option>
                            <option value="application">Application</option>
                            <option value="reasoning">Reasoning</option>
                            <option value="memory">Memory</option>
                          </select>
                        </div>

                        <div className="space-y-1">
                          <label className="text-muted-foreground uppercase text-[10px]">Cognitive Load</label>
                          <select value={customLoad} onChange={(e) => setCustomLoad(e.target.value)} className="p-2 bg-black border text-white w-full rounded-lg">
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                          </select>
                        </div>
                      </div>

                      <div className="space-y-1">
                        <label className="text-muted-foreground uppercase text-[10px]">Explanation</label>
                        <input value={customExpl} onChange={(e) => setCustomExpl(e.target.value)} placeholder="Provide context or explanation for correct choice" className="p-2 bg-black border text-white w-full rounded-lg" />
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div className="space-y-1">
                          <label className="text-muted-foreground uppercase text-[10px]">Relational Concepts (Comma separated)</label>
                          <input value={customConcepts} onChange={(e) => setCustomConcepts(e.target.value)} placeholder="e.g. Discriminant, Roots" className="p-2 bg-black border text-white w-full rounded-lg" />
                        </div>
                        <div className="space-y-1">
                          <label className="text-muted-foreground uppercase text-[10px]">Tags (e.g. Formula, Visualization)</label>
                          <input value={customTags} onChange={(e) => setCustomTags(e.target.value)} placeholder="Formula, Logic" className="p-2 bg-black border text-white w-full rounded-lg" />
                        </div>
                      </div>

                      <Button onClick={handleAddQuestion} className="bg-mint hover:bg-mint-glow text-black font-bold w-full mt-4">
                        Add Question to Repository
                      </Button>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Question Lifecycle Manager */}
              {activeMode === "lifecycle" && (
                <motion.div
                  key="lifecycle"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="w-full text-xs"
                >
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[750px] items-stretch">
                    
                    {/* 1. LEFT SIDEBAR: QUESTION LIST NAVIGATOR (col-span-3) */}
                    <div className="lg:col-span-3 rounded-3xl border border-white/10 p-4 bg-card flex flex-col gap-4 max-h-[750px]">
                      <div>
                        <h3 className="text-sm font-bold flex items-center gap-1.5 text-white">
                          <Search className="h-4 w-4 text-mint" /> MCQ Navigator
                        </h3>
                        <p className="text-[10px] text-muted-foreground mt-0.5">
                          Filter and analyze question assets.
                        </p>
                      </div>

                      <div className="space-y-2">
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="Search questions..."
                          className="w-full p-2.5 rounded-xl bg-black border border-white/10 text-white text-xs"
                        />
                        
                        <div className="grid grid-cols-2 gap-2 text-[10px]">
                          <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                            className="p-2 rounded-lg bg-black border border-white/10 text-gray-300"
                          >
                            <option value="all">All Status</option>
                            <option value="Draft">Draft</option>
                            <option value="AI Validation">AI Validated</option>
                            <option value="Pilot">Pilot</option>
                            <option value="Approved">Approved</option>
                            <option value="Low QQI">Low QQI</option>
                            <option value="Retired">Retired</option>
                          </select>

                          <select
                            value={filterDifficulty}
                            onChange={(e) => setFilterDifficulty(e.target.value)}
                            className="p-2 rounded-lg bg-black border border-white/10 text-gray-300"
                          >
                            <option value="all">All Difficulty</option>
                            <option value="easy">Easy</option>
                            <option value="medium">Medium</option>
                            <option value="hard">Hard</option>
                          </select>
                        </div>
                      </div>

                      <div className="flex-1 overflow-y-auto pr-1 space-y-2 max-h-[550px]">
                        {filteredQuestions.length === 0 ? (
                          <div className="text-center py-10 text-muted-foreground">
                            No MCQs match current filters.
                          </div>
                        ) : (
                          filteredQuestions.map((q) => {
                            const isSelected = selectedQuestionId === q.id;
                            let statusColor = "bg-gray-500/20 text-gray-400 border-gray-500/30";
                            if (q.status === "Approved") statusColor = "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
                            else if (q.status === "Pilot") statusColor = "bg-sky-500/20 text-sky-400 border-sky-500/30";
                            else if (q.status === "AI Validation") statusColor = "bg-amber-500/20 text-amber-400 border-amber-500/30";
                            else if (q.status === "Draft") statusColor = "bg-rose-500/20 text-rose-400 border-rose-500/30";
                            else if (q.status === "Low QQI") statusColor = "bg-orange-500/20 text-orange-400 border-orange-500/30";

                            return (
                              <button
                                key={q.id}
                                onClick={() => loadQuestionDetail(q.id)}
                                className={`w-full text-left p-3 rounded-xl border transition-all flex flex-col gap-2 ${
                                  isSelected 
                                    ? "bg-mint/10 border-mint text-white" 
                                    : "bg-black/40 border-white/5 hover:border-white/20 text-gray-300"
                                }`}
                              >
                                <div className="font-semibold line-clamp-2 text-[11px] leading-tight">
                                  {q.prompt}
                                </div>
                                <div className="flex items-center justify-between text-[9px] text-muted-foreground w-full">
                                  <div className="flex items-center gap-1.5">
                                    <span className={`px-1.5 py-0.5 rounded border text-[8px] font-semibold uppercase ${statusColor}`}>
                                      {q.status}
                                    </span>
                                    <span>v{q.version}</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="font-bold text-white">QQI: {Math.round(q.qqi_score)}%</span>
                                    <span>({Math.round((q.qqi_confidence || 0) * 100)}% C)</span>
                                  </div>
                                </div>
                              </button>
                            );
                          })
                        )}
                      </div>
                    </div>

                    {/* 2. MIDDLE WORKSPACE PANEL: INTERACTIVE EDITOR & PREVIEW (col-span-5) */}
                    <div className="lg:col-span-5 rounded-3xl border border-white/10 p-6 bg-card flex flex-col gap-4 max-h-[750px] overflow-y-auto">
                      {!selectedQuestionId || !questionDetail ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-center py-20 text-muted-foreground gap-3">
                          <Brain className="h-10 w-10 text-mint/30 animate-pulse" />
                          <div>
                            <div className="font-semibold text-white">Question Intelligence Workspace</div>
                            <div className="text-[10px] mt-1 max-w-[250px]">
                              Select an MCQ from the left navigator to review, edit, approve, and rollback versions.
                            </div>
                          </div>
                        </div>
                      ) : workspaceLoading ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-center py-20 text-muted-foreground gap-2">
                          <Activity className="h-8 w-8 text-mint animate-spin" />
                          <span>Loading question details...</span>
                        </div>
                      ) : (
                        <>
                          <div className="flex items-center justify-between border-b border-white/10 pb-3">
                            <div>
                              <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                                {isPreviewMode ? <Eye className="h-4 w-4 text-mint" /> : <Layers className="h-4 w-4 text-mint" />}
                                {isPreviewMode ? "MCQ Student Preview" : "MCQ Interactive Workspace"}
                              </h3>
                              <p className="text-[9px] text-muted-foreground">
                                ID: #{questionDetail.question.id} | Subject: {questionDetail.question.subject.toUpperCase()} | Version: {questionDetail.question.version}
                              </p>
                            </div>
                            
                            <button
                              onClick={() => setIsPreviewMode(!isPreviewMode)}
                              className="px-3 py-1.5 rounded-lg border border-white/10 bg-black hover:bg-black/80 hover:text-white transition text-[10px] font-semibold text-muted-foreground flex items-center gap-1"
                            >
                              {isPreviewMode ? "Open Editor Mode" : "Switch to Student View"}
                            </button>
                          </div>

                          {/* Render Student Preview Mode */}
                          {isPreviewMode ? (
                            <div className="space-y-4 flex-1">
                              <div className="rounded-2xl border border-mint/20 bg-black/60 p-5 space-y-4 shadow-sm relative overflow-hidden">
                                <div className="absolute right-3 top-3 px-2 py-0.5 rounded-md bg-mint/10 border border-mint/30 text-mint font-semibold uppercase text-[8px]">
                                  Student MCQ Preview
                                </div>
                                <div className="text-[12px] text-white font-medium pr-10">
                                  {editPrompt}
                                </div>

                                <div className="space-y-2 mt-4">
                                  {[editOptA, editOptB, editOptC, editOptD].map((opt, oIdx) => {
                                    const isCorrect = oIdx === editCorrectIdx;
                                    return (
                                      <div
                                        key={oIdx}
                                        className={`p-3 rounded-xl border text-[11px] flex items-center justify-between transition-all ${
                                          isCorrect
                                            ? "bg-mint/10 border-mint text-white font-semibold"
                                            : "bg-black/30 border-white/5 text-gray-300"
                                        }`}
                                      >
                                        <span>{opt}</span>
                                        {isCorrect && <Check className="h-4 w-4 text-mint font-bold" />}
                                      </div>
                                    );
                                  })}
                                </div>

                                {editExplanation && (
                                  <div className="p-3 rounded-xl bg-mint/5 border border-mint/10 mt-4 text-[10px] text-gray-400">
                                    <span className="font-bold text-mint">Explanation:</span> {editExplanation}
                                  </div>
                                )}
                              </div>

                              <div className="p-4 border border-white/10 rounded-2xl bg-black/40 space-y-3">
                                <div className="text-[10px] font-bold text-white uppercase tracking-wider">Expected Student Benchmarks</div>
                                <div className="grid grid-cols-2 gap-3 text-[10px]">
                                  <div className="p-2.5 rounded-xl bg-black/60 border border-white/5">
                                    <div className="text-muted-foreground">Expected Solve Time</div>
                                    <div className="text-lg font-bold font-display text-white mt-1">
                                      {editDifficulty === "easy" ? "20s" : editDifficulty === "medium" ? "45s" : "75s"}
                                    </div>
                                  </div>
                                  <div className="p-2.5 rounded-xl bg-black/60 border border-white/5">
                                    <div className="text-muted-foreground">Pedagogical Complexity</div>
                                    <div className="text-lg font-bold font-display text-mint mt-1 capitalize">
                                      {editCognitiveType}
                                    </div>
                                  </div>
                                </div>

                                <div className="p-3 rounded-xl bg-rose-500/5 border border-rose-500/10 text-[10px] text-rose-300">
                                  <div className="font-bold flex items-center gap-1"><AlertTriangle className="h-3.5 w-3.5" /> Behavioral Alert Profile</div>
                                  <p className="mt-1 text-[9px] text-gray-400">
                                    {editCognitiveType === "conceptual" 
                                      ? "Higher option clicks hesitation expected on incorrect options."
                                      : "Expected backspace rewrite events due to math/logic complexity."
                                    }
                                  </p>
                                </div>
                              </div>
                            </div>
                          ) : (
                            /* Editor Mode */
                            <div className="space-y-4 flex-1 text-[11px]">
                              <div className="space-y-1">
                                <label className="text-[9px] uppercase text-muted-foreground font-bold">Prompt / Question Text</label>
                                <textarea
                                  rows={2}
                                  value={editPrompt}
                                  onChange={(e) => setEditPrompt(e.target.value)}
                                  className="w-full p-2.5 rounded-xl bg-black border border-white/10 text-white text-xs"
                                />
                              </div>

                              <div className="grid grid-cols-2 gap-2.5">
                                <div className="space-y-1">
                                  <label className="text-[9px] uppercase text-muted-foreground font-bold">Option A</label>
                                  <input
                                    value={editOptA}
                                    onChange={(e) => setEditOptA(e.target.value)}
                                    className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                                  />
                                </div>
                                <div className="space-y-1">
                                  <label className="text-[9px] uppercase text-muted-foreground font-bold">Option B</label>
                                  <input
                                    value={editOptB}
                                    onChange={(e) => setEditOptB(e.target.value)}
                                    className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                                  />
                                </div>
                                <div className="space-y-1">
                                  <label className="text-[9px] uppercase text-muted-foreground font-bold">Option C</label>
                                  <input
                                    value={editOptC}
                                    onChange={(e) => setEditOptC(e.target.value)}
                                    className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                                  />
                                </div>
                                <div className="space-y-1">
                                  <label className="text-[9px] uppercase text-muted-foreground font-bold">Option D</label>
                                  <input
                                    value={editOptD}
                                    onChange={(e) => setEditOptD(e.target.value)}
                                    className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                                  />
                                </div>
                              </div>

                              <div className="grid grid-cols-3 gap-2">
                                <div className="space-y-1">
                                  <label className="text-[9px] uppercase text-muted-foreground font-bold">Correct Option</label>
                                  <select
                                    value={editCorrectIdx}
                                    onChange={(e) => setEditCorrectIdx(Number(e.target.value))}
                                    className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                                  >
                                    <option value={0}>Option A</option>
                                    <option value={1}>Option B</option>
                                    <option value={2}>Option C</option>
                                    <option value={3}>Option D</option>
                                  </select>
                                </div>

                                <div className="space-y-1">
                                  <label className="text-[9px] uppercase text-muted-foreground font-bold">Difficulty</label>
                                  <select
                                    value={editDifficulty}
                                    onChange={(e) => setEditDifficulty(e.target.value)}
                                    className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                                  >
                                    <option value="easy">Easy</option>
                                    <option value="medium">Medium</option>
                                    <option value="hard">Hard</option>
                                  </select>
                                </div>

                                <div className="space-y-1">
                                  <label className="text-[9px] uppercase text-muted-foreground font-bold">Cognitive Type</label>
                                  <select
                                    value={editCognitiveType}
                                    onChange={(e) => setEditCognitiveType(e.target.value)}
                                    className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                                  >
                                    <option value="conceptual">Conceptual</option>
                                    <option value="application">Application</option>
                                    <option value="reasoning">Reasoning</option>
                                    <option value="memory">Memory</option>
                                  </select>
                                </div>
                              </div>

                              <div className="space-y-1">
                                <label className="text-[9px] uppercase text-muted-foreground font-bold">Explanation</label>
                                <input
                                  value={editExplanation}
                                  onChange={(e) => setEditExplanation(e.target.value)}
                                  className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                                />
                              </div>

                              <div className="space-y-1">
                                <label className="text-[9px] uppercase text-muted-foreground font-bold">Academic Concept Map (comma-separated)</label>
                                <input
                                  value={editConcepts}
                                  onChange={(e) => setEditConcepts(e.target.value)}
                                  className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                                />
                              </div>

                              {/* Impact Predictor Panel (Change 5) */}
                              <div className="border border-white/10 rounded-2xl p-4 bg-black/40 space-y-3">
                                <div className="flex items-center justify-between">
                                  <span className="text-[9px] uppercase font-bold text-white tracking-wider flex items-center gap-1">
                                    <Sparkles className="h-3.5 w-3.5 text-mint" /> Revision Impact Predictor
                                  </span>
                                  <button
                                    onClick={handlePredictImpact}
                                    disabled={predictingImpact}
                                    className="px-2.5 py-1 rounded bg-mint text-black font-semibold hover:bg-mint-glow disabled:opacity-50 text-[9px]"
                                  >
                                    {predictingImpact ? "Predicting..." : "Predict QQI Impact"}
                                  </button>
                                </div>

                                {impactPrediction && (
                                  <div className="space-y-2 animate-fadeIn text-[10px]">
                                    <div className="flex items-center justify-between border-b border-white/5 pb-2">
                                      <div>
                                        <div className="text-muted-foreground">Expected QQI Score</div>
                                        <div className="text-sm font-bold text-white flex items-center gap-1.5 mt-0.5">
                                          <span>{impactPrediction.current_qqi}</span>
                                          <ArrowRight className="h-3 w-3 text-mint" />
                                          <span className="text-mint">{impactPrediction.predicted_qqi}%</span>
                                        </div>
                                      </div>
                                      <div className="text-right">
                                        <div className="text-muted-foreground">Confidence Level</div>
                                        <div className="text-xs font-bold text-emerald-400 mt-1">HIGH</div>
                                      </div>
                                    </div>
                                    <div className="space-y-1.5">
                                      <div className="text-[8px] uppercase text-muted-foreground">AI Rationale:</div>
                                      {impactPrediction.reasons.map((r: string, idx: number) => (
                                        <div key={idx} className="flex items-start gap-1 text-[9px] text-gray-300 leading-tight">
                                          <span className="text-mint font-bold">•</span>
                                          <span>{r}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>

                              {/* Save Audit Trail Revision & Lifecycle controls */}
                              <div className="space-y-3 border-t border-white/10 pt-4">
                                <div className="space-y-1">
                                  <label className="text-[9px] uppercase text-rose-300 font-bold">Audit Trail change reason (Required)</label>
                                  <div className="flex gap-2">
                                    <input
                                      type="text"
                                      value={changeReason}
                                      onChange={(e) => setChangeReason(e.target.value)}
                                      placeholder="e.g. Clarified options logic, fixed math syntax..."
                                      className="flex-1 p-2 bg-black border border-white/10 text-white rounded-lg text-xs"
                                    />
                                    <button
                                      onClick={handleSaveQuestionEdit}
                                      className="px-4 py-2 bg-mint hover:bg-mint-glow text-black font-bold rounded-lg flex items-center gap-1 hover:shadow-lg hover:shadow-mint/20 transition-all text-xs"
                                    >
                                      <Save className="h-4 w-4" /> Save Revision
                                    </button>
                                  </div>
                                </div>

                                <div className="flex items-center justify-between border-t border-white/5 pt-3">
                                  <span className="text-[9px] text-muted-foreground">Manual Status Override:</span>
                                  <div className="flex gap-1.5 text-[9px]">
                                    <button
                                      onClick={() => handleUpdateWorkspaceQuestionStatus(selectedQuestionId, "Approved")}
                                      className="px-2.5 py-1.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold hover:bg-emerald-500/20"
                                    >
                                      Approve
                                    </button>
                                    <button
                                      onClick={() => handleUpdateWorkspaceQuestionStatus(selectedQuestionId, "Pilot")}
                                      className="px-2.5 py-1.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 font-bold hover:bg-sky-500/20"
                                    >
                                      Send to Pilot
                                    </button>
                                    <button
                                      onClick={() => handleUpdateWorkspaceQuestionStatus(selectedQuestionId, "Retired")}
                                      className="px-2.5 py-1.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold hover:bg-rose-500/20"
                                    >
                                      Retire Asset
                                    </button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>

                    {/* 3. RIGHT SIDEBAR PANEL: DETAILED ANALYTICS DASHBOARD (col-span-4) */}
                    <div className="lg:col-span-4 rounded-3xl border border-white/10 p-4 bg-card flex flex-col gap-4 max-h-[750px] overflow-y-auto">
                      {!selectedQuestionId || !questionDetail ? (
                        <div className="flex-1 flex items-center justify-center text-center text-muted-foreground py-20">
                          Select a question to view telemetry and analytics.
                        </div>
                      ) : (
                        <>
                          <div className="flex border-b border-white/10 pb-1 text-[9px] font-bold text-gray-400 uppercase tracking-wider justify-between gap-1 overflow-x-auto">
                            <button
                              onClick={() => setActiveAnalyticsTab("qqi")}
                              className={`pb-2 px-1 border-b-2 transition ${
                                activeAnalyticsTab === "qqi" ? "border-mint text-white" : "border-transparent hover:text-white"
                              }`}
                            >
                              QQI Score
                            </button>
                            <button
                              onClick={() => setActiveAnalyticsTab("telemetry")}
                              className={`pb-2 px-1 border-b-2 transition ${
                                activeAnalyticsTab === "telemetry" ? "border-mint text-white" : "border-transparent hover:text-white"
                              }`}
                            >
                              Telemetry Cues
                            </button>
                            <button
                              onClick={() => setActiveAnalyticsTab("versions")}
                              className={`pb-2 px-1 border-b-2 transition ${
                                activeAnalyticsTab === "versions" ? "border-mint text-white" : "border-transparent hover:text-white"
                              }`}
                            >
                              Versions
                            </button>
                            <button
                              onClick={() => setActiveAnalyticsTab("concepts")}
                              className={`pb-2 px-1 border-b-2 transition ${
                                activeAnalyticsTab === "concepts" ? "border-mint text-white" : "border-transparent hover:text-white"
                              }`}
                            >
                              Graph & Reviews
                            </button>
                            <button
                              onClick={() => setActiveAnalyticsTab("audit")}
                              className={`pb-2 px-1 border-b-2 transition ${
                                activeAnalyticsTab === "audit" ? "border-mint text-white" : "border-transparent hover:text-white"
                              }`}
                            >
                              Audit
                            </button>
                          </div>

                          <div className="flex-1 text-[11px]">
                            
                            {/* Tab 1: QQI Explainability Panel */}
                            {activeAnalyticsTab === "qqi" && (
                              <div className="space-y-4">
                                {/* Health Card (Change 8) */}
                                <div className={`p-3 rounded-2xl border flex items-center justify-between ${
                                  questionDetail.health.color === "emerald" 
                                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                                    : questionDetail.health.color === "rose" 
                                    ? "bg-rose-500/10 text-rose-400 border-rose-500/20" 
                                    : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                }`}>
                                  <div>
                                    <div className="text-[8px] uppercase tracking-wider text-muted-foreground">MCQ Asset Health</div>
                                    <div className="text-sm font-bold flex items-center gap-1 mt-0.5">
                                      <Activity className="h-3.5 w-3.5" />
                                      {questionDetail.health.status}
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-[8px] uppercase tracking-wider text-muted-foreground">Action</div>
                                    <div className="text-xs font-bold font-display uppercase mt-0.5">
                                      {questionDetail.health.recommendation}
                                    </div>
                                  </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                  <div className="border border-white/5 rounded-2xl p-4 bg-black/60 text-center flex flex-col items-center justify-center">
                                    <div className="text-[9px] uppercase text-muted-foreground font-semibold">QQI Index</div>
                                    <div className="text-2xl font-bold font-display mt-2 text-white">
                                      {Math.round(questionDetail.question.qqi_score)}%
                                    </div>
                                  </div>
                                  <div className="border border-white/5 rounded-2xl p-4 bg-black/60 text-center flex flex-col items-center justify-center">
                                    <div className="text-[9px] uppercase text-muted-foreground font-semibold">Evidence Confidence</div>
                                    <div className="text-2xl font-bold font-display mt-2 text-mint">
                                      {Math.round((questionDetail.question.qqi_confidence || 0) * 100)}%
                                    </div>
                                  </div>
                                </div>

                                <div className="border border-white/5 rounded-2xl p-4 bg-black/60 space-y-3">
                                  <div className="text-[9px] uppercase text-muted-foreground font-bold tracking-wider">Explainability Breakdown</div>
                                  
                                  {[
                                    { name: "Concept Purity", key: "purity_score", weight: "12%" },
                                    { name: "Discrimination Index", key: "discrimination_score", weight: "15%" },
                                    { name: "Difficulty Stability", key: "difficulty_stability_score", weight: "10%" },
                                    { name: "Guess Resistance", key: "guess_resistance_score", weight: "10%" },
                                    { name: "Language Quality", key: "language_quality_score", weight: "8%" },
                                    { name: "Behavior Signal Strength", key: "behavior_signal_score", weight: "12%" },
                                    { name: "Knowledge Graph Mapping", key: "kg_mapping_score", weight: "12%" },
                                    { name: "Time Stability", key: "time_stability_score", weight: "8%" },
                                    { name: "Teacher Rating Score", key: "teacher_rating_score", weight: "8%" },
                                    { name: "Historical Reliability (EWMA)", key: "historical_reliability_score", weight: "5%" }
                                  ].map((m, idx) => {
                                    const score = questionDetail.question[m.key] || 80.0;
                                    let progColor = "bg-rose-500";
                                    if (score >= 80) progColor = "bg-emerald-500";
                                    else if (score >= 70) progColor = "bg-amber-500";

                                    return (
                                      <div key={idx} className="space-y-1 text-[10px]">
                                        <div className="flex justify-between text-gray-300">
                                          <span className="flex items-center gap-1">
                                            {m.name}
                                            <span className="text-[8px] text-muted-foreground font-medium">({m.weight})</span>
                                          </span>
                                          <span className="font-semibold text-white">{Math.round(score)}%</span>
                                        </div>
                                        <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                                          <div className={`h-full ${progColor}`} style={{ width: `${score}%` }} />
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            )}

                            {/* Tab 2: Student Telemetry Cues Panel (Change 3) */}
                            {activeAnalyticsTab === "telemetry" && (
                              <div className="space-y-4">
                                <div className="grid grid-cols-3 gap-2 text-center">
                                  <div className="p-3 bg-black/60 border border-white/5 rounded-2xl">
                                    <div className="text-[8px] uppercase text-muted-foreground">Responses</div>
                                    <div className="text-lg font-bold text-white font-display mt-1">
                                      {questionDetail.telemetry.total_responses}
                                    </div>
                                  </div>
                                  <div className="p-3 bg-black/60 border border-white/5 rounded-2xl">
                                    <div className="text-[8px] uppercase text-muted-foreground">Solve Rate</div>
                                    <div className="text-lg font-bold text-emerald-400 font-display mt-1">
                                      {questionDetail.telemetry.solve_rate}%
                                    </div>
                                  </div>
                                  <div className="p-3 bg-black/60 border border-white/5 rounded-2xl">
                                    <div className="text-[8px] uppercase text-muted-foreground">Avg Time</div>
                                    <div className="text-lg font-bold text-white font-display mt-1">
                                      {questionDetail.telemetry.avg_response_time}s
                                    </div>
                                  </div>
                                </div>

                                <div className="border border-white/5 rounded-2xl p-4 bg-black/60 space-y-3">
                                  <div className="text-[9px] uppercase text-muted-foreground font-bold tracking-wider">Option Clicks Distribution (Heatmap)</div>
                                  
                                  {["A", "B", "C", "D"].map((optLetter, oIdx) => {
                                    const count = questionDetail.telemetry.options_distribution[oIdx] || 0;
                                    const total = questionDetail.telemetry.total_responses || 1;
                                    const pct = Math.round((count / total) * 100);
                                    const isCorrect = oIdx === questionDetail.question.correct_index;

                                    return (
                                      <div key={oIdx} className="space-y-1 text-[10px]">
                                        <div className="flex justify-between text-gray-300">
                                          <span className="font-semibold flex items-center gap-1">
                                            Option {optLetter}
                                            {isCorrect && <span className="text-[8px] text-mint border border-mint/20 bg-mint/5 px-1 py-0.5 rounded">Correct</span>}
                                          </span>
                                          <span className="text-white font-medium">{count} responses ({pct}%)</span>
                                        </div>
                                        <div className="w-full h-2.5 bg-white/5 rounded overflow-hidden">
                                          <div 
                                            className={`h-full transition-all ${isCorrect ? "bg-mint" : "bg-white/20"}`} 
                                            style={{ width: `${pct || 1}%` }} 
                                          />
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>

                                <div className="border border-white/5 rounded-2xl p-4 bg-black/60 space-y-3">
                                  <div className="text-[9px] uppercase text-muted-foreground font-bold tracking-wider">Solve Latency Timeline Buckets</div>
                                  
                                  {Object.entries(questionDetail.telemetry.time_buckets).map(([bucket, pctVal]: any, idx) => (
                                    <div key={idx} className="space-y-1 text-[10px]">
                                      <div className="flex justify-between text-gray-300">
                                        <span>{bucket} duration</span>
                                        <span className="text-white font-medium">{pctVal}%</span>
                                      </div>
                                      <div className="w-full h-2 bg-white/5 rounded overflow-hidden">
                                        <div className="h-full bg-mint/60" style={{ width: `${pctVal}%` }} />
                                      </div>
                                    </div>
                                  ))}
                                </div>

                                <div className="border border-white/5 rounded-2xl p-4 bg-black/60 space-y-2">
                                  <div className="text-[9px] uppercase text-muted-foreground font-bold tracking-wider">Cognitive Behavior Signals</div>
                                  <div className="grid grid-cols-2 gap-2 text-[10px] text-gray-300">
                                    <div className="p-2 rounded bg-black/40 border border-white/5">
                                      <div className="text-muted-foreground text-[8px] uppercase">Hesitation Index</div>
                                      <div className="font-semibold text-white mt-0.5">{questionDetail.telemetry.avg_hesitation_score}%</div>
                                    </div>
                                    <div className="p-2 rounded bg-black/40 border border-white/5">
                                      <div className="text-muted-foreground text-[8px] uppercase">Avg Option Clicks</div>
                                      <div className="font-semibold text-white mt-0.5">{questionDetail.telemetry.avg_same_option_clicks} clicks</div>
                                    </div>
                                    <div className="p-2 rounded bg-black/40 border border-white/5">
                                      <div className="text-muted-foreground text-[8px] uppercase">Avg Rewrite Count</div>
                                      <div className="font-semibold text-white mt-0.5">{questionDetail.telemetry.avg_rewrite_count} times</div>
                                    </div>
                                    <div className="p-2 rounded bg-black/40 border border-white/5">
                                      <div className="text-muted-foreground text-[8px] uppercase">Avg Backspaces</div>
                                      <div className="font-semibold text-white mt-0.5">{questionDetail.telemetry.avg_backspace_count} keys</div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Tab 3: Version History Diff Panel (Change 1) */}
                            {activeAnalyticsTab === "versions" && (
                              <div className="space-y-4">
                                <div className="text-[9px] uppercase text-muted-foreground font-bold tracking-wider">MCQ Version Ledger</div>
                                <div className="relative border-l border-white/10 ml-3 pl-4 space-y-6">
                                  {questionDetail.versions.length === 0 ? (
                                    <div className="text-muted-foreground py-4 pl-2">
                                      No revision history logged yet. This is Version 1.
                                    </div>
                                  ) : (
                                    questionDetail.versions.map((ver: any, vIdx: number) => (
                                      <div key={ver.id} className="relative space-y-2">
                                        <div className="absolute -left-6.5 top-0.5 h-3.5 w-3.5 rounded-full border border-mint bg-black flex items-center justify-center">
                                          <div className="h-1.5 w-1.5 rounded-full bg-mint" />
                                        </div>
                                        
                                        <div className="flex items-center justify-between">
                                          <span className="font-bold text-white text-xs">Version {ver.version}</span>
                                          <span className="text-[8px] text-muted-foreground">{ver.edited_at}</span>
                                        </div>

                                        <div className="p-3 bg-black/60 border border-white/5 rounded-2xl space-y-2 text-[10px]">
                                          <div>
                                            <span className="text-muted-foreground">Author:</span> <span className="text-white font-medium">{ver.edited_by}</span>
                                          </div>
                                          <div>
                                            <span className="text-muted-foreground">Reason:</span> <span className="text-mint font-medium italic">"{ver.change_reason}"</span>
                                          </div>
                                          
                                          {ver.change_summary && (
                                            <div className="mt-2 border-t border-white/5 pt-2">
                                              <span className="text-[8px] uppercase text-muted-foreground block mb-1">Field Diffs:</span>
                                              <div className="text-[9px] text-rose-300 font-mono leading-tight whitespace-pre-line">
                                                {ver.change_summary.split(" | ").map((dStr: string, di: number) => (
                                                  <div key={di} className="flex gap-1 items-start">
                                                    <span className="text-mint font-bold">-</span>
                                                    <span>{dStr}</span>
                                                  </div>
                                                ))}
                                              </div>
                                            </div>
                                          )}

                                          {/* Rollback trigger (Change 1) */}
                                          {ver.version !== questionDetail.question.version && (
                                            <button
                                              onClick={() => handleRollbackVersion(ver.version)}
                                              className="mt-3 px-2 py-1 bg-black border border-white/10 hover:border-mint text-[9px] font-semibold text-gray-300 hover:text-white rounded-lg flex items-center gap-1 transition"
                                            >
                                              <RotateCcw className="h-3 w-3 text-mint" /> Rollback to Version {ver.version}
                                            </button>
                                          )}
                                        </div>
                                      </div>
                                    ))
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Tab 4: Concept Map Graph & Reviews (Change 4 & 6) */}
                            {activeAnalyticsTab === "concepts" && (
                              <div className="space-y-4">
                                <div className="border border-white/5 rounded-2xl p-4 bg-black/60 space-y-3">
                                  <div className="text-[9px] uppercase text-muted-foreground font-bold tracking-wider">Concept Graph Connection</div>
                                  
                                  {/* Indented Concept Hierarchy tree visualizer (Change 4) */}
                                  <div className="p-3 bg-black/40 rounded-xl border border-white/5 space-y-2 text-[10px] font-mono">
                                    <div className="text-white font-bold flex items-center gap-1.5">
                                      <span className="text-mint font-bold">Subject:</span>
                                      {questionDetail.question.subject.toUpperCase()}
                                    </div>
                                    <div className="pl-3 border-l border-white/15 py-1 text-gray-300 flex items-center gap-1">
                                      <span>├── Topic:</span>
                                      <span className="text-white">{questionDetail.question.topic}</span>
                                    </div>
                                    <div className="pl-6 border-l border-white/15 py-1 text-gray-300 flex items-center gap-1">
                                      <span>└── Subtopic:</span>
                                      <span className="text-white">{questionDetail.question.subtopic}</span>
                                    </div>
                                    <div className="pl-9 border-l border-mint/20 py-1.5 text-mint font-semibold flex flex-col gap-1.5">
                                      <div className="flex items-center gap-1.5">
                                        <span>└── Concept Node:</span>
                                      </div>
                                      
                                      <div className="space-y-1.5 pl-3">
                                        {questionDetail.concepts.map((c: any) => (
                                          <div key={c.id} className="text-white border border-mint/20 bg-mint/5 px-2.5 py-1 rounded-md text-[9px] inline-block shadow-sm">
                                            {c.name} <span className="text-[8px] text-gray-400 font-bold">(W: {c.weight})</span>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  </div>
                                </div>

                                <div className="border border-white/5 rounded-2xl p-4 bg-black/60 space-y-3">
                                  <div className="text-[9px] uppercase text-muted-foreground font-bold tracking-wider">Teacher Review Ledger (Change 6)</div>
                                  {questionDetail.reviews.length === 0 ? (
                                    <div className="text-muted-foreground py-2 text-center">No reviews submitted yet.</div>
                                  ) : (
                                    <div className="space-y-3">
                                      {questionDetail.reviews.map((rev: any) => (
                                        <div key={rev.id} className="p-3 bg-black/60 border border-white/5 rounded-xl space-y-2 text-[10px]">
                                          <div className="flex justify-between items-center border-b border-white/5 pb-1">
                                            <span className="font-bold text-white">{rev.teacher_email}</span>
                                            <span className="text-[8px] text-muted-foreground">{rev.submitted_at ? rev.submitted_at.substring(0, 10) : ""}</span>
                                          </div>
                                          
                                          <div className="grid grid-cols-2 gap-2 text-[9px] text-gray-300">
                                            <div>Language: <span className="text-white font-bold">{rev.language_rating}/5</span></div>
                                            <div>Difficulty: <span className="text-white font-bold">Lvl {rev.difficulty}</span></div>
                                            <div>Adopted Action: <span className="px-1.5 py-0.5 rounded bg-mint/10 text-mint font-semibold uppercase text-[8px]">{rev.action || "Accepted"}</span></div>
                                            <div>Solve Time: <span className="text-white font-bold">{rev.estimated_solve_time || 45}s</span></div>
                                          </div>
                                          
                                          {rev.change_reason && (
                                            <div className="text-[9px] text-gray-400 italic">
                                              Comment: "{rev.change_reason}"
                                            </div>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Tab 5: QQI History Audit Trail (Change 2) */}
                            {activeAnalyticsTab === "audit" && (
                              <div className="space-y-4">
                                <div className="text-[9px] uppercase text-muted-foreground font-bold tracking-wider">Historical QQI Recalculation Ledger</div>
                                <div className="space-y-3">
                                  {questionDetail.qqi_history.length === 0 ? (
                                    <div className="text-muted-foreground text-center py-4">No historical QQI events registered.</div>
                                  ) : (
                                    questionDetail.qqi_history.map((hist: any) => {
                                      const isPositive = hist.score_delta >= 0;
                                      return (
                                        <div key={hist.id} className="p-3 bg-black/60 border border-white/5 rounded-xl space-y-2 text-[10px]">
                                          <div className="flex justify-between items-center border-b border-white/5 pb-1">
                                            <span className="font-bold text-white flex items-center gap-1.5">
                                              <span>{hist.trigger_event}</span>
                                            </span>
                                            <span className="text-[8px] text-muted-foreground">{hist.timestamp ? hist.timestamp.substring(11, 16) : ""}</span>
                                          </div>

                                          <div className="flex items-center justify-between text-xs">
                                            <div>
                                              <span className="text-muted-foreground text-[9px] block">QQI SCORE</span>
                                              <span className="text-white font-bold font-display">{Math.round(hist.qqi_score)}%</span>
                                            </div>
                                            <div className="text-right">
                                              <span className="text-muted-foreground text-[9px] block">DELTA</span>
                                              <span className={`font-bold font-display ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
                                                {isPositive ? `+${hist.score_delta}` : hist.score_delta}%
                                              </span>
                                            </div>
                                          </div>

                                          {/* Subscore deltas explainability detail (Change 2) */}
                                          {hist.sub_score_deltas && Object.keys(hist.sub_score_deltas).length > 0 && (
                                            <div className="mt-2 border-t border-white/5 pt-2 text-[9px] space-y-1">
                                              <div className="text-[8px] uppercase tracking-wider text-muted-foreground font-bold">Sub-Score Recalibration details:</div>
                                              <div className="grid grid-cols-2 gap-1.5 text-gray-300">
                                                {Object.entries(hist.sub_score_deltas).map(([subKey, subVal]: any) => {
                                                  if (subVal === 0) return null;
                                                  const isSubPos = subVal > 0;
                                                  return (
                                                    <div key={subKey} className="flex justify-between items-center px-1 rounded bg-black/40 py-0.5">
                                                      <span className="capitalize">{subKey.replace("_", " ")}:</span>
                                                      <span className={`font-bold ${isSubPos ? "text-emerald-400" : "text-rose-400"}`}>
                                                        {isSubPos ? `+${subVal}` : subVal}
                                                      </span>
                                                    </div>
                                                  );
                                                })}
                                              </div>
                                            </div>
                                          )}
                                        </div>
                                      );
                                    })
                                  )}
                                </div>
                              </div>
                            )}

                          </div>
                        </>
                      )}
                    </div>

                  </div>
                </motion.div>
              )}

              {/* 3. KNOWLEDGE GRAPH EXPLORER (activeMode === "explorer") */}
              {activeMode === "explorer" && (
                <motion.div
                  key="explorer"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="w-full text-xs"
                >
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[750px] items-stretch">
                    
                    {/* LEFT PANEL: SUBJECT COVERAGE & HEALTH CARD (col-span-3) */}
                    <div className="lg:col-span-3 rounded-3xl border border-white/10 p-4 bg-card flex flex-col gap-4 max-h-[750px] overflow-y-auto">
                      <div>
                        <h3 className="text-sm font-bold flex items-center gap-1.5 text-white">
                          <Activity className="h-4 w-4 text-sky-400 animate-pulse" /> Living KG Dashboard
                        </h3>
                        <p className="text-[10px] text-muted-foreground mt-0.5">
                          Analyze academic coverage and dead nodes.
                        </p>
                      </div>

                      {/* Subject Selection */}
                      <div className="space-y-1.5">
                        <label className="text-[9px] uppercase font-bold text-muted-foreground">Select Domain</label>
                        <select
                          value={kgSubject}
                          onChange={(e) => setKgSubject(e.target.value)}
                          className="w-full p-2.5 rounded-xl bg-black border border-white/10 text-white text-xs font-semibold"
                        >
                          {Object.entries(SUBJECT_MAP).map(([key, val]) => (
                            <option key={key} value={key}>{val.label}</option>
                          ))}
                        </select>
                      </div>

                      {/* Graph Health Card (Change 7) */}
                      {kgHealth ? (
                        <div className="space-y-3">
                          <div className={`p-3.5 rounded-2xl border ${
                            kgHealth.healthy_status === "Healthy" 
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                              : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          }`}>
                            <div className="text-[8px] uppercase tracking-wider text-muted-foreground">Graph Health Status</div>
                            <div className="text-sm font-bold flex items-center gap-1 mt-0.5">
                              <Brain className="h-4 w-4" />
                              {kgHealth.healthy_status}
                            </div>
                            <div className="grid grid-cols-2 gap-2 mt-3 pt-2.5 border-t border-white/5 text-[9px] text-gray-300">
                              <div>Coverage: <span className="text-white font-bold">{kgHealth.coverage_pct}%</span></div>
                              <div>Weighted: <span className="text-sky-400 font-bold">{kgHealth.coverage_score}%</span></div>
                              <div>Active MCQs: <span className="text-white font-bold">{kgHealth.total_questions} items</span></div>
                              <div>Student Mastery: <span className="text-mint font-bold">{kgHealth.student_mastery}%</span></div>
                            </div>
                          </div>

                          <div className="p-3 bg-black/40 border border-white/5 rounded-2xl space-y-2">
                            <div className="text-[9px] uppercase font-bold text-white flex items-center gap-1">
                              <ShieldAlert className="h-3.5 w-3.5 text-rose-400" /> Gap Audit Metrics
                            </div>
                            <div className="grid grid-cols-3 gap-1.5 text-center text-[10px]">
                              <div className="p-2 rounded bg-black/60 border border-white/5">
                                <div className="text-[8px] text-muted-foreground uppercase">Dead</div>
                                <div className="font-bold text-rose-400 mt-0.5">{kgHealth.dead_nodes_count}</div>
                              </div>
                              <div className="p-2 rounded bg-black/60 border border-white/5">
                                <div className="text-[8px] text-muted-foreground uppercase">Weak</div>
                                <div className="font-bold text-orange-400 mt-0.5">{kgHealth.weak_nodes_count}</div>
                              </div>
                              <div className="p-2 rounded bg-black/60 border border-white/5">
                                <div className="text-[8px] text-muted-foreground uppercase">Overloaded</div>
                                <div className="font-bold text-sky-400 mt-0.5">{kgHealth.overloaded_nodes_count}</div>
                              </div>
                            </div>
                          </div>

                          <div className="p-3 bg-black/40 border border-white/5 rounded-2xl space-y-2">
                            <div className="text-[9px] uppercase font-bold text-white flex items-center gap-1">
                              <Activity className="h-3.5 w-3.5 text-emerald-400" /> Advanced Topology Metrics
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-[9px] text-gray-300">
                              <div>Avg Depth: <span className="text-white font-bold">{kgHealth.average_depth || 0}</span></div>
                              <div>Branching Factor: <span className="text-white font-bold">{kgHealth.average_branching || 0}</span></div>
                              <div className="col-span-2">Longest Chain: <span className="text-white font-bold">{kgHealth.longest_dependency_chain || 0} nodes</span></div>
                              <div className="col-span-2">Weakest Topic: <span className="text-amber-400 font-bold">{kgHealth.weakest_topic || "None"}</span></div>
                              <div className="col-span-2">Most Active: <span className="text-sky-400 font-bold">{kgHealth.most_active_topic || "None"}</span></div>
                              <div className="col-span-2">Biggest Gap: <span className="text-rose-400 font-bold">{kgHealth.biggest_remaining_gap || "None"}</span></div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-6 text-muted-foreground animate-pulse">
                          Calculating health matrix...
                        </div>
                      )}

                      {/* Dead Nodes List (No active questions) (Change 6) */}
                      <div className="border border-white/5 rounded-2xl p-3 bg-black/40 flex-1 flex flex-col gap-2 min-h-[220px]">
                        <div className="text-[9px] uppercase font-bold text-white tracking-wider flex items-center justify-between">
                          <span>Node Sourcing Gaps ({kgDeadNodes.length})</span>
                          <span className="text-[8px] text-rose-400 border border-rose-500/20 bg-rose-500/5 px-1 py-0.5 rounded">Authoring Needed</span>
                        </div>
                        
                        <div className="flex-1 overflow-y-auto pr-1 space-y-1.5 max-h-[250px]">
                          {kgDeadNodes.length === 0 ? (
                            <div className="text-center py-10 text-muted-foreground text-[10px]">
                              All concepts have active question coverage.
                            </div>
                          ) : (
                            kgDeadNodes.map((n) => (
                              <div
                                key={n.id}
                                onClick={() => loadKgNodeDetails(n.id)}
                                className="w-full text-left p-2 rounded-lg bg-black/60 border border-rose-500/10 hover:border-rose-500/30 transition text-[10px] flex items-center justify-between cursor-pointer"
                              >
                                <div className="truncate pr-2 font-mono text-gray-300">
                                  {n.name}
                                </div>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedQuestionId(null);
                                    setActiveMode("designer");
                                    setBpSubject(n.subject);
                                    setBpTopic(n.topic);
                                    setBpSubtopic(n.subtopic);
                                    toast({ title: `Authoring prompt loaded for concept: ${n.name}` });
                                  }}
                                  className="px-1.5 py-0.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-[8px] rounded border border-rose-500/20 font-bold"
                                >
                                  + Create
                                </button>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    </div>

                    {/* MIDDLE PANEL: COLLAPSIBLE NODE EXPLORER & PATH TRAVERSALS (col-span-5) */}
                    <div className="lg:col-span-5 rounded-3xl border border-white/10 p-6 bg-card flex flex-col gap-4 max-h-[750px] overflow-y-auto">
                      <div className="flex items-center justify-between border-b border-white/10 pb-3">
                        <div>
                          <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                            <Layers className="h-4 w-4 text-sky-400" /> Interactive Graph Branch
                          </h3>
                          <p className="text-[9px] text-muted-foreground">
                            Ecosystem hierarchy: click concepts to trace ancestors and prerequisites.
                          </p>
                        </div>
                        
                        <div className="flex gap-2">
                          <button
                            onClick={() => setShowCreateNodeDialog(true)}
                            className="px-2.5 py-1.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 font-bold text-[9px] hover:bg-sky-500/20"
                          >
                            + Add Node
                          </button>
                        </div>
                      </div>

                      {/* Collapsible tree layout list */}
                      <div className="flex-1 overflow-y-auto pr-1 space-y-1.5">
                        {kgLoading ? (
                          <div className="text-center py-20 text-muted-foreground flex flex-col items-center gap-2">
                            <Activity className="h-8 w-8 text-sky-400 animate-spin" />
                            <span>Traversing living Knowledge Graph...</span>
                          </div>
                        ) : kgGraphData.nodes.length === 0 ? (
                          <div className="text-center py-20 text-muted-foreground">
                            No concept nodes found.
                          </div>
                        ) : (
                          <div className="space-y-1">
                            {kgGraphData.nodes
                              .filter((n) => n.type !== "question") // filter out question nodes from main list tree
                              .map((n) => {
                                const isSelected = selectedKgNodeId === n.id;
                                let indentClass = "";
                                let bulletColor = "bg-gray-400";
                                
                                if (n.type === "subject") {
                                  indentClass = "pl-0 font-bold text-white text-[12px]";
                                  bulletColor = "bg-mint";
                                } else if (n.type === "topic") {
                                  indentClass = "pl-3 text-white text-[11px] font-semibold";
                                  bulletColor = "bg-blue-400";
                                } else if (n.type === "subtopic") {
                                  indentClass = "pl-6 text-gray-300";
                                  bulletColor = "bg-sky-400";
                                } else if (n.type === "concept") {
                                  indentClass = "pl-9 text-gray-300";
                                  bulletColor = "bg-purple-400";
                                } else if (n.type === "micro_concept") {
                                  indentClass = "pl-12 text-gray-400";
                                  bulletColor = "bg-indigo-400";
                                } else if (n.type === "learning_objective") {
                                  indentClass = "pl-14 text-gray-400";
                                  bulletColor = "bg-emerald-400";
                                } else if (n.type === "skill") {
                                  indentClass = "pl-16 text-gray-400";
                                  bulletColor = "bg-teal-400";
                                } else if (n.type === "misconception") {
                                  indentClass = "pl-20 text-rose-300 font-medium";
                                  bulletColor = "bg-rose-500 animate-pulse";
                                }

                                return (
                                  <button
                                    key={n.id}
                                    onClick={() => loadKgNodeDetails(n.id)}
                                    className={`w-full text-left py-2 px-3 rounded-lg flex items-center gap-2.5 transition-all ${
                                      isSelected
                                        ? "bg-sky-500/15 border border-sky-400 text-white font-semibold"
                                        : "bg-black/20 border border-transparent hover:bg-white/5 text-gray-300"
                                    } ${indentClass}`}
                                  >
                                    <span className={`h-1.5 w-1.5 rounded-full ${bulletColor}`} />
                                    <div className="flex-1 truncate font-mono">
                                      {n.name}
                                    </div>
                                    <div className="text-[8px] uppercase tracking-wider text-muted-foreground font-semibold">
                                      {n.type}
                                    </div>
                                  </button>
                                );
                              })}
                          </div>
                        )}
                      </div>

                      {/* SVG Connections / Ancestor Path view */}
                      {selectedKgNodeId && kgNodeDetails && (
                        <div className="p-4 border border-white/10 rounded-2xl bg-black/40 space-y-3">
                          <div className="text-[10px] font-bold text-white uppercase tracking-wider">Concept Ancestry Chain</div>
                          <div className="flex flex-wrap items-center gap-1.5 font-mono text-[9px] text-gray-400">
                            {kgNodeDetails.ancestors.slice().reverse().map((anc: any, aIdx: number) => (
                              <React.Fragment key={anc.id}>
                                <span 
                                  onClick={() => loadKgNodeDetails(anc.id)}
                                  className="px-2 py-1 rounded bg-black/60 border border-white/5 hover:border-sky-400 text-white cursor-pointer"
                                >
                                  {anc.name}
                                </span>
                                <span>&gt;</span>
                              </React.Fragment>
                            ))}
                            <span className="px-2 py-1 rounded bg-sky-500/10 border border-sky-400 text-sky-400 font-bold">
                              {kgNodeDetails.node.name}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* RIGHT PANEL: NODE DETAILS, LEARNING PATHS & EDGES (col-span-4) */}
                    <div className="lg:col-span-4 rounded-3xl border border-white/10 p-4 bg-card flex flex-col gap-4 max-h-[750px] overflow-y-auto">
                      {!selectedKgNodeId || !kgNodeDetails ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground py-20 gap-3">
                          <HelpCircle className="h-10 w-10 text-muted-foreground/30" />
                          <div>
                            <div className="font-semibold text-white">Academic Details Node Inspector</div>
                            <div className="text-[10px] mt-1 max-w-[220px]">
                              Select a node from the middle branch tree to inspect prerequisite paths, linked test items, and mastery matrices.
                            </div>
                          </div>
                        </div>
                      ) : (
                        <>
                          <div className="space-y-4">
                            {/* Selected Node Header Card */}
                            <div className="border border-white/5 rounded-2xl p-4 bg-black/60 space-y-2">
                              <div className="flex items-center justify-between">
                                <span className="px-1.5 py-0.5 rounded bg-sky-500/10 border border-sky-500/30 text-sky-400 font-semibold uppercase text-[8px]">
                                  {kgNodeDetails.node.type}
                                </span>
                                <span className="text-[9px] text-muted-foreground">ID: #{kgNodeDetails.node.id}</span>
                              </div>
                              <h4 className="text-sm font-bold text-white font-mono">{kgNodeDetails.node.name}</h4>
                              <p className="text-[10px] text-gray-400 leading-normal">{kgNodeDetails.node.description}</p>
                              
                              <div className="grid grid-cols-3 gap-2 text-center text-[9px] text-gray-300 pt-2 border-t border-white/5">
                                <div>
                                  <div className="text-muted-foreground uppercase text-[8px]">Difficulty</div>
                                  <div className="font-bold text-white mt-0.5">{kgNodeDetails.node.difficulty}%</div>
                                </div>
                                <div>
                                  <div className="text-muted-foreground uppercase text-[8px]">Importance</div>
                                  <div className="font-bold text-white mt-0.5">{kgNodeDetails.node.importance}</div>
                                </div>
                                <div>
                                  <div className="text-muted-foreground uppercase text-[8px]">Mastery</div>
                                  <div className="font-bold text-mint mt-0.5">{Math.round((kgNodeDetails.node.mastery_level || 0) * 100)}%</div>
                                </div>
                              </div>
                            </div>

                            {/* Prerequisite learning path generator (Change 8) */}
                            <div className="border border-white/5 rounded-2xl p-4 bg-black/60 space-y-3">
                              <div className="text-[9px] uppercase text-muted-foreground font-bold tracking-wider">Dynamic Prerequisite Learning Path</div>
                              
                              <div className="space-y-2">
                                {kgLearningPath.length === 0 ? (
                                  <div className="text-[10px] text-gray-400 py-1">
                                    No prerequisites required for this node.
                                  </div>
                                ) : (
                                  kgLearningPath.map((pathNode, pIdx) => {
                                    let statusColor = "text-gray-400 border-white/10";
                                    let statusBg = "bg-white/5";
                                    if (pathNode.status === "Mastered") {
                                      statusColor = "text-emerald-400 border-emerald-500/20";
                                      statusBg = "bg-emerald-500/10";
                                    } else if (pathNode.status === "In Progress") {
                                      statusColor = "text-sky-400 border-sky-500/20";
                                      statusBg = "bg-sky-500/10";
                                    }

                                    return (
                                      <div 
                                        key={pathNode.id}
                                        onClick={() => loadKgNodeDetails(pathNode.id)}
                                        className={`p-2.5 rounded-xl border flex items-center justify-between cursor-pointer hover:scale-[1.01] transition-transform ${statusBg} ${statusColor}`}
                                      >
                                        <div>
                                          <div className="font-mono text-[9px] font-bold text-white">{pathNode.name}</div>
                                          <div className="text-[8px] text-gray-400 uppercase mt-0.5">{pathNode.type} (Imp: {pathNode.importance})</div>
                                        </div>
                                        <div className="text-[9px] font-semibold">
                                          {pathNode.status === "Mastered" ? "✓ Mastered" : pathNode.status === "In Progress" ? "● Active" : "🔒 Locked"}
                                        </div>
                                      </div>
                                    );
                                  })
                                )}
                              </div>
                            </div>

                            {/* Linked Test Items (Change 11 & 12) */}
                            <div className="border border-white/5 rounded-2xl p-4 bg-black/60 space-y-3">
                              <div className="flex items-center justify-between">
                                <span className="text-[9px] uppercase text-muted-foreground font-bold tracking-wider">Linked MCQ Items ({kgNodeDetails.questions.length})</span>
                                <button
                                  onClick={() => setShowLinkQuestionDialog(true)}
                                  className="px-2 py-0.5 bg-sky-500/10 border border-sky-500/20 hover:bg-sky-500/20 text-sky-400 text-[8px] rounded font-bold"
                                >
                                  Link Question
                                </button>
                              </div>

                              <div className="space-y-2">
                                {kgNodeDetails.questions.length === 0 ? (
                                  <div className="text-[10px] text-gray-400 py-1">
                                    No questions currently link to this concept.
                                  </div>
                                ) : (
                                  kgNodeDetails.questions.map((q: any) => (
                                    <div 
                                      key={q.id}
                                      className="p-2.5 rounded-xl bg-black/60 border border-white/5 flex items-center justify-between text-[9px]"
                                    >
                                      <div className="truncate pr-3 text-gray-300 font-mono">
                                        #{q.id}: {q.prompt}
                                      </div>
                                      <div className="flex items-center gap-2 flex-shrink-0">
                                        <span className="font-semibold text-white">QQI: {Math.round(q.qqi_score)}%</span>
                                        <button
                                          onClick={() => {
                                            setSelectedQuestionId(q.id);
                                            loadQuestionDetail(q.id);
                                            setActiveMode("lifecycle");
                                          }}
                                          className="px-1.5 py-0.5 bg-white/5 hover:bg-white/10 text-white rounded border border-white/10"
                                        >
                                          Inspect
                                        </button>
                                      </div>
                                    </div>
                                  ))
                                )}
                              </div>
                            </div>

                          </div>
                        </>
                      )}
                    </div>

                  </div>
                </motion.div>
              )}

              {/* PILOT VALIDATION WORKSPACE (Week 5) */}
              {activeMode === "validation" && (
                <motion.div
                  key="validation"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25 }}
                  className="space-y-8"
                >
                  {/* Header */}
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-xs uppercase tracking-widest text-emerald-400 font-bold flex items-center gap-1.5">
                        <Award className="h-4 w-4" /> Pilot Analytics &amp; Validation
                      </div>
                      <h2 className="mt-1 text-2xl font-bold">Evidence Dashboard</h2>
                      <p className="text-sm text-muted-foreground mt-0.5">
                        Closed-loop validation of AI recommendations, QQI predictions, and classroom telemetry.
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={loadValidationData}
                        className="px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold hover:bg-emerald-500/20 transition-all flex items-center gap-1.5"
                      >
                        <RotateCcw className="h-3.5 w-3.5" /> Refresh
                      </button>
                      <button
                        onClick={async () => {
                          try {
                            if (validationKPIs) {
                              await fetch(`${API}/validation/snapshot`, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                  recommendation_acceptance: validationKPIs.acceptance_rate,
                                  application_rate: validationKPIs.application_rate,
                                  success_rate: validationKPIs.success_rate,
                                  QQI_error: validationKPIs.average_qqi_error,
                                  KG_coverage: validationKPIs.kg_coverage,
                                  report_latency: validationKPIs.average_latency_seconds,
                                  telemetry_events: validationKPIs.telemetry_events,
                                  student_count: pilotSessions.reduce((a: number, s: any) => a + (s.total_students || 0), 0),
                                  teacher_count: new Set(pilotSessions.map((s: any) => s.teacher)).size
                                })
                              });
                              toast({ title: "Validation snapshot saved!" });
                              await loadValidationData();
                            }
                          } catch (err) { console.error(err); }
                        }}
                        className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-xs font-semibold hover:bg-white/10 transition-all flex items-center gap-1.5"
                      >
                        <Save className="h-3.5 w-3.5" /> Save Snapshot
                      </button>
                    </div>
                  </div>

                  {/* KPI Cards */}
                  {validationKPIs && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {[
                        { label: "Acceptance Rate", value: `${validationKPIs.acceptance_rate}%`, color: "emerald", icon: Check },
                        { label: "Application Rate", value: `${validationKPIs.application_rate}%`, color: "sky", icon: TrendingUp },
                        { label: "Success Rate", value: `${validationKPIs.success_rate}%`, color: "violet", icon: Award },
                        { label: "Avg Mastery Gain", value: `+${validationKPIs.average_mastery_gain}%`, color: "amber", icon: Brain },
                        { label: "Avg QQI Error", value: `${validationKPIs.average_qqi_error}%`, color: "rose", icon: AlertTriangle },
                        { label: "KG Coverage", value: `${validationKPIs.kg_coverage}%`, color: "cyan", icon: Layers },
                        { label: "Dead Nodes", value: `${validationKPIs.dead_node_count}`, color: "orange", icon: ShieldAlert },
                        { label: "Avg Latency", value: `${validationKPIs.average_latency_seconds}s`, color: "gray", icon: Clock },
                      ].map((kpi: any, i: number) => (
                        <div key={i} className="bg-card border border-white/10 rounded-2xl p-4 flex flex-col gap-2">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-bold">{kpi.label}</span>
                            <kpi.icon className="h-4 w-4 text-muted-foreground" />
                          </div>
                          <span className="text-2xl font-bold text-white">{kpi.value}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Recommendation Lifecycle Funnel */}
                  {validationKPIs?.funnel && (
                    <div className="bg-card border border-white/10 rounded-2xl p-6">
                      <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-emerald-400" /> Recommendation Lifecycle Funnel
                      </h3>
                      <div className="flex items-end gap-4 overflow-x-auto pb-2">
                        {[
                          { label: "Generated", key: "generated" },
                          { label: "Viewed", key: "viewed" },
                          { label: "Accepted", key: "accepted" },
                          { label: "Applied", key: "applied" },
                          { label: "Completed", key: "completed" },
                          { label: "Verified", key: "verified" },
                        ].map((stage: any, i: number) => {
                          const total = validationKPIs.funnel.generated || 1;
                          const val = validationKPIs.funnel[stage.key] || 0;
                          const pct = Math.round((val / total) * 100);
                          const barH = Math.max(Math.round(pct * 1.2), 8);
                          return (
                            <div key={i} className="flex flex-col items-center gap-2 min-w-[70px] flex-1">
                              <span className="text-sm font-bold text-white">{val}</span>
                              <div className="w-full rounded-t-lg bg-emerald-500/20 border border-emerald-500/30 transition-all" style={{ height: `${barH}px` }} />
                              <span className="text-[9px] text-muted-foreground text-center">{stage.label}</span>
                              <span className="text-[9px] text-emerald-400 font-bold">{pct}%</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* QQI Validation Matrix */}
                  {validationQQI.length > 0 && (
                    <div className="bg-card border border-white/10 rounded-2xl p-6">
                      <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                        <BarChart2 className="h-4 w-4 text-sky-400" /> QQI Validation Matrix
                      </h3>
                      <div className="overflow-x-auto">
                        <table className="w-full text-[11px]">
                          <thead>
                            <tr className="border-b border-white/10">
                              <th className="text-left py-2 pr-4 text-muted-foreground font-semibold">Question</th>
                              <th className="text-center py-2 px-3 text-muted-foreground font-semibold">Predicted QQI</th>
                              <th className="text-center py-2 px-3 text-muted-foreground font-semibold">Teacher Rating</th>
                              <th className="text-center py-2 px-3 text-muted-foreground font-semibold">Student Pass%</th>
                              <th className="text-center py-2 px-3 text-muted-foreground font-semibold">Telemetry Conf.</th>
                              <th className="text-center py-2 px-3 text-muted-foreground font-semibold">QQI Error</th>
                            </tr>
                          </thead>
                          <tbody>
                            {validationQQI.map((q: any) => (
                              <tr key={q.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                <td className="py-2 pr-4 text-white max-w-[200px] truncate" title={q.prompt}>{q.prompt}</td>
                                <td className="py-2 px-3 text-center font-bold text-sky-400">{q.predicted_qqi}</td>
                                <td className="py-2 px-3 text-center font-bold text-emerald-400">{q.teacher_rating}%</td>
                                <td className="py-2 px-3 text-center font-bold text-violet-400">{q.student_performance}%</td>
                                <td className="py-2 px-3 text-center text-amber-400">{q.telemetry_quality}</td>
                                <td className={`py-2 px-3 text-center font-bold ${q.final_qqi_error > 15 ? "text-rose-400" : q.final_qqi_error > 8 ? "text-amber-400" : "text-emerald-400"}`}>
                                  {q.final_qqi_error}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Telemetry Validation */}
                  {validationTelemetry && (
                    <div className="bg-card border border-white/10 rounded-2xl p-6">
                      <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                        <Activity className="h-4 w-4 text-violet-400" /> Classroom Telemetry Validation
                      </h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                          { label: "Response Time", data: validationTelemetry.response_time, unit: "s" },
                          { label: "Hover Count", data: validationTelemetry.hover_count, unit: "" },
                          { label: "Idle Time", data: validationTelemetry.idle_time, unit: "s" },
                          { label: "Backspaces", data: validationTelemetry.backspaces, unit: "" },
                        ].map((metric: any, i: number) => (
                          <div key={i} className="bg-white/5 rounded-xl p-3 space-y-2">
                            <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-bold">{metric.label}</span>
                            <div className="space-y-1">
                              <div className="flex justify-between text-xs"><span className="text-muted-foreground">Avg</span><span className="font-bold text-white">{metric.data?.avg}{metric.unit}</span></div>
                              <div className="flex justify-between text-xs"><span className="text-muted-foreground">Min</span><span className="text-white">{metric.data?.min}{metric.unit}</span></div>
                              <div className="flex justify-between text-xs"><span className="text-muted-foreground">Max</span><span className="text-white">{metric.data?.max}{metric.unit}</span></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Pilot Sessions Tracker */}
                  <div className="bg-card border border-white/10 rounded-2xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <Users className="h-4 w-4 text-amber-400" /> Classroom Pilot Sessions
                      </h3>
                      <button
                        onClick={() => setShowCreateSessionDialog(true)}
                        className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold hover:bg-emerald-500/20 transition-all flex items-center gap-1"
                      >
                        <Plus className="h-3 w-3" /> New Session
                      </button>
                    </div>
                    {pilotSessions.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground text-sm">No pilot sessions yet. Enable SIH Demo Mode or create a new session.</div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-[11px]">
                          <thead>
                            <tr className="border-b border-white/10">
                              <th className="text-left py-2 pr-3 text-muted-foreground font-semibold">Classroom</th>
                              <th className="text-left py-2 px-3 text-muted-foreground font-semibold">Teacher</th>
                              <th className="text-center py-2 px-3 text-muted-foreground font-semibold">Subject</th>
                              <th className="text-center py-2 px-3 text-muted-foreground font-semibold">Students</th>
                              <th className="text-center py-2 px-3 text-muted-foreground font-semibold">Attempts</th>
                              <th className="text-center py-2 px-3 text-muted-foreground font-semibold">Completion</th>
                              <th className="text-center py-2 px-3 text-muted-foreground font-semibold">Latency</th>
                              <th className="text-center py-2 px-3 text-muted-foreground font-semibold">Device</th>
                            </tr>
                          </thead>
                          <tbody>
                            {pilotSessions.map((s: any) => (
                              <tr key={s.session_id} className="border-b border-white/5 hover:bg-white/5">
                                <td className="py-2 pr-3 font-bold text-white">{s.classroom_id}</td>
                                <td className="py-2 px-3 text-muted-foreground">{s.teacher}</td>
                                <td className="py-2 px-3 text-center"><span className="px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-400 text-[10px] font-bold uppercase">{s.subject}</span></td>
                                <td className="py-2 px-3 text-center text-white">{s.total_students}</td>
                                <td className="py-2 px-3 text-center text-white">{s.total_attempts}</td>
                                <td className="py-2 px-3 text-center font-bold text-white">{s.completion_rate}%</td>
                                <td className="py-2 px-3 text-center font-bold text-white">{s.average_latency}s</td>
                                <td className="py-2 px-3 text-center text-muted-foreground capitalize">{s.device_type}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>

                  {/* Validation Trend Snapshots */}
                  {validationSnapshots.length > 0 && (
                    <div className="bg-card border border-white/10 rounded-2xl p-6">
                      <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-cyan-400" /> Validation Trend Over Time
                      </h3>
                      <div className="overflow-x-auto">
                        <table className="w-full text-[11px]">
                          <thead>
                            <tr className="border-b border-white/10">
                              <th className="text-left py-2 pr-3 text-muted-foreground font-semibold">Snapshot Date</th>
                              <th className="text-center py-2 px-2 text-muted-foreground font-semibold">Acceptance</th>
                              <th className="text-center py-2 px-2 text-muted-foreground font-semibold">Application</th>
                              <th className="text-center py-2 px-2 text-muted-foreground font-semibold">Success</th>
                              <th className="text-center py-2 px-2 text-muted-foreground font-semibold">QQI Error</th>
                              <th className="text-center py-2 px-2 text-muted-foreground font-semibold">KG Cover</th>
                              <th className="text-center py-2 px-2 text-muted-foreground font-semibold">Students</th>
                            </tr>
                          </thead>
                          <tbody>
                            {validationSnapshots.map((sn: any, i: number) => (
                              <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                                <td className="py-2 pr-3 text-muted-foreground">{new Date(sn.timestamp).toLocaleDateString()}</td>
                                <td className="py-2 px-2 text-center font-bold text-emerald-400">{sn.recommendation_acceptance}%</td>
                                <td className="py-2 px-2 text-center font-bold text-sky-400">{sn.application_rate}%</td>
                                <td className="py-2 px-2 text-center font-bold text-violet-400">{sn.success_rate}%</td>
                                <td className="py-2 px-2 text-center font-bold text-rose-400">{sn.QQI_error}%</td>
                                <td className="py-2 px-2 text-center font-bold text-cyan-400">{sn.KG_coverage}%</td>
                                <td className="py-2 px-2 text-center text-white">{sn.student_count}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

            </AnimatePresence>
          </div>
        </div>

        {/* CREATE PILOT SESSION DIALOG */}
        {showCreateSessionDialog && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div className="bg-card border border-white/10 rounded-3xl p-6 w-full max-w-md space-y-4 shadow-xl">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                  <Users className="h-4 w-4 text-emerald-400" /> Start Pilot Session
                </h3>
                <p className="text-[10px] text-muted-foreground mt-0.5">Record a new classroom pilot session for validation tracking.</p>
              </div>
              <div className="space-y-3 text-[11px]">
                {[
                  { label: "Classroom ID", value: newSessionClassroomId, set: setNewSessionClassroomId, ph: "e.g. CSE-A-2026" },
                  { label: "Teacher Name", value: newSessionTeacher, set: setNewSessionTeacher, ph: "e.g. Dr. Sharma" },
                  { label: "Subject", value: newSessionSubject, set: setNewSessionSubject, ph: "e.g. dsa" },
                  { label: "Topic", value: newSessionTopic, set: setNewSessionTopic, ph: "e.g. Arrays" },
                ].map((field: any) => (
                  <div key={field.label} className="space-y-1">
                    <label className="text-[9px] uppercase font-bold text-muted-foreground">{field.label}</label>
                    <input type="text" value={field.value} onChange={(e) => field.set(e.target.value)} placeholder={field.ph} className="w-full p-2.5 rounded-xl bg-black border border-white/10 text-white text-xs" />
                  </div>
                ))}
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[9px] uppercase font-bold text-muted-foreground">Device Type</label>
                    <select value={newSessionDevice} onChange={(e) => setNewSessionDevice(e.target.value)} className="w-full p-2 bg-black border border-white/10 text-white rounded-lg">
                      <option value="desktop">Desktop</option><option value="laptop">Laptop</option><option value="mobile">Mobile</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[9px] uppercase font-bold text-muted-foreground">Network Quality</label>
                    <select value={newSessionNetwork} onChange={(e) => setNewSessionNetwork(e.target.value)} className="w-full p-2 bg-black border border-white/10 text-white rounded-lg">
                      <option>Excellent</option><option>Good</option><option>Fair</option><option>Poor</option>
                    </select>
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-[9px] uppercase font-bold text-muted-foreground">Session Duration (minutes)</label>
                  <input type="number" value={newSessionDuration} onChange={(e) => setNewSessionDuration(e.target.value)} className="w-full p-2.5 rounded-xl bg-black border border-white/10 text-white text-xs" />
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button onClick={() => setShowCreateSessionDialog(false)} className="flex-1 py-2.5 rounded-xl border border-white/10 text-muted-foreground text-xs hover:bg-white/5 transition-all">Cancel</button>
                <button onClick={handleCreatePilotSession} className="flex-1 py-2.5 rounded-xl bg-emerald-500 text-black text-xs font-bold hover:bg-emerald-400 transition-all">Start Session</button>
              </div>
            </div>
          </div>
        )}

        {/* KNOWLEDGE GRAPH DIALOGS */}
        {showCreateNodeDialog && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div className="bg-card border border-white/10 rounded-3xl p-6 w-full max-w-md space-y-4 shadow-xl">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                  <Plus className="h-4 w-4 text-sky-400" /> Add Knowledge Node
                </h3>
                <p className="text-[10px] text-muted-foreground mt-0.5">
                  Insert a new taxonomic element or prerequisite dependency.
                </p>
              </div>

              <div className="space-y-3 text-[11px]">
                <div className="space-y-1">
                  <label className="text-[9px] uppercase font-bold text-muted-foreground">Node Name</label>
                  <input
                    type="text"
                    value={newNodeName}
                    onChange={(e) => setNewNodeName(e.target.value)}
                    placeholder="e.g. array_search"
                    className="w-full p-2.5 rounded-xl bg-black border border-white/10 text-white text-xs"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[9px] uppercase font-bold text-muted-foreground">Type</label>
                    <select
                      value={newNodeType}
                      onChange={(e) => setNewNodeType(e.target.value)}
                      className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                    >
                      <option value="topic">Topic</option>
                      <option value="subtopic">Subtopic</option>
                      <option value="concept">Concept</option>
                      <option value="micro_concept">Micro Concept</option>
                      <option value="learning_objective">Learning Objective</option>
                      <option value="skill">Skill</option>
                      <option value="misconception">Misconception</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[9px] uppercase font-bold text-muted-foreground">Topic</label>
                    <input
                      type="text"
                      value={newNodeTopic}
                      onChange={(e) => setNewNodeTopic(e.target.value)}
                      placeholder="e.g. arrays"
                      className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-[9px] uppercase font-bold text-muted-foreground">Subtopic</label>
                  <input
                    type="text"
                    value={newNodeSubtopic}
                    onChange={(e) => setNewNodeSubtopic(e.target.value)}
                    placeholder="e.g. searching"
                    className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[9px] uppercase font-bold text-muted-foreground">Description</label>
                  <textarea
                    rows={2}
                    value={newNodeDesc}
                    onChange={(e) => setNewNodeDesc(e.target.value)}
                    placeholder="Provide pedagogical description..."
                    className="w-full p-2 bg-black border border-white/10 text-white rounded-lg text-xs"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[9px] uppercase font-bold text-muted-foreground">Parent Node</label>
                    <select
                      value={newNodeParentId}
                      onChange={(e) => setNewNodeParentId(e.target.value)}
                      className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                    >
                      <option value="">None</option>
                      {kgGraphData.nodes
                        .filter((n) => n.type !== "question")
                        .map((n) => (
                          <option key={n.id} value={n.id}>{n.name} ({n.type})</option>
                        ))}
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[9px] uppercase font-bold text-muted-foreground">Prerequisite Node</label>
                    <select
                      value={newNodePrereqId}
                      onChange={(e) => setNewNodePrereqId(e.target.value)}
                      className="w-full p-2 bg-black border border-white/10 text-white rounded-lg"
                    >
                      <option value="">None</option>
                      {kgGraphData.nodes
                        .filter((n) => n.type !== "question")
                        .map((n) => (
                          <option key={n.id} value={n.id}>{n.name} ({n.type})</option>
                        ))}
                    </select>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 justify-end pt-3 text-xs">
                <button
                  onClick={() => setShowCreateNodeDialog(false)}
                  className="px-4 py-2 border border-white/10 rounded-xl text-gray-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateKgNode}
                  className="px-4 py-2 bg-sky-500 text-black font-bold rounded-xl hover:bg-sky-600"
                >
                  Create Node
                </button>
              </div>
            </div>
          </div>
        )}

        {showLinkQuestionDialog && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div className="bg-card border border-white/10 rounded-3xl p-6 w-full max-w-sm space-y-4 shadow-xl">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                  <Plus className="h-4 w-4 text-sky-400" /> Link Question to Concept
                </h3>
                <p className="text-[10px] text-muted-foreground mt-0.5">
                  Link an existing assessment question to the selected concept.
                </p>
              </div>

              <div className="space-y-3 text-[11px]">
                <div className="space-y-1">
                  <label className="text-[9px] uppercase font-bold text-muted-foreground">Question ID</label>
                  <input
                    type="number"
                    value={linkQuestionId}
                    onChange={(e) => setLinkQuestionId(e.target.value)}
                    placeholder="e.g. 1"
                    className="w-full p-2.5 bg-black border border-white/10 text-white rounded-lg"
                  />
                </div>
              </div>

              <div className="flex gap-2 justify-end pt-3 text-xs">
                <button
                  onClick={() => setShowLinkQuestionDialog(false)}
                  className="px-4 py-2 border border-white/10 rounded-xl text-gray-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  onClick={handleLinkQuestionToNode}
                  className="px-4 py-2 bg-sky-500 text-black font-bold rounded-xl hover:bg-sky-600"
                >
                  Link MCQ
                </button>
              </div>
            </div>
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

        {/* Join room card */}
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

                  <div className="mt-2 inline-flex rounded-full border border-mint/20 px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-mint">
                    {r.scores.conceptual >= 60
                      ? "High Concept"
                      : r.scores.fakeUnderstanding >= 40
                      ? "Surface Familiarity"
                      : "Mixed Signals"}
                  </div>

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
