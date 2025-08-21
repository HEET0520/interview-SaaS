// frontend/pages/interview/new.js
import { useRouter } from "next/router";
import { useUser } from "@clerk/nextjs";
import InterviewTypeSelector from "../../components/InterviewTypeSelector";
import ResumeUploader from "../../components/ResumeUploader";
import { useState } from "react";

export default function NewInterview() {
  const router = useRouter()
  const { user, isSignedIn } = useUser()
  const [resume, setResume] = useState(null)

  async function createInterview(payload) {
    // Add clerk header
    const headers = {
      "Content-Type": "application/json",
      "X-Clerk-User-Id": user?.id || ""
    }
    const res = await fetch(process.env.NEXT_PUBLIC_API_URL + "/interviews/new", {
      method: "POST",
      headers,
      body: JSON.stringify(payload)
    })
    const j = await res.json()
    if (j?.interview?.id) {
      router.push(`/interview/${j.interview.id}`)
    } else {
      alert("Failed to create interview")
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-12">
      <h2 className="text-2xl font-bold mb-6">New Interview</h2>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <InterviewTypeSelector onCreate={createInterview} />
        </div>

        <div>
          <ResumeUploader onUploaded={(r)=> {
            setResume(r)
            alert("Resume uploaded: " + r.id)
          }} />
          <div className="mt-6 card">
            <h3 className="font-semibold">Uploaded resume id</h3>
            <p className="text-sm text-gray-300">{resume?.id || "No resume uploaded yet."}</p>
            <p className="mt-3 text-xs text-gray-400">If you upload a resume, copy the resume id into "Resume (optional)" field in the form.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
