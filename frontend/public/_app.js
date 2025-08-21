// frontend/pages/_app.js
import '../styles/globals.css'
import { ClerkProvider, RedirectToSignIn, SignedIn, SignedOut } from '@clerk/nextjs'
import { useRouter } from 'next/router'

function MyApp({ Component, pageProps }) {
  const router = useRouter()
  return (
    <ClerkProvider
      publishableKey={process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
      frontendApi={process.env.NEXT_PUBLIC_CLERK_FRONTEND_API}
    >
      <div className="min-h-screen p-6">
        <Component {...pageProps} />
      </div>
    </ClerkProvider>
  )
}

export default MyApp
