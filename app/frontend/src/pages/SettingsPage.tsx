import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Settings as SettingsIcon } from 'lucide-react';
import { IconLabel } from '@/components/ui/icon-label';
import { PageHeader } from '@/components/layout/PageHeader';
import { PageContent } from '@/components/layout/PageContent';

export function SettingsPage() {
  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Settings"
        description="Configure your application"
        icon={<SettingsIcon className="h-6 w-6 text-primary" />}
      />

      <PageContent>
          <Card>
            <CardHeader>
              <IconLabel 
                icon={
                  <div className="p-2 rounded-lg bg-primary/10 text-primary">
                    <SettingsIcon className="h-6 w-6" />
                  </div>
                } 
                gap="md"
              >
                <div>
                  <CardTitle>Settings</CardTitle>
                  <CardDescription>Coming Soon</CardDescription>
                </div>
              </IconLabel>
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
      </PageContent>
    </div>
  );
}
