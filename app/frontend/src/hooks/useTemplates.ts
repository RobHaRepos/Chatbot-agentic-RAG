import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  fetchTemplates, 
  fetchTemplate, 
  createTemplate, 
  updateTemplate, 
  deleteTemplate 
} from '@/services/api';
import type { Template, TemplateCreate, TemplateUpdate } from '@/types/template';

// Query keys for cache management
export const templateKeys = {
  all: ['templates'] as const,
  byStore: (storeId: number) => [...templateKeys.all, 'store', storeId] as const,
  detail: (id: number) => [...templateKeys.all, 'detail', id] as const,
};

/**
 * Fetch all templates for a store
 */
export function useTemplates(storeId: number) {
  return useQuery({
    queryKey: templateKeys.byStore(storeId),
    queryFn: () => fetchTemplates(storeId),
    enabled: storeId > 0,
  });
}

/**
 * Fetch a single template by ID
 */
export function useTemplate(templateId: number) {
  return useQuery({
    queryKey: templateKeys.detail(templateId),
    queryFn: () => fetchTemplate(templateId),
    enabled: templateId > 0,
  });
}

/**
 * Create a new template
 */
export function useCreateTemplate() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: TemplateCreate) => createTemplate(data),
    onSuccess: (newTemplate: Template) => {
      // Invalidate store-specific template list
      queryClient.invalidateQueries({ 
        queryKey: templateKeys.byStore(newTemplate.store_id) 
      });
    },
  });
}

/**
 * Update an existing template
 */
export function useUpdateTemplate(templateId: number) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: TemplateUpdate) => updateTemplate(templateId, data),
    onSuccess: (updatedTemplate: Template) => {
      // Update the specific template in cache
      queryClient.setQueryData(
        templateKeys.detail(templateId), 
        updatedTemplate
      );
      // Invalidate the store's template list
      queryClient.invalidateQueries({ 
        queryKey: templateKeys.byStore(updatedTemplate.store_id) 
      });
    },
  });
}

/**
 * Delete a template
 */
export function useDeleteTemplate() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ templateId }: { templateId: number; storeId: number }) => 
      deleteTemplate(templateId),
    onSuccess: (_, { storeId }) => {
      // Invalidate the store's template list
      queryClient.invalidateQueries({ 
        queryKey: templateKeys.byStore(storeId) 
      });
    },
  });
}
