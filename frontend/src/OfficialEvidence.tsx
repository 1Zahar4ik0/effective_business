import evidence from "../public/official/20260929/manifest.json";

function formatGrantAmount(amount: string) {
  const [rubles, kopecks = "00"] = amount.split(".");
  const groupedRubles = rubles.replace(/\B(?=(\d{3})+(?!\d))/g, "\u00a0");
  if (kopecks === "00") return `${groupedRubles} ₽`;
  return `${groupedRubles},${kopecks} ₽`;
}

type Grant = (typeof evidence.grant_limits)[number];

function GrantCard({ grant }: { grant: Grant }) {
  return (
    <article className="measure-card">
      <h3>{grant.title}</h3>
      <dl>
        {grant.rows.map((row) => (
          <div key={row.amount} className="evidence-limit">
            <dt>{row.condition}</dt>
            <dd>До {formatGrantAmount(row.amount)}</dd>
          </div>
        ))}
      </dl>
      <p>{grant.reference}. Приказ 186-пр от 08.07.2026.</p>
      <a href="/official/20260929/186-pr.pdf" target="_blank" rel="noopener noreferrer">
        Открыть документ (PDF)
      </a>
    </article>
  );
}

export function OfficialEvidence() {
  return (
    <section className="official-evidence" aria-labelledby="evidence-title">
      <h2 id="evidence-title">Размеры грантов и документы</h2>
      <p>
        Положения присланных нормативных документов сверены 29 сентября 2026 года.
        Это пределы по приказу, а не обещание выплаты или подтверждение открытого приёма.
      </p>
      <div className="card-grid">
        {evidence.grant_limits.map((grant) => <GrantCard key={grant.id} grant={grant} />)}
      </div>
      <p className="alert">
        «Агропрогресс» исключает КФХ, ИП — глав КФХ, ЛПХ и сельхозпотребкооперативы.
        Основание: <a href="/official/20260929/622-p.pdf" target="_blank" rel="noopener noreferrer">
          622-П, страница 1, пункт 6
        </a>.
        Для КФХ рассматривайте отдельный фермерский грант; остальные требования также должны выполняться.
      </p>
      <details className="evidence-documents">
        <summary>Первоисточники и область проверки — {evidence.documents.length} документов</summary>
        <p>
          PDF — сохранённые копии предоставленных документов.
          Ссылки на публикации нужны для проверки последующих изменений.
        </p>
        {evidence.documents.map((document) => (
          <article key={document.id}>
            <h3>{document.title}</h3>
            <p>{document.scope}</p>
            <p>
              <a href={document.file} target="_blank" rel="noopener noreferrer">
                PDF · {document.pages} стр.
              </a>{" · "}
              <a href={document.original_url} target="_blank" rel="noopener noreferrer">
                Официальный источник
              </a>
            </p>
          </article>
        ))}
        <a href="/official/20260929/manifest.json" target="_blank" rel="noopener noreferrer">
          Реестр файлов и контрольные суммы
        </a>
      </details>
    </section>
  );
}
