'use client';

import React from 'react';
import { CodeBlock } from '@/components/ui/code-block';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'; // Assuming Card can take Header/Title/Content
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'; // Assuming Alert can take Title/Description

export function DocumentationContent() {
  // Helper for consistent section titles
  const SectionTitle: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <h2 className="text-3xl font-semibold pb-3 mb-8 border-b border-gray-200">
      {children}
    </h2>
  );

  // Helper for consistent subsection titles
  const SubSectionTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
    <h3 className={`text-xl font-medium mb-4 ${className || ''}`}>
      {children}
    </h3>
  );

  return (
    <>
      {/* NavBar and Header are now handled by the parent page (docs/page.tsx) */}
      <div className="max-w-4xl mx-auto px-4 space-y-16">
        {/* Added space-y-16 for consistent vertical spacing between sections */}
        
        <section className="pt-8"> {/* pt-8 for initial spacing from page header */}
          <SectionTitle>Quick Start</SectionTitle>
          <Card className="overflow-hidden"> {/* Added overflow-hidden for cleaner look with CodeBlock */}
            <CardHeader>
              <SubSectionTitle>Installation</SubSectionTitle>
            </CardHeader>
            <CardContent>
              <CodeBlock
                language="bash"
                code="pip install bhumi"
              />
            </CardContent>
          </Card>
        </section>

        <section>
          <SectionTitle>Basic Usage</SectionTitle>
          {/* Assuming CodeBlock can be placed directly or within a Card if preferred */}
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

        <section>
          <SectionTitle>Supported Providers</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              { name: 'OpenAI', prefix: 'openai/' },
              { name: 'Anthropic', prefix: 'anthropic/' },
              { name: 'Gemini', prefix: 'gemini/' },
              { name: 'Groq', prefix: 'groq/' },
              { name: 'SambaNova', prefix: 'sambanova/' },
            ].map((provider) => (
              <Card key={provider.name} className="hover:border-[hsl(15,85%,70%)] transition-colors">
                <CardHeader>
                  <CardTitle className="text-lg">{provider.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-500 mb-1">Model Prefix:</p>
                  <code className="text-sm text-[hsl(15,85%,70%)] bg-orange-50 px-2 py-1 rounded-md">{provider.prefix}model_name</code>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section>
          <SectionTitle>Tool Usage Example</SectionTitle>
          <Alert className="my-6 border-[hsl(15,85%,70%)] bg-[hsl(15,85%,95%)] text-[hsl(15,85%,30%)]">
            {/* <AlertTitle>Tool Integration</AlertTitle> Optional: if Alert supports it */}
            <AlertDescription>
              Bhumi supports external tool integration for enhanced AI capabilities.
            </AlertDescription>
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

        <section>
          <SectionTitle>Key Features</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { title: "Streaming Responses", description: "Get real-time responses as they're generated." },
              { title: "Multi-Provider Support", description: "Easily switch between different AI providers." },
              { title: "Tool Integration", description: "Add custom tools for enhanced functionality." },
            ].map((feature) => (
              <Card key={feature.title} className="hover:border-[hsl(15,85%,70%)] transition-colors">
                <CardHeader>
                  <CardTitle className="text-lg text-[hsl(15,85%,70%)]">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 text-sm">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section>
          <SectionTitle>Streaming Configuration</SectionTitle>
          <Alert className="my-6 border-[hsl(15,85%,70%)] bg-[hsl(15,85%,95%)] text-[hsl(15,85%,30%)]">
            {/* <AlertTitle>Streaming Modes</AlertTitle> */}
            <AlertDescription>
              Bhumi supports both streaming and non-streaming modes. Streaming provides faster initial responses and real-time updates.
            </AlertDescription>
          </Alert>
          
          <div className="space-y-12"> {/* Increased space-y for better separation */}
            <div>
              <SubSectionTitle>Streaming Mode (Default)</SubSectionTitle>
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
              <SubSectionTitle>Non-Streaming Mode</SubSectionTitle>
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