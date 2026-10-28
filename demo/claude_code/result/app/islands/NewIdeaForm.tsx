// Spec: knowledge/components/idea-board-page.md
// Enhances the plain HTML form: with JavaScript it posts JSON to the API and shows errors in place;
// without it, the same form posts to / and the server answers.
import { useState } from "preact/hooks";
import type { TargetedSubmitEvent } from "preact";
import { type FieldError, type IdeaFormValues, messageFor, parseIdeaForm } from "../domain/form.ts";
import { IdeaFormFields } from "../components/IdeaFormFields.tsx";

const FORM_FIELDS = new Set(["title", "description", "tags"]);

export default function NewIdeaForm(props: { values: IdeaFormValues; error?: FieldError }) {
  const [values, setValues] = useState(props.values);
  const [error, setError] = useState(props.error);
  const [sending, setSending] = useState(false);

  async function submit(event: TargetedSubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const draft = parseIdeaForm(new FormData(event.currentTarget));
    setValues(draft);
    setSending(true);
    try {
      const response = await fetch("/api/ideas", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(draft),
      });
      // A stored idea reloads the list from the server; anything else is shown, never swallowed.
      if (response.status === 201) return location.assign("/");
      const body = await response.json().catch(() => ({}));
      setError({ field: body.field ?? "form", reason: body.reason ?? body.error ?? `http_${response.status}` });
    } catch {
      setError({ field: "form", reason: "network" });
    } finally {
      setSending(false);
    }
  }

  const formError = error && !FORM_FIELDS.has(error.field) ? error : undefined;
  return (
    <form method="post" action="/" class="idea-form" onSubmit={submit} noValidate>
      {formError && <p class="form-error" role="alert">{messageFor(formError.reason)}</p>}
      <IdeaFormFields values={values} error={error} />
      <button type="submit" disabled={sending}>{sending ? "Saving…" : "Add idea"}</button>
    </form>
  );
}
