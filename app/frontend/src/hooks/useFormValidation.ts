import { useState, useCallback } from 'react';

export interface ValidationRule {
  test: (value: string) => boolean;
  message: string;
}

export interface FieldValidation {
  value: string;
  error: string | null;
  isDirty: boolean;
}

/**
 * Hook for form field validation
 * CRITICAL: Replaces scattered .trim() checks and manual validation
 * 
 * @param initialValue - Initial field value
 * @param rules - Array of validation rules
 */
export function useFormField(
  initialValue: string = '',
  rules: ValidationRule[] = []
): {
  value: string;
  error: string | null;
  isDirty: boolean;
  isValid: boolean;
  setValue: (value: string) => void;
  validate: () => boolean;
  reset: () => void;
} {
  const [field, setField] = useState<FieldValidation>({
    value: initialValue,
    error: null,
    isDirty: false,
  });

  const validate = useCallback((value: string): string | null => {
    for (const rule of rules) {
      if (!rule.test(value)) {
        return rule.message;
      }
    }
    return null;
  }, [rules]);

  const setValue = useCallback((newValue: string) => {
    const error = validate(newValue);
    setField({
      value: newValue,
      error,
      isDirty: true,
    });
  }, [validate]);

  const validateField = useCallback(() => {
    const error = validate(field.value);
    setField(prev => ({ ...prev, error, isDirty: true }));
    return error === null;
  }, [field.value, validate]);

  const reset = useCallback(() => {
    setField({
      value: initialValue,
      error: null,
      isDirty: false,
    });
  }, [initialValue]);

  return {
    value: field.value,
    error: field.error,
    isDirty: field.isDirty,
    isValid: field.error === null,
    setValue,
    validate: validateField,
    reset,
  };
}

/**
 * Common validation rules
 */
export const validationRules = {
  required: (message: string = 'This field is required'): ValidationRule => ({
    test: (value) => value.trim().length > 0,
    message,
  }),
  minLength: (min: number, message?: string): ValidationRule => ({
    test: (value) => value.trim().length >= min,
    message: message || `Minimum length is ${min} characters`,
  }),
  maxLength: (max: number, message?: string): ValidationRule => ({
    test: (value) => value.trim().length <= max,
    message: message || `Maximum length is ${max} characters`,
  }),
};
