// Spec: knowledge/components/idea-board-page.md
// The form's fields, shared by the server page and the island so both render the same markup.
import { type FieldError, type IdeaFormValues, messageFor } from "../domain/form.ts";

interface FieldProps {
  name: keyof IdeaFormValues;
  label: string;
  hint?: string;
  value: string;
  error?: FieldError;
  multiline?: boolean;
  maxLength: number;
}

function Field({ name, label, hint, value, error, multiline, maxLength }: FieldProps) {
  // The error, when it is this field's, is announced with the field through aria-describedby.
  const invalid = error?.field === name;
  const describedBy = invalid ? `${name}-error` : hint ? `${name}-hint` : undefined;
  const control = {
    id: name,
    name,
    value,
    maxLength,
    "aria-invalid": invalid || undefined,
    "aria-describedby": describedBy,
  };
  return (
    <div class="field">
      <label for={name}>{label}</label>
      {multiline ? <textarea rows={3} {...control} /> : <input type="text" {...control} />}
      {invalid
        ? <p id={`${name}-error`} class="field-error">{messageFor(error.reason)}</p>
        : hint && <p id={`${name}-hint`} class="field-hint">{hint}</p>}
    </div>
  );
}

export function IdeaFormFields({ values, error }: { values: IdeaFormValues; error?: FieldError }) {
  return (
    <>
      <Field name="title" label="Title" value={values.title} error={error} maxLength={80} />
      <Field
        name="description"
        label="Description (optional)"
        value={values.description}
        error={error}
        multiline
        maxLength={500}
      />
      <Field
        name="tags"
        label="Tags (optional)"
        hint="Comma-separated, up to 5: ux, sync"
        value={values.tags.join(", ")}
        error={error}
        maxLength={120}
      />
    </>
  );
}
