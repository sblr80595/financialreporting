import React from 'react';
import { AlertCircle } from 'lucide-react';

interface FormErrorProps {
  message?: string;
  errors?: string[];
  className?: string;
}

export const FormError: React.FC<FormErrorProps> = ({ message, errors, className = '' }) => {
  if (!message && (!errors || errors.length === 0)) return null;

  return (
    <div className={`rounded-md bg-red-50 p-4 ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <AlertCircle className="h-5 w-5 text-red-400" />
        </div>
        <div className="ml-3">
          {message && (
            <h3 className="text-sm font-medium text-red-800">{message}</h3>
          )}
          {errors && errors.length > 0 && (
            <div className="mt-2 text-sm text-red-700">
              <ul className="list-disc space-y-1 pl-5">
                {errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

interface FieldErrorProps {
  error?: string;
  touched?: boolean;
}

export const FieldError: React.FC<FieldErrorProps> = ({ error, touched }) => {
  if (!error || !touched) return null;

  return (
    <p className="mt-1 text-sm text-red-600">{error}</p>
  );
};

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  touched?: boolean;
  required?: boolean;
  helperText?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  touched,
  required,
  helperText,
  className = '',
  ...props
}) => {
  const hasError = error && touched;

  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <input
        className={`
          block w-full rounded-md shadow-sm
          ${hasError
            ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
            : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
          }
          ${className}
        `}
        {...props}
      />
      {hasError && <FieldError error={error} touched={touched} />}
      {helperText && !hasError && (
        <p className="text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  );
};

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  touched?: boolean;
  required?: boolean;
  helperText?: string;
  options: Array<{ value: string; label: string }>;
}

export const Select: React.FC<SelectProps> = ({
  label,
  error,
  touched,
  required,
  helperText,
  options,
  className = '',
  ...props
}) => {
  const hasError = error && touched;

  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <select
        className={`
          block w-full rounded-md shadow-sm
          ${hasError
            ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
            : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
          }
          ${className}
        `}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {hasError && <FieldError error={error} touched={touched} />}
      {helperText && !hasError && (
        <p className="text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  );
};

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  touched?: boolean;
  required?: boolean;
  helperText?: string;
}

export const TextArea: React.FC<TextAreaProps> = ({
  label,
  error,
  touched,
  required,
  helperText,
  className = '',
  ...props
}) => {
  const hasError = error && touched;

  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <textarea
        className={`
          block w-full rounded-md shadow-sm
          ${hasError
            ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
            : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
          }
          ${className}
        `}
        {...props}
      />
      {hasError && <FieldError error={error} touched={touched} />}
      {helperText && !hasError && (
        <p className="text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  );
};

export const validateRequired = (value: any): string | undefined => {
  return value ? undefined : 'This field is required';
};

export const validateEmail = (value: string): string | undefined => {
  if (!value) return undefined;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(value) ? undefined : 'Invalid email address';
};

export const validateMinLength = (min: number) => (value: string): string | undefined => {
  if (!value) return undefined;
  return value.length >= min ? undefined : `Must be at least ${min} characters`;
};

export const validateMaxLength = (max: number) => (value: string): string | undefined => {
  if (!value) return undefined;
  return value.length <= max ? undefined : `Must be at most ${max} characters`;
};

export const validateNumber = (value: string): string | undefined => {
  if (!value) return undefined;
  return !isNaN(Number(value)) ? undefined : 'Must be a valid number';
};

export const composeValidators = (...validators: Array<(value: any) => string | undefined>) => (
  value: any
): string | undefined => {
  for (const validator of validators) {
    const error = validator(value);
    if (error) return error;
  }
  return undefined;
};
