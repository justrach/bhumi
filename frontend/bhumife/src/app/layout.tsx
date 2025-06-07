import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Bhumi भूमि - Blazing-Fast AI Inference Client",
  description: "Bhumi is the blazing-fast AI inference client for Python. Built with Rust for unmatched performance, supporting OpenAI, Anthropic, Gemini, Groq, and more. Get 3x faster inference with 60% less memory usage.",
  keywords: [
    "AI inference",
    "Python AI client", 
    "Rust AI library",
    "OpenAI client",
    "Anthropic client",
    "fast AI inference",
    "machine learning",
    "artificial intelligence",
    "Bhumi",
    "भूमि"
  ],
  authors: [{ name: "Trilok.ai", url: "https://trilok.ai" }],
  creator: "Trilok.ai",
  publisher: "Trilok.ai",
  openGraph: {
    type: "website",
    title: "Bhumi भूमि - Blazing-Fast AI Inference Client",
    description: "The blazing-fast AI inference client for Python. Built with Rust for 3x faster performance. Unified interface for OpenAI, Anthropic, Gemini, Groq, and more.",
    url: "https://bhumi.trilok.ai",
    siteName: "Bhumi",
    images: [
      {
        url: '/api/og',
        width: 1200,
        height: 630,
        alt: 'Bhumi भूमि - Blazing-Fast AI Inference Client for Python',
      },
    ],
    locale: "en_US",
  },
  twitter: {
    card: 'summary_large_image',
    title: "Bhumi भूमि - Blazing-Fast AI Inference Client",
    description: "The blazing-fast AI inference client for Python. Built with Rust for 3x faster performance.",
    images: ['/api/og'],
    creator: "@trilok_ai",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: undefined, // Add Google Search Console verification if needed
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <meta name="theme-color" content="hsl(15, 85%, 70%)" />
        <meta name="msapplication-TileColor" content="hsl(15, 85%, 70%)" />
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/manifest.json" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-white`}
      >
        {children}
      </body>
    </html>
  );
}
