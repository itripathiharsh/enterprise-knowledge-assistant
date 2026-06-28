export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const THINKING_STEPS: { key: string; label: string; duration: number }[] = [
  { key: "understanding", label: "Understanding your request...", duration: 600 },
  { key: "planning", label: "Planning execution...", duration: 500 },
  { key: "searching", label: "Searching knowledge base...", duration: 800 },
  { key: "reading", label: "Reading documents...", duration: 700 },
  { key: "gathering", label: "Gathering relevant context...", duration: 600 },
  { key: "synthesizing", label: "Synthesizing information...", duration: 500 },
  { key: "validating", label: "Validating answer...", duration: 400 },
  { key: "generating", label: "Generating final response...", duration: 0 },
];

export const LOW_CONFIDENCE_THRESHOLD = 0.3;
