import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Edit2, RotateCcw, Plus } from 'lucide-react';
import { IconLabel } from '@/components/ui/icon-label';
import { ErrorState, EmptyState } from '@/components/common';
import { SkeletonCard } from '@/components/common/SkeletonCard';
import { TemplateEditDialog } from './TemplateEditDialog';
import { CreateTemplateDialog } from './CreateTemplateDialog';
import { useTemplates } from '@/hooks/useTemplates';
import type { Template } from '@/types/template';
import { TEMPLATE_TYPE_LABELS, TEMPLATE_TYPE_DESCRIPTIONS } from '@/types/template';

interface TemplateListProps {
  storeId: number;
}

export function TemplateList({ storeId }: Readonly<TemplateListProps>) {
  const { data: templates, isLoading, error, refetch } = useTemplates(storeId);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : 'Failed to load templates'}
        onRetry={() => refetch()}
      />
    );
  }

  if (!templates || templates.length === 0) {
    return (
      <>
        <EmptyState
          icon={<MessageSquare className="h-12 w-12" />}
          message="No templates configured for this store. Default templates will be used."
          action={
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Template
            </Button>
          }
        />
        <CreateTemplateDialog
          open={isCreateDialogOpen}
          onOpenChange={setIsCreateDialogOpen}
          storeId={storeId}
          onCreated={() => refetch()}
        />
      </>
    );
  }

  return (
    <>
      <div className="space-y-4">
        <div className="flex justify-end">
          <Button variant="outline" size="sm" onClick={() => setIsCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Template
          </Button>
        </div>
        {templates.map((template) => (
          <TemplateCard
            key={template.id}
            template={template}
            onEdit={() => setEditingTemplate(template)}
          />
        ))}
      </div>

      {editingTemplate && (
        <TemplateEditDialog
          open={!!editingTemplate}
          onOpenChange={(open) => !open && setEditingTemplate(null)}
          template={editingTemplate}
          onSaved={() => {
            setEditingTemplate(null);
            refetch();
          }}
        />
      )}

      <CreateTemplateDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        storeId={storeId}
        onCreated={() => refetch()}
      />
    </>
  );
}

interface TemplateCardProps {
  template: Template;
  onEdit: () => void;
}

function TemplateCard({ template, onEdit }: Readonly<TemplateCardProps>) {
  const messageCount = template.messages.length;
  const systemMessages = template.messages.filter((m) => m.role === 'system').length;
  const userMessages = template.messages.filter((m) => m.role === 'user').length;

  return (
    <Card className={template.is_active ? undefined : 'opacity-60'}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h4 className="font-medium">{template.name}</h4>
              {!template.is_active && (
                <Badge variant="secondary" className="text-xs">
                  Inactive
                </Badge>
              )}
            </div>
            <CardDescription>
              {TEMPLATE_TYPE_LABELS[template.template_type]}
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onEdit}>
            <Edit2 className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground mb-3">
          {TEMPLATE_TYPE_DESCRIPTIONS[template.template_type]}
        </p>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <IconLabel icon={<MessageSquare className="h-3 w-3" />} gap="xs">
            {messageCount} message{messageCount === 1 ? '' : 's'}
          </IconLabel>
          <span className="text-xs">
            ({systemMessages} system, {userMessages} user)
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

interface ResetTemplateButtonProps {
  templateId: number;
  onReset?: () => void;
}

export function ResetTemplateButton({ templateId: _templateId, onReset }: Readonly<ResetTemplateButtonProps>) {
  // Future: implement reset to default functionality
  return (
    <Button variant="outline" size="sm" onClick={onReset} disabled>
      <RotateCcw className="h-4 w-4 mr-2" />
      Reset to Default
    </Button>
  );
}
