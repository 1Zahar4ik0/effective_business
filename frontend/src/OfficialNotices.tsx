import { OfficialEvidence } from "./OfficialEvidence";
import { useEffect, useState } from "react";
import { ArrowUpRight, Search } from "lucide-react";
import { api } from "./api/client";
import type { components } from "./api/schema";
type Notices = components["schemas"]["AnnouncementsView"];
const formatRubles = (value: string) => {
  const [whole, part = ""] = value.split(".");
  return whole.replace(/\B(?=(\d{3})+(?!\d))/g, "\u00a0") + "," + part.padEnd(2, "0") + " ₽";
};
const formatDate = (value: string, timeZone = "Europe/Moscow") =>
  new Date(value).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone,
  });
const deadlineLabels: Record<string, string> = {
  ended_in_notice: "Срок в объявлении истёк",
  not_started_in_notice: "Начало по объявлению — впереди",
  within_notice_dates: "Срок по объявлению ещё не истёк",
};
export function OfficialNotices() {
  const [data, setData] = useState<Notices | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  async function load() {
    setError("");
    try {
      setData(await api<Notices>("/official-announcements"));
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    void load();
  }, []);
  if (error)
    return (
      <div className="alert error" role="alert">
        {error}
        <button onClick={() => void load()}>Повторить</button>
      </div>
    );
  if (!data) return <p role="status">Загружаем официальные объявления…</p>;
  const query = search.toLowerCase();
  const items = data.items.filter((notice) => {
    const matchesCategory = filter === "all" || notice.category === filter;
    const searchableText = `${notice.title} ${notice.round.code} ${notice.audience}`;
    const matchesSearch = searchableText.toLowerCase().includes(query);
    return matchesCategory && matchesSearch;
  });
  return (
    <section>
      <div className="section-heading">
        <div>
          <h1>Официальные объявления</h1>
          <p>
            Суммы и сроки сверены с объявлениями Минсельхоза. Для каждого отбора указаны его бюджет,
            предел выплаты и дата проверки.
          </p>
        </div>
      </div>
      <div className="alert">
        Суммы, сроки и документы приведены для конкретных отборов. Этот раздел предназначен для
        просмотра объявлений; персональный подбор доступен отдельно для опубликованных условий.
      </div>
      <OfficialEvidence />
      <div className="catalog-toolbar">
        <label className="search">
          <Search size={19} />
          <input
            aria-label="Поиск официальных объявлений"
            placeholder="Название, категория заявителя или шифр…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <div className="tabs">
          {[
            ["all", "Все"],
            ["grant", "Гранты"],
            ["subsidy", "Субсидии"],
          ].map(([id, label]) => (
            <button
              key={id}
              className={filter === id ? "selected" : ""}
              onClick={() => setFilter(id)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <p className="result-count">
        Найдено: {items.length}. Бюджеты разных отборов не складываются в сумму вашей поддержки.
      </p>
      <div className="card-grid official-notices">
        {items.map((notice) => (
          <NoticeCard key={notice.round.code} notice={notice} />
        ))}
      </div>
      {!items.length && (
        <p className="empty">По этому запросу объявлений нет. Измените поиск или фильтр.</p>
      )}
    </section>
  );
}


type Notice = Notices["items"][number];

function NoticeCard({ notice }: { notice: Notice }) {
  return (
    <article className="measure-card">
      <div className="card-top">
        <span className="badge">Официальное объявление</span>
        <span className="badge">{notice.category === "grant" ? "Грант" : "Субсидия"}</span>
      </div>
      <h2>{notice.title}</h2>
      <p>{notice.audience}</p>
      <p className="notice-code">
        Шифр: <strong>{notice.round.code}</strong>
      </p>
      <dl className="notice-money">
        <dt>Средства отбора на {notice.funding_year} год</dt>
        <dd>{formatRubles(notice.budget_rub)}</dd>
        <dt>Предел на получателя в объявлении</dt>
        <dd>
          {notice.recipient_limit_rub == null
            ? "Не установлен в объявлении"
            : formatRubles(notice.recipient_limit_rub)}
        </dd>
      </dl>
      <p className="notice-warning">{notice.finance_note}</p>
      <strong>{deadlineLabels[notice.deadline_status]}</strong>
      <p className="notice-dates">
        {formatDate(notice.round.starts_at)} — {formatDate(notice.round.ends_at)} МСК
        <br />В Саратове окончание: {formatDate(notice.round.ends_at, "Europe/Saratov")} (UTC+4)
      </p>
      <p>Актуальный статус приёма смотрите на официальном портале по шифру отбора.</p>
      <details>
        <summary>Источники и ограничения применения</summary>
        <p>Проверено: {formatDate(notice.checked_at, "Europe/Saratov")} по Саратову.</p>
        <p>{notice.legal_edition || "Полная применимая редакция ещё проверяется."}</p>
        <ul>
          {notice.missing_evidence.map((missingEvidence, index) => (
            <li key={index}>{missingEvidence}</li>
          ))}
        </ul>
        <p>
          Файл: {notice.source.document}. Суммы — стр. {notice.source.finance_page}; сроки — стр.{" "}
          {notice.source.dates_page}.
        </p>
        <p>
          Скачивание источника не заменяет юридическую проверку всех условий. Перечень
          документов для заявки находится в официальном комплекте.
        </p>
      </details>
      <div className="notice-links">
        <a
          className="secondary"
          href={notice.source.url}
          target="_blank"
          rel="noopener noreferrer"
        >
          Официальный документ <ArrowUpRight size={16} />
        </a>
        <a
          className="text-button"
          href={notice.round.application_url}
          target="_blank"
          rel="noopener noreferrer"
        >
          Проверить отбор на портале <ArrowUpRight size={16} />
        </a>
      </div>
    </article>
  );
}
