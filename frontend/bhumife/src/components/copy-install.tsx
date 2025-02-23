'use client'

import { Copy } from "lucide-react"
import { useState } from "react"

export function CopyInstall() {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText("pip install bhumi")
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="inline-flex items-center gap-2 bg-gray-100 rounded-lg font-mono text-sm overflow-hidden">
      <div className="px-4 py-2">
        <span className="text-gray-500 mr-2">$</span>
        <span>pip install bhumi</span>
      </div>
      <button
        onClick={copyToClipboard}
        className="p-2 hover:bg-gray-200 transition-colors border-l border-gray-200"
        aria-label="Copy install command"
      >
        <Copy className={`h-4 w-4 ${copied ? 'text-green-500' : 'text-gray-400'}`} />
      </button>
    </div>
  )
} 