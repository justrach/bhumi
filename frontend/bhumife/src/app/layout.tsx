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
  title: "Bhumi - Fast AI Inference",
  description: "Bhumi is the fastest and most efficient AI inference client for Python. Built with Rust for blazing speed, it outperforms pure Python implementations with native multiprocessing. Works seamlessly with OpenAI, Anthropic, Gemini, DeepSeek, Groq, and more.",
  openGraph: {
    title: "Bhumi - Fast AI Inference",
    description: "The fastest and most efficient AI inference client for Python",
    images: [
      {
        url: '/api/og',
        width: 1200,
        height: 630,
        alt: 'Bhumi - Fast AI Inference',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: "Bhumi - Fast AI Inference",
    description: "The fastest and most efficient AI inference client for Python",
    images: ['/api/og'],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
