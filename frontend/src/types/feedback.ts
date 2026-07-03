export type FeedbackCategory = "bug" | "suggestion" | "content" | "other";

export interface FeedbackSubmitRequestBody {
  category: FeedbackCategory;
  message: string;
  contact_email?: string | null;
  page_url?: string | null;
  platform?: string | null;
  app_version?: string | null;
  /** Honeypot — must stay empty. */
  website?: string | null;
}

export interface FeedbackSubmitResponseBody {
  detail: string;
}

export const FEEDBACK_CATEGORY_OPTIONS: ReadonlyArray<{ value: FeedbackCategory; label: string }> = [
  { value: "bug", label: "Ошибка / проблема" },
  { value: "suggestion", label: "Предложение" },
  { value: "content", label: "Вопрос по новости" },
  { value: "other", label: "Другое" },
];
