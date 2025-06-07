import { FeatureCards } from "@/components/feature-cards"
import { NavBar } from "@/components/nav-bar"
import { PerformanceChart } from "@/components/performance-chart"
import { Button } from "@/components/ui/button"
import { CodeBlock } from "@/components/ui/code-block"
import { Brain } from "lucide-react"
import Image from "next/image"
import { CopyInstall } from "@/components/copy-install"
import { InteractiveButtons } from "@/components/home/interactive-buttons"
import { Card } from "@/components/ui/card"

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-4 pt-4 py-10">
        <NavBar />

        <div className="text-center max-w-4xl mx-auto">
          <div className="mb-8">
            <a 
              href="https://trilok.ai" 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors text-gray-700 text-sm"
            >
              <span className="mr-2">Powered by</span>
              <span className="font-semibold text-[hsl(15,85%,50%)]">Trilok.ai</span>
              <span className="ml-2">→</span>
            </a>
          </div>
          <Image 
            width={192}
            height={192}
            src="https://images.bhumi.trilqwaok.ai/bhumi_logo.png" 
            alt="Bhumi Logo - A stylized orange and white design representing speed and intelligence" 
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
            outperforming pure Python implementations through native multiprocessing. Supporting OpenAI, Anthropic, Gemini, DeepSeek, Groq, and more.
          </p>

          {/* Code Example */}
          <div className="mt-8 max-w-2xl mx-auto">
            <Card className="p-6">
              <h3 className="text-xl font-medium mb-4">Quick Start</h3>
              <CodeBlock
                language="python"
                code={`from bhumi.base_client import BaseLLMClient, LLMConfig
import asyncio

async def main():
    config = LLMConfig(
        api_key="your-api-key",
        model="openai/gpt-4o"
    )
    
    client = BaseLLMClient(config)
    response = await client.completion([
        {"role": "user", "content": "Hello!"}
    ])
    
    print(response['text'])

if __name__ == "__main__":
    asyncio.run(main())`}
              />
            </Card>
          </div>

          {/* Call-to-Action */}
          <div className="flex gap-4 justify-center mb-16 mt-8">
            <CopyInstall />
            <InteractiveButtons />
          </div>
        </div>

        {/* Performance Chart */}
        <div className="max-w-4xl mx-auto mb-16">
          <PerformanceChart />
        </div>

        <FeatureCards />
      </div>

      {/* Footer */}
      <footer className="text-center text-gray-600 py-8">
        <p>Built with ❤️ by <a href="https://trilok.ai" className="text-[hsl(15,85%,70%)] hover:underline">Trilok.ai</a></p>
      </footer>
    </div>
  )
}