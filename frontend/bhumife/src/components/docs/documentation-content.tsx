'use client'

import React from 'react'
import { CodeBlock } from '@/components/ui/code-block'
import { Card } from '@/components/ui/card'
import { Alert } from '@/components/ui/alert'
import { NavBar } from '@/components/nav-bar'

export function DocumentationContent() {
  return (
    <>
      <NavBar />
      
      <div className="max-w-4xl mx-auto py-10 px-4">
        <header className="mb-12 text-center">
          <h1 className="text-6xl font-extrabold mb-4 tracking-tight">
            Bhumi <span className="font-black" style={{ color: "hsl(15, 85%, 70%)" }}>Documentation</span>
          </h1>
          <p className="text-xl text-gray-600">
            Fast, efficient AI inference for your applications
          </p>
        </header>

        <section className="mb-12">
          <h2 className="text-3xl font-semibold mb-6">Quick Start</h2>
          <Card className="p-6">
            <h3 className="text-xl font-medium mb-4">Installation</h3>
            <CodeBlock
              language="bash"
              code="pip install bhumi"
            />
          </Card>
        </section>

        <section className="mb-12">
          <h2 className="text-3xl font-semibold mb-6">Basic Usage</h2>
          <CodeBlock
            language="python"
            code={`
import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig
import os

async def main():
    config = LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="openai/gpt-4"
    )
    
    client = BaseLLMClient(config)
    response = await client.completion([
        {"role": "user", "content": "Hello!"}
    ])
    
    print(response['text'])

if __name__ == "__main__":
    asyncio.run(main())
            `}
          />
        </section>

        <section className="mb-12">
          <h2 className="text-3xl font-semibold mb-6">Supported Providers</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { name: 'OpenAI', prefix: 'openai/' },
              { name: 'Anthropic', prefix: 'anthropic/' },
              { name: 'Gemini', prefix: 'gemini/' },
              { name: 'Groq', prefix: 'groq/' },
              { name: 'SambaNova', prefix: 'sambanova/' },
            ].map((provider) => (
              <Card key={provider.name} className="p-6 hover:border-[hsl(15,85%,70%)] transition-colors">
                <h3 className="font-medium">{provider.name}</h3>
                <code className="text-sm text-[hsl(15,85%,70%)]">{provider.prefix}model_name</code>
              </Card>
            ))}
          </div>
        </section>

        <section className="mb-12">
          <h2 className="text-3xl font-semibold mb-6">Tool Usage Example</h2>
          <Alert className="mb-4 border-[hsl(15,85%,70%)] bg-[hsl(15,85%,95%)] text-[hsl(15,85%,30%)]">
            Bhumi supports external tool integration for enhanced AI capabilities
          </Alert>
          <CodeBlock
            language="python"
            code={`
async def get_weather(location: str, unit: str = "f") -> str:
    result = f"The weather in {location} is 75°{unit}"
    return result

# Register the tool
client.register_tool(
    name="get_weather",
    func=get_weather,
    description="Get the current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "The city and state"},
            "unit": {"type": "string", "enum": ["c", "f"]}
        },
        "required": ["location", "unit"]
    }
)
            `}
          />
        </section>

        <section className="mb-12">
          <h2 className="text-3xl font-semibold mb-6">Key Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="p-6 hover:border-[hsl(15,85%,70%)] transition-colors">
              <h3 className="font-medium mb-2 text-[hsl(15,85%,70%)]">Streaming Responses</h3>
              <p className="text-gray-600">
                Get real-time responses as they're generated
              </p>
            </Card>
            <Card className="p-6 hover:border-[hsl(15,85%,70%)] transition-colors">
              <h3 className="font-medium mb-2 text-[hsl(15,85%,70%)]">Multi-Provider Support</h3>
              <p className="text-gray-600">
                Easily switch between different AI providers
              </p>
            </Card>
            <Card className="p-6 hover:border-[hsl(15,85%,70%)] transition-colors">
              <h3 className="font-medium mb-2 text-[hsl(15,85%,70%)]">Tool Integration</h3>
              <p className="text-gray-600">
                Add custom tools for enhanced functionality
              </p>
            </Card>
          </div>
        </section>

        <section className="mb-12">
          <h2 className="text-3xl font-semibold mb-6">Streaming Configuration</h2>
          <Alert className="mb-4 border-[hsl(15,85%,70%)] bg-[hsl(15,85%,95%)] text-[hsl(15,85%,30%)]">
            Bhumi supports both streaming and non-streaming modes. Streaming provides faster initial responses and real-time updates.
          </Alert>
          
          <div className="space-y-8">
            <div>
              <h3 className="text-xl font-medium mb-4">Streaming Mode (Default)</h3>
              <CodeBlock
                language="python"
                code={`
import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig

async def main():
    config = LLMConfig(
        api_key="your-api-key",
        model="openai/gpt-4",
        stream=True  # Enable streaming (default)
    )
    
    client = BaseLLMClient(config)
    
    # Option 1: Process chunks as they arrive
    async for chunk in client.stream([
        {"role": "user", "content": "Write a story about a robot"}
    ]):
        print(chunk.text, end="", flush=True)
    
    # Option 2: Get final response with streaming internally enabled
    response = await client.completion([
        {"role": "user", "content": "Write a story about a robot"}
    ])
    print(response['text'])

if __name__ == "__main__":
    asyncio.run(main())`}
              />
            </div>

            <div>
              <h3 className="text-xl font-medium mb-4">Non-Streaming Mode</h3>
              <CodeBlock
                language="python"
                code={`
import asyncio
from bhumi.base_client import BaseLLMClient, LLMConfig

async def main():
    config = LLMConfig(
        api_key="your-api-key",
        model="openai/gpt-4",
        stream=False  # Disable streaming
    )
    
    client = BaseLLMClient(config)
    
    # Get complete response at once
    response = await client.completion([
        {"role": "user", "content": "Write a story about a robot"}
    ])
    print(response['text'])

if __name__ == "__main__":
    asyncio.run(main())`}
              />
            </div>

            <Card className="p-6">
              <h3 className="text-xl font-medium mb-4 text-[hsl(15,85%,70%)]">When to Use Each Mode</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-2">Use Streaming When:</h4>
                  <ul className="list-disc list-inside text-gray-600 space-y-2">
                    <li>You want to show real-time progress</li>
                    <li>Working with long responses</li>
                    <li>Building interactive chat interfaces</li>
                    <li>Need faster initial response times</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Use Non-Streaming When:</h4>
                  <ul className="list-disc list-inside text-gray-600 space-y-2">
                    <li>Processing responses in batch</li>
                    <li>Need complete response for processing</li>
                    <li>Working with structured outputs</li>
                    <li>Implementing retry logic</li>
                  </ul>
                </div>
              </div>
            </Card>
          </div>
        </section>
      </div>
    </>
  )
} 