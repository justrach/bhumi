'use client'

import { Button } from "@/components/ui/button"
import { Brain } from "lucide-react"

export function InteractiveButtons() {
  return (
    <Button 
      size="lg" 
      variant="outline"
      onClick={() => window.location.href='/docs'}
      className="hover:border-[hsl(15,85%,70%)] transition-colors"
    >
      <Brain className="mr-2 h-5 w-5" />
      View Docs
    </Button>
  )
} 