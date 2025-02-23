import { FeatureCards } from "@/components/feature-cards"
import { NavBar } from "@/components/nav-bar"
import { PerformanceChart } from "@/components/performance-chart"
import { Card } from "@/components/ui/card"
import { CodeBlock } from "@/components/ui/code-block"
import { CopyInstall } from "@/components/copy-install"
import { InteractiveButtons } from "@/components/home/interactive-buttons"
import { Hero } from "@/components/home/hero"

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-4 pt-4 py-10">
        <NavBar />
        <Hero />

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