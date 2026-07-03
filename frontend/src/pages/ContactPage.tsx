import { FormEvent, useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ApiError, postFeedback } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { getLegalConfig } from "../config/legal";
import { collectFeedbackClientContext } from "../lib/feedbackContext";
import { FEEDBACK_CATEGORY_OPTIONS, type FeedbackCategory } from "../types/feedback";

export function ContactPage(): JSX.Element {
  const legal = getLegalConfig();
  const location = useLocation();
  const { user } = useAuth();

  const [category, setCategory] = useState<FeedbackCategory>("suggestion");
  const [message, setMessage] = useState<string>("");
  const [contactEmail, setContactEmail] = useState<string>("");
  const [honeypot, setHoneypot] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(false);
  const [sent, setSent] = useState<boolean>(false);

  useEffect(() => {
    if (user?.email) {
      setContactEmail(user.email);
    }
  }, [user?.email]);

  const handleSubmit = async (evt: FormEvent<HTMLFormElement>): Promise<void> => {
    evt.preventDefault();
    setError("");
    setBusy(true);
    try {
      const ctx = collectFeedbackClientContext(`${window.location.origin}${location.pathname}${location.search}`);
      await postFeedback({
        category,
        message: message.trim(),
        contact_email: contactEmail.trim().length > 0 ? contactEmail.trim().toLowerCase() : null,
        page_url: ctx.pageUrl,
        platform: ctx.platform,
        app_version: ctx.appVersion,
        website: honeypot.trim().length > 0 ? honeypot.trim() : null,
      });
      setSent(true);
      setMessage("");
      setHoneypot("");
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setError("Слишком много сообщений. Попробуйте позже.");
        } else if (err.status === 422) {
          setError("Проверьте поля формы — сообщение должно быть не короче 10 символов.");
        } else if (err.status === 503) {
          setError(
            legal.contactEmail
              ? `Сервис временно недоступен. Напишите на ${legal.contactEmail}.`
              : "Сервис временно недоступен. Используйте email из раздела ниже.",
          );
        } else {
          setError(err.message);
        }
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Не удалось отправить сообщение.");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="legal-page">
      <h1>Контакты</h1>
      <p className="muted">
        По вопросам работы приложения, содержания ленты и запросам по персональным данным свяжитесь с
        оператором сервиса.
      </p>

      <h2>Обратная связь</h2>
      <p className="muted">
        Сообщите об ошибке или предложите улучшение — мы читаем все обращения. Email для ответа необязателен.
      </p>

      {sent ? (
        <div className="feedback-form-card feedback-form-success" role="status">
          <p>Спасибо! Сообщение отправлено.</p>
          <button
            className="feedback-form-secondary"
            onClick={() => {
              setSent(false);
            }}
            type="button"
          >
            Отправить ещё
          </button>
        </div>
      ) : (
        <form className="feedback-form-card" onSubmit={(e) => void handleSubmit(e)}>
          <label className="field-label" htmlFor="feedback-category">
            Тип сообщения
          </label>
          <select
            className="feedback-form-field"
            id="feedback-category"
            onChange={(e) => {
              setCategory(e.target.value as FeedbackCategory);
            }}
            value={category}
          >
            {FEEDBACK_CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          <label className="field-label" htmlFor="feedback-message">
            Сообщение
          </label>
          <textarea
            className="feedback-form-field feedback-form-textarea"
            id="feedback-message"
            maxLength={4000}
            minLength={10}
            name="message"
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Опишите проблему или идею…"
            required
            rows={5}
            value={message}
          />

          <label className="field-label" htmlFor="feedback-email">
            Email для ответа <span className="muted">(необязательно)</span>
          </label>
          <input
            autoComplete="email"
            className="feedback-form-field"
            id="feedback-email"
            inputMode="email"
            maxLength={254}
            name="contact_email"
            onChange={(e) => setContactEmail(e.target.value)}
            spellCheck={false}
            type="email"
            value={contactEmail}
          />

          <div aria-hidden="true" className="feedback-form-honeypot">
            <label htmlFor="feedback-website">Website</label>
            <input
              autoComplete="off"
              id="feedback-website"
              name="website"
              onChange={(e) => setHoneypot(e.target.value)}
              tabIndex={-1}
              type="text"
              value={honeypot}
            />
          </div>

          {error !== "" ? <p className="error">{error}</p> : null}

          <button className="feedback-form-submit" disabled={busy} type="submit">
            {busy ? "Отправка…" : "Отправить"}
          </button>

          <p className="muted feedback-form-note">
            Если указан email, мы используем его только для ответа на это обращение.
          </p>
        </form>
      )}

      <h2>E-mail</h2>
      {legal.contactEmail ? (
        <p>
          <a href={`mailto:${legal.contactEmail}`}>{legal.contactEmail}</a>
        </p>
      ) : (
        <p className="legal-warning">
          Укажите <code>VITE_LEGAL_CONTACT_EMAIL</code> в frontend/.env перед публикацией в магазине
          приложений.
        </p>
      )}

      <h2>Оператор</h2>
      {legal.operatorComplete ? (
        <p>
          {legal.operatorName}, {legal.operatorStreet}, {legal.operatorPostalCity}
        </p>
      ) : (
        <p className="legal-warning">Заполните поля VITE_LEGAL_OPERATOR_* в frontend/.env.</p>
      )}

      <p className="muted">
        Правовая информация: <Link to="/impressum">Impressum</Link> ·{" "}
        <Link to="/privacy">Конфиденциальность</Link>
      </p>
    </section>
  );
}
