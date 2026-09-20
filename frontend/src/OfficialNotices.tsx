import { useEffect, useState } from 'react';
import { ArrowUpRight, Search } from 'lucide-react';
import { api } from './api/client';
import type { components } from './api/schema';

type Notices = components['schemas']['AnnouncementsView'];
const rubles = (value: string) => {
  // Decimal strings stay exact, including kopecks; do not pass amounts through Number.
  const [whole, part = ''] = value.split('.');
  return whole.replace(/\B(?=(\d{3})+(?!\d))/g, '\u00a0') + ',' + part.padEnd(2, '0') + ' ₽';
};
const date = (value: string, timeZone = 'Europe/Moscow') => new Date(value).toLocaleString('ru-RU', {
  day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit', timeZone,
});
const status: Record<string,string> = {
  ended_in_notice:'Срок в объявлении истёк',
  not_started_in_notice:'Начало по объявлению — впереди',
  within_notice_dates:'Срок по объявлению ещё не истёк',
};

export function OfficialNotices() {
  const [data,setData] = useState<Notices|null>(null);
  const [error,setError] = useState('');
  const [search,setSearch] = useState('');
  const [filter,setFilter] = useState('all');
  async function load() {
    setError('');
    try {setData(await api<Notices>('/official-announcements'));}
    catch(e) {setError((e as Error).message);}
  }
  useEffect(()=>{void load();},[]);
  if(error) return <div className="alert error" role="alert">{error}<button onClick={()=>void load()}>Повторить</button></div>;
  if(!data) return <p role="status">Загружаем официальные объявления…</p>;
  const items = data.items.filter(x => (filter==='all'||x.category===filter) &&
    `${x.title} ${x.round.code} ${x.audience}`.toLowerCase().includes(search.toLowerCase()));
  return <section>
    <div className="section-heading"><div><span className="eyebrow muted">ОФИЦИАЛЬНЫЕ ИСТОЧНИКИ • САРАТОВСКАЯ ОБЛАСТЬ</span>
      <h1>Объявления и реальные суммы</h1><p>Суммы и сроки сверены с объявлениями Минсельхоза. Для каждого отбора указаны его бюджет, предел выплаты и дата проверки.</p></div></div>
    <div className="alert">Это сведения из объявлений. Текущий приём на портале и полный набор условий участия ещё требуют проверки. Объявления пока не участвуют в персональном подборе и сохранении плана.</div>
    <div className="catalog-toolbar"><label className="search"><Search size={19}/><input aria-label="Поиск официальных объявлений" placeholder="Название, категория заявителя или шифр…" value={search} onChange={e=>setSearch(e.target.value)}/></label>
      <div className="tabs">{[['all','Все'],['grant','Гранты'],['subsidy','Субсидии']].map(([id,label])=><button key={id} className={filter===id?'selected':''} onClick={()=>setFilter(id)}>{label}</button>)}</div></div>
    <p className="result-count">Найдено: {items.length}. Бюджеты разных отборов не складываются в сумму вашей поддержки.</p>
    <div className="card-grid official-notices">{items.map(x=><article className="measure-card" key={x.round.code}>
      <div className="card-top"><span className="badge">Официальное объявление</span><span className="badge">{x.category==='grant'?'Грант':'Субсидия'}</span></div>
      <h2>{x.title}</h2><p>{x.audience}</p><p className="notice-code">Шифр: <strong>{x.round.code}</strong></p>
      <dl className="notice-money"><dt>Средства отбора на {x.funding_year} год</dt><dd>{rubles(x.budget_rub)}</dd><dt>Предел на получателя в объявлении</dt><dd>{x.recipient_limit_rub==null?'Не установлен в объявлении':rubles(x.recipient_limit_rub)}</dd></dl>
      <p className="notice-warning">{x.finance_note}</p>
      <strong>{status[x.deadline_status]}</strong><p className="notice-dates">{date(x.round.starts_at)} — {date(x.round.ends_at)} МСК<br/>В Саратове окончание: {date(x.round.ends_at,'Europe/Saratov')} (UTC+4)</p>
      <p>Приём на портале не подтверждён. Проверяйте изменения по шифру отбора.</p>
      <details><summary>Источники и что ещё нужно проверить</summary><p>Проверено: {date(x.checked_at,'Europe/Saratov')} по Саратову.</p><p>{x.legal_edition || 'Полная применимая редакция ещё проверяется.'}</p><ul>{x.missing_evidence.map((m,i)=><li key={i}>{m}</li>)}</ul>
        <p>Файл: {x.source.document}. Суммы — стр. {x.source.finance_page}; сроки — стр. {x.source.dates_page}.</p>
        <p>Скачивание источника не заменяет юридическую проверку всех условий. Перечень документов для заявки находится в официальном комплекте.</p>
      </details>
      <div className="notice-links"><a className="secondary" href={x.source.url} target="_blank" rel="noopener noreferrer">Официальный документ <ArrowUpRight size={16}/></a><a className="text-button" href={x.round.application_url} target="_blank" rel="noopener noreferrer">Проверить отбор на портале <ArrowUpRight size={16}/></a></div>
    </article>)}</div>
    {!items.length&&<p className="empty">По этому запросу объявлений нет. Измените поиск или фильтр.</p>}
  </section>;
}
