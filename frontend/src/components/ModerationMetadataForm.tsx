import { useEffect, useState } from "react";
import { newsTopicChipClass } from "../lib/newsUi";
import {
  coverTagLabelRu,
  newsTopicLabelRu,
  type CoverTag,
  type NewsTopic,
  type ProcessedNews
} from "../types/news";
import { NewsTopicCover } from "./NewsTopicCover";

const TOPIC_OPTIONS: readonly NewsTopic[] = ["politics", "economy", "life"] as const;
const TITLE_MAX_LENGTH: number = 300;
const SUMMARY_MAX_LENGTH: number = 2000;

interface CoverTagGroup {
  label: string;
  tags: readonly CoverTag[];
}

const COVER_TAG_GROUPS: readonly CoverTagGroup[] = [
  { label: "Политика", tags: ["government", "elections", "eu", "security"] },
  { label: "Экономика", tags: ["money", "jobs", "energy", "construction", "transport"] },
  { label: "Жизнь", tags: ["health", "education", "sport", "family", "weather", "culture"] }
] as const;

export interface NewsMetadataDraft {
  title: string;
  one_sentence_summary: string;
  topic: NewsTopic;
  cover_tag: CoverTag;
  is_urgent: boolean;
  is_positive: boolean;
}

interface ModerationMetadataFormProps {
  item: ProcessedNews;
  disabled: boolean;
  onSave: (newsId: number, draft: NewsMetadataDraft) => Promise<void>;
}

function defaultCoverTag(item: ProcessedNews): CoverTag {
  if (item.cover_tag) {
    return item.cover_tag;
  }
  if (item.topic === "politics") {
    return "government";
  }
  if (item.topic === "economy") {
    return "money";
  }
  return "family";
}

function draftFromItem(item: ProcessedNews): NewsMetadataDraft {
  return {
    title: item.title,
    one_sentence_summary: item.one_sentence_summary,
    topic: item.topic,
    cover_tag: defaultCoverTag(item),
    is_urgent: item.is_urgent,
    is_positive: item.is_positive
  };
}

function draftsEqual(left: NewsMetadataDraft, right: NewsMetadataDraft): boolean {
  return (
    left.title.trim() === right.title.trim() &&
    left.one_sentence_summary.trim() === right.one_sentence_summary.trim() &&
    left.topic === right.topic &&
    left.cover_tag === right.cover_tag &&
    left.is_urgent === right.is_urgent &&
    left.is_positive === right.is_positive
  );
}

export function ModerationMetadataForm({
  item,
  disabled,
  onSave
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
    const title: string = draft.title.trim();
    const oneSentenceSummary: string = draft.one_sentence_summary.trim();
    if (title.length === 0) {
      setSaveError("Заголовок не может быть пустым.");
      return;
    }
    if (oneSentenceSummary.length === 0) {
      setSaveError("Краткое описание не может быть пустым.");
      return;
    }
    setSaving(true);
    setSaveError("");
    try {
      await onSave(item.id, {
        ...draft,
        title,
        one_sentence_summary: oneSentenceSummary
      });
    } catch (error: unknown) {
      setSaveError(error instanceof Error ? error.message : "Не удалось сохранить изменения.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="moderation-metadata-form">
      <label className="moderation-metadata-field">
        <span className="moderation-metadata-field-head">
          Заголовок
          <span className="moderation-metadata-counter">
            {draft.title.length}/{TITLE_MAX_LENGTH}
          </span>
        </span>
        <input
          autoComplete="off"
          disabled={disabled || saving}
          maxLength={TITLE_MAX_LENGTH}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            setDraft((current: NewsMetadataDraft) => ({
              ...current,
              title: event.target.value
            }))
          }
          type="text"
          value={draft.title}
        />
      </label>
      <label className="moderation-metadata-field">
        <span className="moderation-metadata-field-head">
          Краткое описание
          <span className="moderation-metadata-counter">
            {draft.one_sentence_summary.length}/{SUMMARY_MAX_LENGTH}
          </span>
        </span>
        <textarea
          disabled={disabled || saving}
          maxLength={SUMMARY_MAX_LENGTH}
          onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
            setDraft((current: NewsMetadataDraft) => ({
              ...current,
              one_sentence_summary: event.target.value
            }))
          }
          rows={4}
          value={draft.one_sentence_summary}
        />
      </label>
      <div className="moderation-metadata-section">
        <p className="moderation-metadata-label">Метки перед публикацией</p>
        <NewsTopicCover coverTag={draft.cover_tag} newsId={item.id} topic={draft.topic} variant="card" />
        <label className="moderation-metadata-field">
          <span>Категория</span>
          <select
            disabled={disabled || saving}
            onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
              setDraft((current: NewsMetadataDraft) => ({
                ...current,
                topic: event.target.value as NewsTopic
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
        <label className="moderation-metadata-field">
          <span>Иллюстрация</span>
          <select
            disabled={disabled || saving}
            onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
              setDraft((current: NewsMetadataDraft) => ({
                ...current,
                cover_tag: event.target.value as CoverTag
              }))
            }
            value={draft.cover_tag}
          >
            {COVER_TAG_GROUPS.map((group: CoverTagGroup) => (
              <optgroup key={group.label} label={group.label}>
                {group.tags.map((tag: CoverTag) => (
                  <option key={tag} value={tag}>
                    {coverTagLabelRu(tag)}
                  </option>
                ))}
              </optgroup>
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
                is_urgent: event.target.checked
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
                is_positive: event.target.checked
              }))
            }
            type="checkbox"
          />
          <span>Позитивная</span>
        </label>
      </div>
      <div className="moderation-metadata-actions">
        <button disabled={disabled || saving || !isDirty} onClick={() => void handleSave()} type="button">
          {saving ? "Сохранение…" : "Сохранить"}
        </button>
        <span className={newsTopicChipClass(draft.topic)}>{newsTopicLabelRu(draft.topic)}</span>
        <span className="moderation-cover-tag-chip">{coverTagLabelRu(draft.cover_tag)}</span>
      </div>
      {saveError !== "" ? <p className="error moderation-metadata-error">{saveError}</p> : null}
    </div>
  );
}
