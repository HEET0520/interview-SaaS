// frontend/pages/index.js
import Link from 'next/link'
import { SignInButton, SignUpButton, useUser, SignedIn, SignedOut } from "@clerk/nextjs";

export default function Home() {
  const heroStyle = "max-w-4xl mx-auto py-20 text-center";

  return (
    <main className="container mx-auto">
      <div className={heroStyle}>
        <h1 className="text-5xl font-bold mb-4" style={{color: "white"}}>
          Practice interviews, powered by AI — real-time & tailored
        </h1>
        <p className="mb-8 text-lg text-gray-300">
          Role-based or resume-based interviews with streaming questions, instant feedback, and improvement plans.
        </p>
        <div className="flex justify-center gap-4">
          <SignInButton>
            <button className="px-6 py-3 rounded-md font-semibold bg-white text-black shadow">Sign in</button>
          </SignInButton>
          <Link href="/interview/new">
            <a className="px-6 py-3 rounded-md font-semibold border border-white text-white">Start practice</a>
          </Link>
        </div>
        <div className="mt-12">
          <Link href="/dashboard">
            <a className="text-sm text-gray-300">My Dashboard →</a>
          </Link>
        </div>
      </div>
    </main>
  )
}
// frontend/public/index.js