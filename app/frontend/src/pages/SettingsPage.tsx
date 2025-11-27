import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Settings as SettingsIcon } from 'lucide-react';

export function SettingsPage() {
  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-border bg-card/30 backdrop-blur-sm px-6 py-4">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-sm text-muted-foreground">
            Configure your application
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/10 text-primary">
                  <SettingsIcon className="h-6 w-6" />
                </div>
                <div>
                  <CardTitle>Settings</CardTitle>
                  <CardDescription>Coming Soon</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Future settings options will include:
              </p>
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                <li>• API configuration</li>
                <li>• Model selection</li>
                <li>• Default parameters</li>
                <li>• Theme customization</li>
                <li>• Logging preferences</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
