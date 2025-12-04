// ======= Prompt Templates =======

export type TemplateType = 'retrieve_or_respond' | 'generate_answer';

export interface MessageBlock {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface Template {
  id: number;
  name: string;
  template_type: TemplateType;
  store_id: number;
  messages: MessageBlock[];
  is_active: boolean;
}

export interface TemplateCreate {
  name: string;
  template_type: TemplateType;
  store_id: number;
  messages: MessageBlock[];
}

export interface TemplateUpdate {
  name?: string;
  messages?: MessageBlock[];
  is_active?: boolean;
}

// Helper to get display name for template types
export const TEMPLATE_TYPE_LABELS: Record<TemplateType, string> = {
  retrieve_or_respond: 'Retrieve or Respond',
  generate_answer: 'Generate Answer',
};

export const TEMPLATE_TYPE_DESCRIPTIONS: Record<TemplateType, string> = {
  retrieve_or_respond: 'Decides whether to retrieve information or ask for clarification',
  generate_answer: 'Generates the final answer using retrieved documents',
};
