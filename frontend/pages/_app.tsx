import '../styles/globals.css'
import type { AppProps } from 'next/app'
import 'katex/dist/katex.min.css'

export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />
} 