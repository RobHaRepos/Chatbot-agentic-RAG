import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function Layout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Mobile Menu Button */}
      <Button
        variant="outline"
        size="icon"
        className="md:hidden fixed top-4 left-4 z-50 bg-card shadow-lg"
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
      >
        {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </Button>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <button
          type="button"
          className="md:hidden fixed inset-0 bg-background/80 backdrop-blur-sm z-40 cursor-default"
          onClick={() => setIsMobileMenuOpen(false)}
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              setIsMobileMenuOpen(false);
            }
          }}
          aria-label="Close menu"
        />
      )}

      {/* Sidebar - Desktop always visible, Mobile drawer */}
      <Sidebar 
        isMobileMenuOpen={isMobileMenuOpen} 
        onClose={() => setIsMobileMenuOpen(false)} 
      />

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
