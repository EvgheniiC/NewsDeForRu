import { AnalyticsRevokeButton } from "../../components/AnalyticsRevokeButton";
import { LegalOperatorBlock } from "../../components/LegalOperatorBlock";
import { getLegalConfig } from "../../config/legal";

export function PrivacyContentRu(): JSX.Element {
  const legal = getLegalConfig();

  return (
    <>
      <h1>Политика конфиденциальности</h1>
      <p className="muted">
        Версия: август 2026 · GDPR (DSGVO), TTDSG · Сервис:{" "}
        <a href={legal.publicAppBaseUrl}>{legal.publicAppBaseUrl}</a>
      </p>

      <h2>1. Оператор персональных данных</h2>
      <LegalOperatorBlock detail="compact" locale="ru" />
      <p>Запросы по персональным данным направляйте на указанный выше e-mail.</p>

      <h2>2. Краткий обзор</h2>
      <ul>
        <li>Чтение ленты без регистрации; технические логи на сервере в {legal.hostingCountry}.</li>
        <li>
          Опциональный аккаунт: e-mail, хеш пароля, JWT в localStorage (<code>newsfr.auth.*</code>).
        </li>
        <li>
          Аналитика использования — только после согласия в баннере (псевдонимные ID,{" "}
          <code>/engagement/events</code>).
        </li>
        <li>
          Пайплайн: RSS и БД в Германии; тексты через OpenAI (США); при включении — Telegram.
        </li>
      </ul>

      <h2>3. Цели и правовые основания (ст. 6 GDPR)</h2>
      <div className="legal-table-wrap">
        <table className="legal-table">
          <thead>
            <tr>
              <th>Данные</th>
              <th>Цель</th>
              <th>Основание</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Логи сервера (время, путь, статус; без секретов)</td>
              <td>Работа и безопасность</td>
              <td>Законный интерес (f)</td>
            </tr>
            <tr>
              <td>RSS, статьи, embeddings (БД в DE)</td>
              <td>Новостной пайплайн</td>
              <td>Законный интерес (f)</td>
            </tr>
            <tr>
              <td>OpenAI API (gpt-4o-mini)</td>
              <td>Сводка, перевод</td>
              <td>f; передача в США — SCC</td>
            </tr>
            <tr>
              <td>Telegram Bot API</td>
              <td>Уведомления в канал</td>
              <td>Законный интерес (f)</td>
            </tr>
            <tr>
              <td>Аккаунт: e-mail, хеш, refresh-токен</td>
              <td>Вход, сброс пароля</td>
              <td>Договор (b)</td>
            </tr>
            <tr>
              <td>GMX SMTP (mail.gmx.net)</td>
              <td>Письмо со ссылкой сброса</td>
              <td>Договор (b)</td>
            </tr>
            <tr>
              <td>
                <code>nga_anonymous_user_id</code>, <code>nga_session_id</code>, события
              </td>
              <td>Статистика использования</td>
              <td>Согласие (a), баннер</td>
            </tr>
            <tr>
              <td>JWT, локально «полезно»</td>
              <td>Сессия / отображение</td>
              <td>b / f; на сервер — только с согласием</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h2>4. Баннер согласия — что происходит?</h2>
      <ul>
        <li>
          <strong>На сервере мы не храним</strong>, кто нажал «принять» или «отклонить». Нет реестра
          пользователей согласия. Только ваш браузер сохраняет <code>nga_analytics_consent</code> (
          <code>granted</code> или <code>denied</code>) и при необходимости{" "}
          <code>nga_analytics_consent_at</code> (время выбора).
        </li>
        <li>
          <strong>Принять:</strong> можно записать псевдонимные ID и отправлять агрегированные события
          (открытие статей, «полезно») на сервер в Германии.
        </li>
        <li>
          <strong>Отклонить:</strong> лента и аккаунт работают как обычно;{" "}
          <strong>аналитика не отправляется</strong>, постоянный анонимный ID не сохраняется.
        </li>
        <li>
          <strong>Отозвать согласие:</strong> кнопка ниже — аналитика прекращается, баннер снова
          предложит выбор; или удалите ключи в браузере.
        </li>
      </ul>
      <AnalyticsRevokeButton locale="ru" />

      <h2>5. Сроки хранения</h2>
      <ul>
        <li>Логи сервера: до ~90 дней.</li>
        <li>События engagement: 12 месяцев.</li>
        <li>Аккаунт: до удаления; refresh-токен до 14 дней.</li>
        <li>Токен сброса пароля: 60 минут.</li>
      </ul>

      <h2>6. Обработчики (субподрядчики)</h2>
      <ul>
        <li>Хостинг / БД — {legal.hostingCountry}.</li>
        <li>OpenAI (США), Telegram, GMX.</li>
        <li>Sentry / Prometheus — сейчас выключены.</li>
      </ul>

      <h2>7. Ваши права</h2>
      <p>
        Доступ, исправление, удаление, ограничение, возражение, отзыв согласия. Жалоба в надзорный орган
        (для Германии — земельный орган, например{" "}
        <a
          href="https://lfd.niedersachsen.de/startseite/themen/datenschutz/"
          rel="noopener noreferrer"
          target="_blank"
        >
          LfD Niedersachsen
        </a>
        ).
      </p>

      <h2>8. Автоматическая публикация</h2>
      <p>Обработка RSS с помощью ИИ; профилирование читателей не проводится.</p>

      <h2>9. Дети</h2>
      <p>Сервис не предназначен для лиц младше 16 лет.</p>
    </>
  );
}
