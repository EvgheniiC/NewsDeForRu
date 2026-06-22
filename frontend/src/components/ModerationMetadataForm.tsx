import { useEffect, useState } from "react";
import { newsTopicChipClass } from "../lib/newsUi";
import { newsTopicLabelRu, type NewsTopic, type ProcessedNews } from "../types/news";

const TOPIC_OPTIONS: readonly NewsTopic[] = ["politics", "economy", "life"] as const;

export interface NewsMetadataDraft {
  topic: NewsTopic;
  is_urgent: boolean;
  is_positive: boolean;
}

interface ModerationMetadataFormProps {
  item: ProcessedNews;
  disabled: boolean;
  onSave: (newsId: number, draft: NewsMetadataDraft) => Promise<void>;
}

function draftFromItem(item: ProcessedNews): NewsMetadataDraft {
  return {
    topic: item.topic,
    is_urgent: item.is_urgent,
    is_positive: item.is_positive,
  };
}

function draftsEqual(left: NewsMetadataDraft, right: NewsMetadataDraft): boolean {
  return (
    left.topic === right.topic &&
    left.is_urgent === right.is_urgent &&
    left.is_positive === right.is_positive
  );
}

export function ModerationMetadataForm({
  item,
  disabled,
  onSave,
}: ModerationMetadataFormProps): JSX.Element {
  const [draft, setDraft] = useState<NewsMetadataDraft>(() => draftFromItem(item));
  const [saving, setSaving] = useState<boolean>(false);
  const [saveError, setSaveError] = useState<string>("");

  useEffect(() => {
    setDraft(draftFromItem(item));
    setSaveError("");
  }, [item]);

  const savedDraft: NewsMetadataDraft = draftFromItem(item);
  const isDirty: boolean = !draftsEqual(draft, savedDraft);

  const handleSave = async (): Promise<void> => {
    if (!isDirty) {
      return;
    }
    setSaving(true);
    setSaveError("");
    try {
      await onSave(item.id, draft);
    } catch (error: unknown) {
      setSaveError(error instanceof Error ? error.message : "Не удалось сохранить метки.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="moderation-metadata-form">
      <p className="moderation-metadata-label">Метки перед публикацией</p>
      <label className="moderation-metadata-field">
        <span>Категория</span>
        <select
          disabled={disabled || saving}
          onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
            setDraft((current: NewsMetadataDraft) => ({
              ...current,
              topic: event.target.value as NewsTopic,
            }))
          }
          value={draft.topic}
        >
          {TOPIC_OPTIONS.map((topic: NewsTopic) => (
            <option key={topic} value={topic}>
              {newsTopicLabelRu(topic)}
            </option>
          ))}
        </select>
      </label>
      <label className="moderation-metadata-checkbox">
        <input
          checked={draft.is_urgent}
          disabled={disabled || saving}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            setDraft((current: NewsMetadataDraft) => ({
              ...current,
              is_urgent: event.target.checked,
            }))
          }
          type="checkbox"
        />
        <span>Срочная</span>
      </label>
      <label className="moderation-metadata-checkbox">
        <input
          checked={draft.is_positive}
          disabled={disabled || saving}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            setDraft((current: NewsMetadataDraft) => ({
              ...current,
              is_positive: event.target.checked,
            }))
          }
          type="checkbox"
        />
        <span>Позитивная</span>
      </label>
      <div className="moderation-metadata-actions">
        <button
          disabled={disabled || saving || !isDirty}
          onClick={() => void handleSave()}
          type="button"
        >
          {saving ? "Сохранение…" : "Сохранить метки"}
        </button>
        <span className={newsTopicChipClass(draft.topic)}>{newsTopicLabelRu(draft.topic)}</span>
      </div>
      {saveError !== "" ? <p className="error moderation-metadata-error">{saveError}</p> : null}
    </div>
  );
}
