import { useEffect, useState } from "react";
import { getFeedPreferences, putFeedPreferences } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { COVER_TAGS, coverTagLabelRu, type CoverTag } from "../types/news";

export function AccountInterests(): JSX.Element {
  const { withAccountAccess } = useAuth();
  const [selected, setSelected] = useState<CoverTag[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let cancelled: boolean = false;
    void withAccountAccess((accessToken: string) => getFeedPreferences(accessToken))
      .then((body) => {
        if (!cancelled) {
          setSelected(body.interests);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("Не удалось загрузить темы.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [withAccountAccess]);

  const toggle = (tag: CoverTag): void => {
    if (saving) {
      return;
    }
    const previous: CoverTag[] = selected;
    const next: CoverTag[] = selected.includes(tag)
      ? selected.filter((item: CoverTag) => item !== tag)
      : [...selected, tag];
    setSelected(next);
    setSaving(true);
    setError("");
    void withAccountAccess((accessToken: string) => putFeedPreferences(accessToken, next))
      .then((body) => {
        setSelected(body.interests);
      })
      .catch(() => {
        setSelected(previous);
        setError("Не удалось сохранить темы.");
      })
      .finally(() => {
        setSaving(false);
      });
  };

  return (
    <div className="account-interests">
      <h2>Темы ленты</h2>
      <p className="muted">
        Включите, что хотите видеть раньше. Остальные новости остаются ниже. Пустой выбор оставляет ленту как есть.
      </p>
      {loading ? <p className="loading-inline">Загрузка тем…</p> : null}
      <div className="account-interest-list" role="group" aria-label="Темы ленты">
        {COVER_TAGS.map((tag: CoverTag) => {
          const on: boolean = selected.includes(tag);
          return (
            <button
              key={tag}
              type="button"
              className={on ? "account-interest-chip is-on" : "account-interest-chip"}
              aria-pressed={on}
              disabled={loading || saving}
              onClick={() => {
                toggle(tag);
              }}
            >
              {coverTagLabelRu(tag)}
            </button>
          );
        })}
      </div>
      {error !== "" ? <p className="error">{error}</p> : null}
    </div>
  );
}
