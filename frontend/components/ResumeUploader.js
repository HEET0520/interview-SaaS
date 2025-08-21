// frontend/components/ResumeUploader.js
import { useState } from "react";

export default function ResumeUploader({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    // The backend expects X-Clerk-User-Id header (frontend will inject it).
    const res = await fetch(process.env.NEXT_PUBLIC_API_URL + "/upload_resume", {
      method: "POST",
      body: form,
      // Headers set by browser; Clerk id header set by wrapper in page.
    });
    const j = await res.json();
    setUploading(false);
    if (j?.resume) onUploaded(j.resume);
  }

  return (
    <div className="card">
      <label className="block text-sm text-gray-300">Upload Resume (PDF)</label>
      <input type="file" accept="application/pdf" onChange={(e)=>setFile(e.target.files?.[0])} className="mt-2" />
      <div className="mt-3">
        <button onClick={handleUpload} className="px-4 py-2 rounded bg-indigo-600">{uploading ? "Uploading..." : "Upload"}</button>
      </div>
    </div>
  )
}
