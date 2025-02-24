import Image from "next/image"

export function Hero() {

  return (
    <div className="text-center max-w-4xl mx-auto">
      <div className="flex flex-col items-center gap-2 mb-8">
        <a 
          href="https://trilok.ai" 
          target="_blank" 
          rel="noopener noreferrer"
          className="inline-flex items-center px-4 py-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors text-gray-700 text-sm"
        >
          <span className="mr-2">Part of</span>
          <span className="font-semibold text-[hsl(15,85%,70%)]">Trilok.ai</span>
          <span className="ml-2">→</span>
        </a>
        <a 
          href="https://rach.codes/blog/Introducing-Bhumi" 
          target="_blank" 
          rel="noopener noreferrer"
          className="inline-flex items-center px-4 py-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors text-gray-700 text-sm"
        >
          <span className="mr-2">Read the</span>
          <span className="font-semibold text-[hsl(15,85%,70%)]">Technical Writeup</span>
          <span className="ml-2">→</span>
        </a>
      </div>
      <Image 
        width={192}
        height={192}
        src="https://images.bhumi.trilok.ai/bhumi_logo.png" 
        alt="Bhumi Logo" 
        className="mx-auto mb-8 w-48 h-48 rounded-xl"
        priority
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
    </div>
  )
} 