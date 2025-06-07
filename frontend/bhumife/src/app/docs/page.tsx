import { Metadata } from 'next';
import { NavBar } from '@/components/nav-bar';
import { DocumentationContent } from '@/components/docs/documentation-content';

export const metadata: Metadata = {
  title: 'Bhumi Documentation - Fast AI Inference',
  description: 'Comprehensive documentation for Bhumi, the high-performance AI inference client. Learn how to integrate and leverage Bhumi for optimal speed and efficiency.',
};

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-white">
      <NavBar />
      <div className="container mx-auto px-4 py-10 md:py-16">
        <header className="mb-10 md:mb-12 text-center">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-gray-900">
            Bhumi Documentation
          </h1>
          <p className="mt-3 text-lg md:text-xl text-gray-600 max-w-3xl mx-auto">
            Your complete guide to installing, configuring, and using Bhumi for blazing-fast AI inference across various models and providers.
          </p>
        </header>
        <main>
          <DocumentationContent />
        </main>
      </div>
      {/* Consider adding a consistent footer if not globally managed */}
    </div>
  );
}
