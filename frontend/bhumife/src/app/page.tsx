import { FeatureCards } from "@/components/feature-cards";
import { NavBar } from "@/components/nav-bar";
import { PerformanceChart } from "@/components/performance-chart";
import { Button } from "@/components/ui/button";
import { CodeBlock } from "@/components/ui/code-block";
import Image from "next/image";
import { CopyInstall } from "@/components/copy-install";
import { Card } from "@/components/ui/card";
import { Star, Github, ChevronRight, Code, Zap, Shield } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-white">
      <NavBar />
      
      <div className="container mx-auto px-4 py-12">
        {/* Hero Section */}
        <section className="text-center py-20 max-w-4xl mx-auto">
          <div className="mb-6">
            <Image
              width={140}
              height={140}
              src="https://images.bhumi.trilok.ai/bhumi_logo.png"
              alt="Bhumi Logo"
              className="mx-auto mb-8 w-35 h-35 rounded-xl shadow-lg"
            />
          </div>

          <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-6 tracking-tight">
            <span className="text-gray-900">Bhumi</span>{" "}
            <span className="text-orange-500">भूमि</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-700 mb-8 leading-relaxed">
            The <span className="text-orange-600 font-semibold">blazing-fast</span> AI inference client for Python
          </p>
          
          <p className="text-lg text-gray-600 mb-12 max-w-2xl mx-auto">
            Built with Rust for performance. Unified interface for{" "}
            <span className="text-orange-600 font-medium">OpenAI, Anthropic, Gemini, Groq</span>, and more.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <CopyInstall />
            
            <Button variant="outline" size="lg" className="border-orange-200 hover:bg-orange-50" asChild>
              <a href="https://github.com/justrach/bhumi" target="_blank" rel="noopener noreferrer">
                <Github className="w-5 h-5 mr-2" />
                View on GitHub
              </a>
            </Button>
            
            <Button size="lg" className="bg-orange-500 hover:bg-orange-600 text-white" asChild>
              <a href="/docs">
                Documentation
                <ChevronRight className="w-4 h-4 ml-2" />
              </a>
            </Button>
          </div>

          {/* Simple Stats */}
          <div className="grid grid-cols-3 gap-8 max-w-md mx-auto border-t border-gray-200 pt-8">
            <div className="text-center">
              <div className="text-2xl font-semibold text-orange-600">3x</div>
              <div className="text-sm text-gray-500">Faster</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-semibold text-orange-600">60%</div>
              <div className="text-sm text-gray-500">Less Memory</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-semibold text-orange-600">4+</div>
              <div className="text-sm text-gray-500">AI Providers</div>
            </div>
          </div>
        </section>

        {/* Quick Start */}
        <section className="max-w-4xl mx-auto mb-24">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Quick Start</h2>
            <p className="text-lg text-gray-600">Get started with your first AI call in seconds</p>
          </div>

          <Card className="p-8 border border-orange-100 bg-white shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
                <Code className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Example: OpenAI GPT-4</h3>
                <p className="text-sm text-gray-600">Simple async client usage</p>
              </div>
            </div>
            <CodeBlock
              language="python"
              code={`from bhumi.base_client import BaseLLMClient, LLMConfig
import asyncio

async def main():
    config = LLMConfig(
        api_key="YOUR_OPENAI_API_KEY", 
        model="openai/gpt-4o",
        max_tokens=1000
    )
    
    client = BaseLLMClient(config)
    
    response = await client.completion([
        {"role": "user", "content": "Hello, world!"}
    ])
    
    print(response['text'])

asyncio.run(main())`}
            />
          </Card>
        </section>

        {/* Performance */}
        <section className="max-w-5xl mx-auto mb-24">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Performance</h2>
            <p className="text-lg text-gray-600">Benchmarked against popular alternatives</p>
          </div>
          
          <Card className="p-8 border border-orange-100 bg-white shadow-sm">
            <PerformanceChart />
          </Card>
        </section>

        {/* Features */}
        <section className="mb-24">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Why Bhumi?</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Built for developers who need reliable, fast AI inference
            </p>
          </div>
          <FeatureCards />
        </section>

        {/* Key Benefits */}
        <section className="max-w-4xl mx-auto mb-24">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center p-6 bg-white rounded-lg border border-orange-100 shadow-sm">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Zap className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="font-semibold text-lg text-gray-900 mb-2">Fast</h3>
              <p className="text-gray-600">Rust-powered performance with async Python interface</p>
            </div>
            
            <div className="text-center p-6 bg-white rounded-lg border border-orange-100 shadow-sm">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Code className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="font-semibold text-lg text-gray-900 mb-2">Simple</h3>
              <p className="text-gray-600">Unified API for all major AI providers</p>
            </div>
            
            <div className="text-center p-6 bg-white rounded-lg border border-orange-100 shadow-sm">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Shield className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="font-semibold text-lg text-gray-900 mb-2">Reliable</h3>
              <p className="text-gray-600">Built-in rate limiting and error handling</p>
            </div>
          </div>
        </section>

        {/* Call to Action */}
        <section className="text-center py-16 border-t border-gray-200">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Ready to <span className="text-orange-600">go faster</span>?
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              Install Bhumi and make your first AI call in under 2 minutes
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="bg-orange-500 hover:bg-orange-600 text-white" asChild>
                <a href="/docs">
                  Get Started
                </a>
              </Button>
              
              <Button variant="outline" size="lg" className="border-orange-200 hover:bg-orange-50" asChild>
                <a href="https://github.com/justrach/bhumi" target="_blank" rel="noopener noreferrer">
                  <Star className="w-4 h-4 mr-2" />
                  Star on GitHub
                </a>
              </Button>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-gray-200 py-12 mt-20">
          <div className="text-center">
            <div className="mb-6">
              <Image
                width={32}
                height={32}
                src="https://images.bhumi.trilok.ai/bhumi_logo.png"
                alt="Bhumi Logo"
                className="mx-auto mb-3 w-8 h-8 rounded"
              />
              <p className="font-medium text-gray-900">Bhumi <span className="text-orange-500">भूमि</span></p>
            </div>
            
            <p className="text-gray-600 mb-6">
              Built by{" "}
              <a 
                href="https://trilok.ai" 
                className="text-orange-600 hover:text-orange-700 font-medium hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                Trilok.ai
              </a>
            </p>
            
            <div className="flex justify-center gap-6 text-sm text-gray-500">
              <a href="/docs" className="hover:text-orange-600">Documentation</a>
              <a href="https://github.com/justrach/bhumi" className="hover:text-orange-600">GitHub</a>
              <a href="mailto:support@trilok.ai" className="hover:text-orange-600">Support</a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}