// frontend/pages/dashboard.js
import useSWR from "swr";
import { useUser } from "@clerk/nextjs";
import Link from "next/link";

const fetcher = (url, headers) => fetch(url, { headers }).then(r => r.json());

export default function Dashboard() {
  const { user } = useUser();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL + "/interviews/history";

  const { data, error } = useSWR(user ? [apiUrl, { "X-Clerk-User-Id": user?.id }] : null, () =>
    fetch(apiUrl, {
      headers: { "X-Clerk-User-Id": user?.id }
    }).then(r => r.json())
  );

  return (
    <div className="max-w-4xl mx-auto py-12">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      <div className="mb-6">
        <Link href="/interview/new"><a className="px-4 py-2 rounded bg-gradient-to-r from-violet-500 to-cyan-400">New Interview</a></Link>
      </div>

      <div className="grid gap-4">
        {data?.interviews?.length === 0 && <p className="text-gray-300">No interviews yet.</p>}
        {data?.interviews?.map(i => (
          <div key={i.id} className="card flex justify-between items-center">
            <div>
              <div className="font-semibold">{i.role} <span className="text-sm text-gray-400">({i.mode})</span></div>
              <div className="text-sm text-gray-400">Created: {new Date(i.created_at).toLocaleString()}</div>
            </div>
            <div>
              <Link href={`/interview/${i.id}`}><a className="px-3 py-2 rounded bg-white/5">Open</a></Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
