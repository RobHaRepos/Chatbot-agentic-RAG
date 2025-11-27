import { Link, useLocation } from 'react-router-dom';
import { MessageSquare, Database, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Chat', href: '/', icon: MessageSquare },
  { name: 'Vector Stores', href: '/vectorstores', icon: Database },
  { name: 'Settings', href: '/settings', icon: Settings },
];

interface SidebarProps {
  readonly isMobileMenuOpen?: boolean;
  readonly onClose?: () => void;
}

export function Sidebar({ isMobileMenuOpen, onClose }: Readonly<SidebarProps>) {
  const location = useLocation();

  return (
    <aside className={cn(
      "w-64 border-r border-border bg-card/50 backdrop-blur-sm",
      "md:relative md:translate-x-0 transition-transform duration-300 ease-in-out",
      "fixed inset-y-0 left-0 z-50",
      isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
    )}>
      <div className="flex h-full flex-col">
        <div className="p-6">
          <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            LangGraph Chat
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            AI-Powered Assistant
          </p>
        </div>

        <nav className="flex-1 space-y-1 px-3">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                onClick={onClose}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 text-xs text-muted-foreground border-t border-border">
          <p>v1.0.0 • Built with React</p>
        </div>
      </div>
    </aside>
  );
}
