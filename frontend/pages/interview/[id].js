// frontend/pages/interview/[id].js
import { useRouter } from "next/router";
import { useEffect, useRef, useState } from "react";
import { useUser } from "@clerk/nextjs";

export default function InterviewSession() {
  const router = useRouter();
  const { id } = router.query;
  const { user } = useUser();
  const [messages, setMessages] = useState([]); // {from:'ai'|'user'|'info', text:''}
  const [input, setInput] = useState("");
  const wsRef = useRef(null);

  useEffect(() => {
    if (!id || !user) return;
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const backendUrl = process.env.NEXT_PUBLIC_API_WS || process.env.NEXT_PUBLIC_API_URL;
    const wsUrl = (backendUrl || "http://localhost:8000").replace(/^http/, wsProtocol) + `/ws/interview/${id}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.onopen = () => {
      console.log("ws open");
    };
    ws.onmessage = (ev) => {
      let d = {}
      try { d = JSON.parse(ev.data) } catch(e){}
      if (d.type === "question") {
        // append question text
        setMessages(prev => [...prev, {from: "ai", text: d.text}])
      } else if (d.type === "question_end") {
        // maybe mark end
      } else if (d.type === "info") {
        setMessages(prev=>[...prev, {from:'info', text:d.text}])
      } else if (d.type === "end") {
        setMessages(prev=>[...prev, {from:'info', text:"Analysis received"}])
        setMessages(prev=>[...prev, {from:'analysis', text: JSON.stringify(d.analysis, null, 2)}])
      } else {
        setMessages(prev => [...prev, {from: "ai", text: JSON.stringify(d)}])
      }
    }
    ws.onclose = ()=> console.log("ws closed")
    ws.onerror = (e)=> console.error("ws error", e)

    // set header for clerk — cannot set custom headers for WebSocket handshakes easily in browser.
    // So we rely on the backend accepting X-Clerk-User-Id as query param or subprotocol in production.
    // For local demo we assume the interview is already created for this user.
    return ()=> ws.close()
  }, [id, user])

  const sendAnswer = () => {
    if (!input.trim()) return;
    // append locally
    setMessages(prev => [...prev, {from:'user', text: input}])
    // send via websocket
    try {
      wsRef.current.send(JSON.stringify({ type: "answer", text: input }));
    } catch (e) {
      alert("WebSocket not connected")
    }
    setInput("");
  }

  const endInterview = () => {
    try {
      wsRef.current.send(JSON.stringify({ type: "end" }));
    } catch (e) {
      alert("WebSocket not connected")
    }
  }

  return (
    <div className="max-w-3xl mx-auto py-8">
      <h2 className="text-2xl font-bold mb-4">Interview Session</h2>
      <div className="card mb-4 min-h-[320px] overflow-auto">
        {messages.map((m, idx) => (
          <div key={idx} className={`mb-3 ${m.from === "user" ? "text-right" : ""}`}>
            <div className={`${m.from === "ai" ? "inline-block bg-white/5 p-3 rounded" : m.from === "user" ? "inline-block bg-gradient-to-r from-violet-600 to-cyan-400 text-black p-3 rounded" : "text-sm text-gray-400"}`}>
              <pre style={{whiteSpace: "pre-wrap", margin: 0}}>{m.text}</pre>
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <input value={input} onChange={(e)=>setInput(e.target.value)} placeholder="Type your answer..." className="flex-1 p-3 rounded bg-transparent border border-white/10"/>
        <button onClick={sendAnswer} className="px-4 py-2 rounded bg-indigo-600">Send</button>
        <button onClick={endInterview} className="px-4 py-2 rounded bg-red-600">Finish</button>
      </div>
    </div>
  )
}
