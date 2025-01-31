"use client"

import { Github } from "lucide-react"
import { Button } from "@/components/ui/button"

export function NavBar() {
  return (
    <nav className="flex justify-between items-center mb-16">
      <div className="flex items-center gap-2">
        {/* <Image 
          src="https://images.bhumi.trilok.ai/bhumi_logo.png" 
          alt="Bhumi Logo" 
          className="w-10 h-10"
        /> */}
        <span className="font-bold text-xl">Bhumi</span>
      </div>
      <div className="flex gap-4">
        <Button variant="ghost">Documentation</Button>
        <Button variant="ghost">Benchmarks</Button>
        <Button variant="outline" onClick={() => window.open('https://github.com/justrach/bhumi', '_blank')}>
          <Github className="mr-2 h-4 w-4" />
          GitHub
        </Button>
      </div>
    </nav>
  )
} 