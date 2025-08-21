// frontend/components/InterviewTypeSelector.js
import { useState } from "react";

export default function InterviewTypeSelector({ onCreate }) {
  const [mode, setMode] = useState("role");
  const [role, setRole] = useState("Frontend Developer");
  const [difficulty, setDifficulty] = useState("medium");
  const [experience, setExperience] = useState("0-1 years");
  const [resumeId, setResumeId] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    await onCreate({ mode, role, difficulty, experience_level: experience, resume_id: resumeId });
  };

  return (
    <form onSubmit={handleSubmit} className="card max-w-2xl mx-auto">
      <div className="mb-4">
        <label className="block text-sm text-gray-300">Mode</label>
        <div className="mt-2 flex gap-2">
          <button type="button" onClick={() => setMode("role")} className={`px-4 py-2 rounded ${mode==="role" ? "bg-indigo-600 text-white" : "bg-white/5 text-gray-200"}`}>Role-based</button>
          <button type="button" onClick={() => setMode("resume")} className={`px-4 py-2 rounded ${mode==="resume" ? "bg-indigo-600 text-white" : "bg-white/5 text-gray-200"}`}>Resume-based</button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm text-gray-300">Role</label>
          <input value={role} onChange={(e)=>setRole(e.target.value)} className="mt-2 w-full rounded p-2 bg-transparent border border-white/10" />
        </div>
        <div>
          <label className="block text-sm text-gray-300">Experience</label>
          <input value={experience} onChange={(e)=>setExperience(e.target.value)} className="mt-2 w-full rounded p-2 bg-transparent border border-white/10" />
        </div>
        <div>
          <label className="block text-sm text-gray-300">Difficulty</label>
          <select value={difficulty} onChange={(e)=>setDifficulty(e.target.value)} className="mt-2 w-full rounded p-2 bg-transparent border border-white/10">
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>
        <div>
          <label className="block text-sm text-gray-300">Resume (optional)</label>
          <input type="text" placeholder="Resume id (optional)" value={resumeId || ""} onChange={(e)=>setResumeId(e.target.value)} className="mt-2 w-full rounded p-2 bg-transparent border border-white/10" />
        </div>
      </div>

      <div className="mt-6 flex justify-end">
        <button className="px-5 py-2 rounded bg-gradient-to-r from-violet-500 to-cyan-400 font-semibold">Start Interview</button>
      </div>
    </form>
  )
}
