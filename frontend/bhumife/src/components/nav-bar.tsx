"use client";

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { Github, Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useState } from 'react';

export function NavBar() {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { href: '/docs', label: 'Documentation' },
    { href: '/benchmarks', label: 'Benchmarks' },
  ];

  const toggleMobileMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);
  const closeMobileMenu = () => setIsMobileMenuOpen(false);

  return (
    <nav className="w-full border-b border-gray-200 bg-white/80 backdrop-blur-md sticky top-0 z-50 mb-10 md:mb-12">
      <div className="container mx-auto px-4 flex justify-between items-center py-3 md:py-4">
        {/* Logo */}
        <Link href="/" legacyBehavior passHref>
          <a className="flex items-center gap-2 group" onClick={closeMobileMenu}>
            <Image 
              src="https://images.bhumi.trilok.ai/bhumi_logo.png" 
              alt="Bhumi Logo" 
              width={32}
              height={32}
              className="w-8 h-8 group-hover:opacity-80 transition-opacity rounded-md"
            /> 
            <span className="font-bold text-xl hover:text-[hsl(15,85%,70%)] transition-colors">
              Bhumi
            </span>
          </a>
        </Link>

        {/* Desktop Navigation Links (Centered) */}
        <div className="hidden md:flex flex-1 justify-center items-center gap-1 md:gap-2">
          {navItems.map((item) => (
            <Button variant="ghost" asChild key={item.href}>
              <Link 
                href={item.href} 
                className={cn(
                  "text-sm md:text-base px-3 py-2",
                  pathname === item.href 
                    ? "text-[hsl(15,85%,70%)] font-semibold" 
                    : "text-gray-600 hover:text-[hsl(15,85%,70%)]",
                  "transition-colors"
                )}
              >
                {item.label}
              </Link>
            </Button>
          ))}
        </div>

        {/* Right Aligned Actions: GitHub and Hamburger Menu */}
        <div className="flex items-center gap-2">
          <Button 
            variant="outline"
            size="sm"
            onClick={() => window.open('https://github.com/trilokai/bhumi', '_blank')} 
            aria-label="View source on GitHub"
            className="flex items-center"
          >
            <Github className="h-4 w-4 md:mr-2" />
            <span className="hidden md:inline">GitHub</span>
          </Button>

          {/* Hamburger Menu Button - Mobile Only */}
          <div className="md:hidden">
            <Button onClick={toggleMobileMenu} variant="ghost" size="icon" aria-label="Toggle menu">
              {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Panel */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white/95 backdrop-blur-md">
          <div className="container mx-auto px-4 py-4 flex flex-col space-y-2">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={closeMobileMenu}
                className={cn(
                  "block px-3 py-2 rounded-md text-base font-medium",
                  pathname === item.href
                    ? "text-white bg-[hsl(15,85%,60%)]"
                    : "text-gray-700 hover:bg-gray-100 hover:text-[hsl(15,85%,70%)]",
                  "transition-colors"
                )}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}