import { FeatureCards } from "@/components/feature-cards"
import { NavBar } from "@/components/nav-bar"
import { PerformanceChart } from "@/components/performance-chart"
import { Button } from "@/components/ui/button"
import { Zap, Brain } from "lucide-react"
import Image from "next/image"
export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-4 py-16">
        <NavBar />

        <div className="text-center max-w-4xl mx-auto">
          <Image 
            src="https://images.bhumi.trilok.ai/bhumi_logo.png" 
            alt="Bhumi Logo" 
            className="mx-auto mb-8 w-48 h-48 rounded-xl"
          />
          <h1 className="text-7xl font-extrabold mb-4 tracking-tight">
            Meet{" "}
            <span 
              className="font-black"
              style={{ color: "hsl(15, 85%, 70%)" }}
            >
              Bhumi
            </span>
          </h1>
          <div 
            className="text-4xl font-bold mb-8"
            style={{ color: "hsl(15, 85%, 70%)" }}
          >
            भूमि
          </div>
          <p className="text-2xl text-gray-600 mb-8 leading-relaxed">
            The <span className="font-semibold">fastest</span> and most <span className="font-semibold">efficient</span> AI inference client
            for Python. Built with <span style={{ color: "hsl(15, 85%, 70%)" }}>Rust</span> for unmatched performance, 
            outperforming pure Python implementations through native multiprocessing. Supporting OpenAI, Anthropic, and Gemini.
          </p>
          <div className="flex gap-4 justify-center mb-16">
            <Button size="lg" className="bg-[hsl(15,85%,70%)] hover:bg-[hsl(15,85%,65%)] text-white font-semibold shadow-md">
              <Zap className="mr-2 h-5 w-5" />
              Get Started
            </Button>
            <Button size="lg" variant="outline">
              <Brain className="mr-2 h-5 w-5" />
              View Benchmarks
            </Button>
          </div>
        </div>

        <div className="max-w-4xl mx-auto mb-16">
          <PerformanceChart />
        </div>

        <FeatureCards />
      </div>
    </div>
  )
}