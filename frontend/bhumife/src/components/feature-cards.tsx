"use client"

import { Zap, Brain, Github, Cpu, Code, Lock } from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

const features = [
  {
    icon: Zap,
    title: "Lightning Fast",
    description: "2-3x faster than alternatives with optimized Rust implementation",
    color: "hsl(15,85%,70%)"
  },
  {
    icon: Code,
    title: "Multi-Model Support",
    description: "Seamless integration with OpenAI, Anthropic, and Gemini models",
    color: "hsl(15,85%,70%)"
  },
  {
    icon: Cpu,
    title: "Resource Efficient",
    description: "Uses 60% less memory while handling concurrent requests",
    color: "hsl(15,85%,70%)"
  },
  {
    icon: Brain,
    title: "Production Ready",
    description: "Battle-tested in high-throughput environments with 99.9% uptime",
    color: "hsl(15,85%,70%)"
  },
  {
    icon: Github,
    title: "Open Source",
    description: "Apache 2.0 licensed, free for commercial use with attribution",
    color: "hsl(15,85%,70%)"
  },
  {
    icon: Lock,
    title: "Enterprise Ready",
    description: "Built-in rate limiting, error handling, and monitoring",
    color: "hsl(15,85%,70%)"
  }
]

export function FeatureCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
      {features.map((feature, index) => {
        const Icon = feature.icon
        return (
          <Card 
            key={index} 
            className="border-2 transition-all duration-300 hover:shadow-lg hover:border-[hsl(15,85%,70%)]"
          >
            <CardHeader>
              <div 
                className="w-12 h-12 bg-[hsl(15,85%,70%)] bg-opacity-10 rounded-full 
                          flex items-center justify-center mb-4 
                          transition-all duration-300 group-hover:bg-opacity-20"
              >
                <Icon className="h-6 w-6 text-[hsl(15,85%,70%)]" />
              </div>
              <CardTitle className="text-xl mb-2">{feature.title}</CardTitle>
              <CardDescription className="text-base">
                {feature.description}
              </CardDescription>
            </CardHeader>
          </Card>
        )
      })}
    </div>
  )
} 