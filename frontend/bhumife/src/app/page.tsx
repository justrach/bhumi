import { FeatureCards } from "@/components/feature-cards";
import { NavBar } from "@/components/nav-bar";
import { PerformanceChart } from "@/components/performance-chart";
import { Button } from "@/components/ui/button";
import { CodeBlock } from "@/components/ui/code-block";
import Image from "next/image";
import { CopyInstall } from "@/components/copy-install";
import { Card } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
         <NavBar />
      <div className="container mx-auto px-4 py-10">
     

        {/* --- Hero Section --- */}
        <section className="text-center py-16 md:py-20">
          <Image
            width={160}
            height={160}
            src="https://images.bhumi.trilok.ai/bhumi_logo.png"
            alt="Bhumi Logo"
            className="mx-auto mb-6 w-40 h-40 rounded-xl shadow-lg"
          />
          <h1 className="text-6xl md:text-7xl font-extrabold mb-3 tracking-tight">
            Bhumi <span style={{ color: "hsl(15, 85%, 70%)" }}>भूमि</span>
          </h1>
          <p className="text-2xl md:text-3xl text-gray-700 mb-6 max-w-3xl mx-auto leading-snug">
            The <span className="font-bold text-[hsl(15,85%,60%)]">blazing-fast</span> AI inference client for Python, powered by Rust.
          </p>
          <p className="text-lg text-gray-600 mb-10 max-w-2xl mx-auto">
            Unmatched performance via native multiprocessing. Supports OpenAI, Anthropic, Gemini, Groq, and more.
          </p>

          {/* --- Main CTAs --- */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <CopyInstall />
            <Button variant="outline" size="lg" asChild>
              <a href="https://github.com/justrach/bhumi" target="_blank" rel="noopener noreferrer">
                View on GitHub
              </a>
            </Button>
            <Button variant="default" size="lg" asChild>
              <a href="/docs" rel="noopener noreferrer"> {/* Replace with actual docs path */}
                Read Docs
              </a>
            </Button>
          </div>
        </section>

        {/* --- Quick Start --- */}
        <section className="max-w-3xl mx-auto mb-16 md:mb-24">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-8">Get Started in Seconds</h2>
          <Card className="p-6 shadow-lg">
            <CodeBlock
              language="python"
              code={`from bhumi.base_client import BaseLLMClient, LLMConfig
import asyncio

async def main():
    # Configure with your API key and desired model
    config = LLMConfig(
        api_key="YOUR_API_KEY", 
        model="openai/gpt-4o"
    )
    client = BaseLLMClient(config)

    response = await client.completion([
        {"role": "user", "content": "Hello, Bhumi!"}
    ])
    print(response['text'])

if __name__ == "__main__":
    asyncio.run(main())`}
            />
          </Card>
        </section>

        {/* --- Performance --- */}
        <section className="max-w-4xl mx-auto mb-16 md:mb-24">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-8">Experience the Speed</h2>
          <PerformanceChart />
        </section>

        {/* --- Features --- */}
        <section className="mb-16 md:mb-24">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">Why Bhumi?</h2>
          <FeatureCards />
        </section>

        {/* --- Footer --- */}
        <footer className="text-center text-gray-600 py-8 border-t">
          <p className="mb-2">
            Built with ❤️ by <a href="https://trilok.ai" className="text-[hsl(15,85%,70%)] hover:underline">Trilok.ai</a>
          </p>
          <a
            href="https://trilok.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-3 py-1 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors text-gray-700 text-xs"
          >
            <span className="mr-1">Powered by</span>
            <span className="font-semibold text-[hsl(15,85%,50%)]">Trilok.ai</span>
          </a>
        </footer>
      </div>
    </div>
  );
}