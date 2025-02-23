import { Metadata } from 'next'
import { DocumentationContent } from '@/components/docs/documentation-content'

export const metadata: Metadata = {
  title: 'Bhumi Documentation - Fast AI Inference',
  description: 'Learn how to use Bhumi for faster AI inference on your device',
}

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-4 py-16">
        <DocumentationContent />
      </div>
    </div>
  )
}
