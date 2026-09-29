import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight,
  ArrowUpRight,
  Bookmark,
  Check as CheckIcon,
  ChevronLeft,
  CircleHelp,
  ClipboardList,
  Compass,
  FileCheck2,
  Leaf,
  LogOut,
  Search,
  Settings2,
  ShieldCheck,
  Sprout,
  X,
} from "lucide-react";
import {
  api,
  ApiError,
  setSession,
  type Session,
  type Measure,
  type Profile,
  type Match,
  type Plan,
  type Check,
  type ProfileQuestion,
} from "./api/client";
import "./style.css";
import { OfficialNotices } from "./OfficialNotices";
const statusName: Record<string, string> = {
  PASS: "Соответствует ответам анкеты",
  UNKNOWN: "Нужно уточнить",
  FAIL: "Есть ограничения",
};
const availabilityName: Record<string, string> = {
  open: "Приём открыт",
  closed: "Приём завершён",
  scheduled: "Приём скоро",
  unknown: "Доступность подачи не подтверждена",
  suspended: "Приём приостановлен",
  cancelled: "Отбор отменён",
};
const categoryName: Record<string, string> = {
  grant: "Грант",
  subsidy: "Субсидия",
  consultation: "Консультация",
};
const stateName: Record<string, string> = {
  draft: "Черновик",
  review: "На проверке",
  published: "Опубликована",
  archived: "Архив",
};
const date = (value?: string | null, zone = "Europe/Saratov") =>
  value
    ? new Date(value).toLocaleString("ru-RU", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: zone,
      })
    : "Не проверено";
const example: Profile = {
  registration_region: "64",
  activity_region: "64",
  legal_form: "ip",
  is_kfh: true,
  tax_regime: "eshn",
  sector: "crops",
  goal: "equipment",
  expense_stage: "planned",
  years_active: 2,
  own_funds: "450000",
  is_sme: true,
  special_category: null,
};
type Page = "home" | "profile" | "results" | "catalog" | "plans" | "editor";
type Config = {
  demo: boolean;
  max_configured: boolean;
  max_app_url?: string | null;
};
declare global {
  interface Window {
    WebApp?: {
      initData?: string;
      ready?: () => void;
    };
  }
}
function Badge({ kind, children }: { kind?: string; children: React.ReactNode }) {
  return <span className={"badge " + (kind || "")}>{children}</span>;
}
function Empty({ children }: { children: React.ReactNode }) {
  return (
    <div className="empty">
      <Sprout size={36} />
      <p>{children}</p>
    </div>
  );
}
function App() {
  const [session, updateSession] = useState<Session | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [page, setPage] = useState<Page>("home");
  const [catalogMode, setCatalogMode] = useState<"official" | "published">("official");
  const [catalog, setCatalog] = useState<Measure[]>([]);
  const [profile, setProfile] = useState<Profile>({});
  const [questions, setQuestions] = useState<ProfileQuestion[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [detail, setDetail] = useState<Measure | null>(null);
  const [planRoundId, setPlanRoundId] = useState<string | undefined>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  function accept(s: Session | null) {
    updateSession(s);
    setSession(s);
  }
  async function run(task: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await task();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function loadPersonal() {
    const [p, ps] = await Promise.all([
      api<Profile>("/profile"),
      api<Plan[]>("/preparation-plans"),
    ]);
    setProfile(p);
    setPlans(ps);
  }
  async function login(persona = "farmer") {
    await run(async () => {
      accept(await api<Session>("/auth/demo", "POST", { persona }));
      await loadPersonal();
      setPage("home");
      setMatches([]);
    });
  }
  async function openFarmExample() {
    if (!config?.demo) return;
    await run(async () => {
      if (!session?.user.demo) {
        accept(await api<Session>("/auth/demo", "POST", { persona: "farmer" }));
        await loadPersonal();
      }
      setProfile({ ...example });
      setMatches([]);
      navigate("profile");
      setNotice("Учебный пример заполнен, но ещё не сохранён. Нажмите «Сохранить и подобрать»: грант «Развитие фермерского хозяйства» должен предварительно подойти.");
    });
  }
  useEffect(() => {
    void run(async () => {
      const c = await api<Config>("/config");
      setConfig(c);
      setCatalog(await api<Measure[]>("/catalog"));
      setQuestions(await api<ProfileQuestion[]>("/profile/questions"));
      const launchParams = new URLSearchParams(window.location.hash.slice(1));
      const launchedInMax = Boolean(window.WebApp) || launchParams.has("WebAppData");
      if (c.max_configured && launchedInMax && !window.WebApp) {
        if (launchParams.getAll("WebAppData").length !== 1)
          throw new Error("Некорректные параметры запуска MAX");
        await new Promise<void>((resolve, reject) => {
          const script = document.createElement("script");
          script.src = "https://st.max.ru/js/max-web-app.js";
          script.onload = () => resolve();
          script.onerror = () => reject(new Error("Не удалось загрузить MAX Bridge"));
          document.head.appendChild(script);
        });
      }
      let signedIn = false;
      try {
        accept(await api<Session>("/auth/me"));
        signedIn = true;
      } catch (e) {
        if (!(e instanceof ApiError) || e.status !== 401) throw e;
        if (c.max_configured && window.WebApp?.initData) {
          accept(await api<Session>("/auth/max", "POST", { init_data: window.WebApp.initData }));
          signedIn = true;
        }
      }
      if (signedIn) await loadPersonal();
      window.WebApp?.ready?.();
    });
  }, []);
  function navigate(p: Page) {
    setPage(p);
    setDetail(null);
    setNotice("");
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  async function match() {
    await run(async () => {
      await api("/profile", "PUT", profile);
      const data = await api<{
        results: Match[];
      }>("/matches", "POST");
      setMatches(data.results);
      setPlans(await api<Plan[]>("/preparation-plans"));
      navigate("results");
    });
  }
  function openAnnouncements() {
    setCatalogMode("official");
    navigate("catalog");
  }
  async function savePlan(round_id: string) {
    await run(async () => {
      await api("/preparation-plans", "POST", { round_id });
      setPlans(await api<Plan[]>("/preparation-plans"));
      setDetail(null);
      navigate("plans");
      setNotice("План сохранён. Отмечайте готовые документы — прогресс останется после входа.");
    });
  }
  const nav: {
    id: Page;
    label: string;
    icon: React.ReactNode;
  }[] = [
    { id: "home", label: "Обзор", icon: <Compass size={20} /> },
    { id: "profile", label: "Моё хозяйство", icon: <Sprout size={20} /> },
    { id: "catalog", label: "Каталог поддержки", icon: <Search size={20} /> },
    { id: "plans", label: "Мои планы", icon: <Bookmark size={20} /> },
  ];
  if (session?.user.role === "editor")
    nav.push({ id: "editor", label: "Редактор", icon: <Settings2 size={20} /> });
  return (
    <div className="app">
      <aside className="sidebar">
        <a
          href="#"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            navigate("home");
          }}
        >
          <span className="brand-symbol">
            <Sprout />
          </span>
          <span>
            опора<span className="brand-apk">АПК</span>
          </span>
        </a>
        <nav aria-label="Основная навигация">
          {nav.map((n) => (
            <button
              key={n.id}
              className={"nav-item " + (page === n.id ? "active" : "")}
              onClick={() => navigate(n.id)}
            >
              {n.icon}
              <span>{n.label}</span>
              {n.id === "plans" && plans.length > 0 && <b>{plans.length}</b>}
            </button>
          ))}
        </nav>
        <div className="side-note">
          <ShieldCheck size={24} />
          <strong>Понятный путь к поддержке</strong>
          <p>От условий участия до списка документов и официального портала.</p>
        </div>
        <div className="account">
          <div className="avatar">{session?.user.role === "editor" ? "Р" : "Ф"}</div>
          <div>
            <strong>{session?.user.name || "Гость"}</strong>
            <small>
              {session
                ? session.user.demo
                  ? "Локальная демонстрация"
                  : ""
                : "Войдите, чтобы сохранить план"}
            </small>
          </div>
          {session && (
            <button
              className="icon-button"
              aria-label="Выйти"
              onClick={() =>
                void run(async () => {
                  await api("/auth/logout", "POST");
                  accept(null);
                  setPlans([]);
                  setProfile({});
                  setMatches([]);
                  navigate("home");
                })
              }
            >
              <LogOut size={17} />
            </button>
          )}
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span>
            <i className="dot" /> Саратовская область
          </span>
          {config?.demo && <Badge>Локальная версия</Badge>}
          {session && (
            <button
              className="icon-button mobile-logout"
              aria-label="Выйти из аккаунта"
              onClick={() =>
                void run(async () => {
                  await api("/auth/logout", "POST");
                  accept(null);
                  setPlans([]);
                  setProfile({});
                  setMatches([]);
                  navigate("home");
                })
              }
            >
              <LogOut size={17} />
            </button>
          )}
        </header>
        {config?.demo && (
          <div className="demo-banner">
            <CircleHelp size={16} />
            <span>
              <b>Локальный учебный вход.</b> Не вводите персональные данные. Реальные объявления и
              суммы — в каталоге. Подбор пока использует учебные меры; полные условия реальных мер
              проверяются.
            </span>
          </div>
        )}
        <main>
          {error && (
            <div className="alert error" role="alert">
              {error}
              <button onClick={() => setError("")} aria-label="Закрыть ошибку">
                <X size={17} />
              </button>
            </div>
          )}
          {notice && (
            <div className="alert success" role="status">
              {notice}
            </div>
          )}
          {busy && (
            <div className="loading" role="status">
              Сохраняем и проверяем…
            </div>
          )}
          {!session && (
            <section className="login-strip">
              <div>
                <strong>{config?.demo ? "Попробуйте путь фермера" : "Вход через MAX"}</strong>
                <p>
                  {config?.demo
                    ? "Общие учебные аккаунты. Не вводите персональные данные."
                    : "Откройте приложение через настроенного бота MAX для входа."}
                </p>
              </div>
              {!config?.demo && config?.max_app_url && (
                <a
                  className="primary"
                  href={config.max_app_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Открыть в MAX <ArrowUpRight size={17} />
                </a>
              )}
              {config?.demo && (
                <div className="actions">
                  <button disabled={busy} className="primary" onClick={() => void login()}>
                    Войти как фермер <ArrowRight size={17} />
                  </button>
                  <button
                    disabled={busy}
                    className="secondary"
                    onClick={() => void login("editor")}
                  >
                    Вход редактора
                  </button>
                </div>
              )}
            </section>
          )}
          {page === "home" && (
            <>
              <section className="hero">
                <div className="hero-copy">
                  <h1>
                    Найдите поддержку.
                    <br />
                    <em>Спланируйте развитие.</em>
                  </h1>
                  <p>
                    Расскажите о хозяйстве — мы сопоставим условия мер, объясним результат и поможем
                    подготовить документы.
                  </p>
                  <button
                    className="primary light"
                    disabled={!session || busy}
                    onClick={() => navigate("profile")}
                  >
                    Подобрать поддержку <ArrowRight size={19} />
                  </button>
                  <small>Короткая анкета · Можно отвечать «Не знаю»</small>
                </div>
                <div className="hero-art" aria-hidden="true">
                  <div className="sun" />
                  <div className="hill h1" />
                  <div className="hill h2" />
                  <div className="hill h3" />
                  <Sprout className="hero-sprout" />
                  <div className="art-label">
                    <Leaf size={15} /> Идея → План → Развитие
                  </div>
                </div>
              </section>
              <section className="steps">
                <div>
                  <span>01</span>
                  <strong>Расскажите о себе</strong>
                  <p>Регион, хозяйство и цель проекта</p>
                </div>
                <div>
                  <span>02</span>
                  <strong>Разберитесь в условиях</strong>
                  <p>Понятные причины подбора</p>
                </div>
                <div>
                  <span>03</span>
                  <strong>Подготовьте документы</strong>
                  <p>Личный план и маршрут подачи</p>
                </div>
              </section>
              <div className="section-heading">
                <div>
                  <h2>Как работает подбор</h2>
                  <p>
                    {config?.demo
                      ? "Ниже — учебные примеры. Реальные объявления с суммами доступны в каталоге."
                      : catalog.length
                        ? "Опубликованные меры с условиями участия и документами."
                        : "Реальные объявления с суммами и сроками доступны в каталоге. Условия персонального подбора ещё проверяются."}
                  </p>
                </div>
                <button className="text-button" onClick={() => navigate("catalog")}>
                  Весь каталог <ArrowRight size={16} />
                </button>
              </div>
              <div className="card-grid">
                {catalog.slice(0, 3).map((m) => (
                  <MeasureCard key={m.id} m={m} onOpen={() => setDetail(m)} />
                ))}
              </div>
              <section className="info-strip">
                <ShieldCheck />
                <div>
                  <strong>Вы видите причину, а не обещание</strong>
                  <p>
                    Соответствие анкете не гарантирует получение поддержки. Решение принимает
                    организатор отбора.
                  </p>
                </div>
              </section>
            </>
          )}
          {page === "profile" && session && !session.user.demo && (
            <details className="evidence-documents">
              <summary>Мой ID для настройки доступа</summary>
              <p>MAX ID: <code>{session.user.id.replace(/^max:/, "")}</code></p>
              <p>Этот идентификатор виден только вам. Передайте его администратору для назначения редактора. Токен бота не нужен.</p>
            </details>
          )}
          {config?.demo && page === "home" && (
            <section className="alert">
              <strong>Проверить подбор на готовом примере</strong>
              <p>КФХ в Саратовской области, покупка оборудования, собственные средства 450 000 ₽.
                Учебные условия позволяют проверить подбор и сохранение плана.</p>
              <button className="secondary" disabled={busy} onClick={() => void openFarmExample()}>
                Заполнить учебный пример КФХ
              </button>
              <p>Кнопка заменит ответы в форме; сохранение выполняется отдельно.</p>
            </section>
          )}
          {page === "profile" && config && !config.demo && catalog.length === 0 && (
            <div className="alert" role="status">
              <strong>Подбор по реальным мерам ещё не готов</strong>
              <p>В каталоге нет опубликованных условий для проверки анкеты. Ответы можно сохранить,
                но изменение суммы, цели или формы хозяйства пока не даст результат подбора.</p>
              <button className="text-button" onClick={openAnnouncements}>Открыть официальные объявления</button>
            </div>
          )}
          {page === "profile" &&
            (session ? (
              <Questionnaire
                demo={!!config?.demo}
                questions={questions}
                profile={profile}
                setProfile={setProfile}
                submit={match}
                busy={busy}
              />
            ) : (
              <Empty>{config?.demo ? "Для сохранения анкеты войдите в демонстрационный аккаунт." : "Для сохранения анкеты откройте приложение через бота MAX."}</Empty>
            ))}
          {page === "catalog" && (
            <>
              <div className="tabs catalog-mode">
                <button
                  className={catalogMode === "official" ? "selected" : ""}
                  onClick={() => setCatalogMode("official")}
                >
                  Реальные объявления
                </button>
                <button
                  className={catalogMode === "published" ? "selected" : ""}
                  onClick={() => setCatalogMode("published")}
                >
                  Меры и подготовка
                </button>
              </div>
              {catalogMode === "official" ? (
                <OfficialNotices />
              ) : (
                <Catalog catalog={catalog} onOpen={setDetail} onEdit={() => navigate("profile")} onAnnouncements={openAnnouncements} />
              )}
            </>
          )}
          {page === "results" && (
            <Catalog
              catalog={catalog}
              matches={matches}
              onAnnouncements={openAnnouncements}
              onOpen={setDetail}
              onEdit={() => navigate("profile")}
            />
          )}
          {page === "plans" && (
            <>
              <div className="section-heading">
                <div>
                  <h1>Мои планы</h1>
                  <p>Ваш список подготовки. Отметки не являются официальным статусом заявки.</p>
                </div>
              </div>
              {plans.length === 0 ? (
                <Empty>
                  Пока нет планов. Откройте меру в каталоге и сохраните план подготовки.
                </Empty>
              ) : (
                plans.map((p) => (
                  <section className="plan-panel" key={p.id}>
                    <div className="section-heading">
                      <div>
                        <Badge>Версия условий {p.measure.version}</Badge>
                        <h2>{p.measure.title}</h2>
                      </div>
                      <span className="plan-count">
                        {p.items.filter((i) => i.done).length} / {p.items.length}
                      </span>
                    </div>
                    <progress value={p.items.filter((i) => i.done).length} max={p.items.length} />
                    {p.needs_review && (
                      <div className="alert">
                        Условия изменились или сняты с публикации. Старый план сохранён. Проверьте
                        актуальную карточку перед продолжением.
                        <button
                          className="text-button"
                          onClick={() =>
                            void run(async () =>
                              setDetail(await api<Measure>("/measures/" + p.measure.id)),
                            )
                          }
                        >
                          Проверить новую версию
                        </button>
                      </div>
                    )}
                    <PlanCheck plan={p} onEdit={() => navigate("profile")} />
                    <div className="document-list">
                      {p.items.map((i) => (
                        <label key={i.id} className={"document " + (i.done ? "done" : "")}>
                          <input
                            type="checkbox"
                            checked={i.done}
                            disabled={busy}
                            onChange={() =>
                              void run(async () => {
                                const updated = await api<Plan>(
                                  `/preparation-plans/${p.id}/items/${i.id}`,
                                  "PATCH",
                                  { done: !i.done, revision: p.revision },
                                );
                                setPlans(plans.map((x) => (x.id === p.id ? updated : x)));
                              })
                            }
                          />
                          <span>
                            <strong>{i.title}</strong>
                            <small>{i.hint}</small>
                            {i.applicability && <small>{documentStatus[i.applicability]}</small>}
                            {i.check && <small>{i.check.label} · {i.check.source_ref}</small>}
                          </span>
                        </label>
                      ))}
                    </div>
                    <div className="plan-footer">
                      <small>Сохранён {date(p.created_at)}</small>
                      <button
                        className="secondary"
                        onClick={() => {
                          setPlanRoundId(p.round_id);
                          setDetail(p.measure);
                        }}
                      >
                        Карточка и маршрут подачи <ArrowUpRight size={16} />
                      </button>
                    </div>
                  </section>
                ))
              )}
            </>
          )}
          {page === "editor" && session?.user.role === "editor" && (
            <>
              <NewMeasureComposer demo={!!config?.demo} run={run} />
              <Editor
                run={run}
                busy={busy}
                refresh={async () => {
                  setCatalog(await api<Measure[]>("/catalog"));
                  setQuestions(await api<ProfileQuestion[]>("/profile/questions"));
                }}
              />
            </>
          )}
          <footer>Опора АПК</footer>
        </main>
      </div>
      {detail && (
        <Detail
          selectedRoundId={page === "plans" ? planRoundId : undefined}
          measure={detail}
          match={matches.find((m) => m.measure.version_id === detail.version_id)}
          close={() => {
            setDetail(null);
            setPlanRoundId(undefined);
          }}
          save={savePlan}
          canSave={!!session}
          busy={busy}
        />
      )}
    </div>
  );
}
const documentStatus: Record<string, string> = {
  required: "Нужен по сохранённым ответам; отметка означает только вашу готовность",
  not_applicable: "По сохранённым ответам условие не применяется; подтвердите по документам",
  unknown: "Применимость не установлена: уточните условие; готовность не подтверждает применимость",
};
const questionLabels: Record<string, string> = {
  expense_year: "Год расходов",
  family_kfh_members: "Члены семейного КФХ по проекту",
  requested_grant: "Запрашиваемый грант, ₽",
};
function PlanCheck({ plan, onEdit }: { plan: Plan; onEdit: () => void }) {
  const a = plan.assessment;
  if (!a)
    return (
      <div className="alert">
        Этот план создан до сохранения объяснений подбора. Отметки документов сохранены;
        соответствие условиям нужно проверить по текущей анкете.
        <button className="text-button" onClick={onEdit}>
          Проверить анкету
        </button>
      </div>
    );
  return (
    <section className="plan-check">
      <h3>Проверка при сохранении плана</h3>
      <p>
        {date(a.assessed_at)} · <Badge kind={a.status}>{statusName[a.status]}</Badge>
      </p>
      {plan.profile_changed && (
        <div className="alert">
          Анкета изменилась после сохранения плана. Объяснения ниже относятся к прежним ответам.
          <button className="text-button" onClick={onEdit}>
            Повторить подбор по новой анкете
          </button>
        </div>
      )}
      <p>Сохранение плана и ответы анкеты не подтверждают документы или право на поддержку.
        Счётчик отражает отмеченные позиции, а не готовность заявки. Условия документов сохранены
        вместе с прежними ответами и не пересчитываются при изменении анкеты.</p>
      <p>
        Версия оценки: {a.version ?? plan.measure.version}. Отбор:{" "}
        {a.round?.code ?? plan.measure.rounds.find((r) => r.id === plan.round_id)?.code}.{" "}
        {a.legal_edition}
      </p>
      <details>
        <summary>Ответы на момент оценки</summary>
        <dl>
          {Object.entries(a.profile).map(([key, value]) => (
            <React.Fragment key={key}>
              <dt>{labels[key] || questionLabels[key] || key}</dt>
              <dd>
                {value === null
                  ? "Не указано"
                  : (options[key]?.find(([v]) => v === String(value))?.[1] ?? String(value))}
              </dd>
            </React.Fragment>
          ))}
        </dl>
      </details>
      <p>
        На момент сохранения: {availabilityName[a.availability] || "статус приёма неизвестен"}.
        Текущие сроки — в карточке отбора.
      </p>
      <details>
        <summary>Показать объяснения и что нужно уточнить</summary>
        <CheckList checks={a.checks} />
      </details>
    </section>
  );
}
function MeasureCard({ m, match, onOpen }: { m: Measure; match?: Match; onOpen: () => void }) {
  return (
    <article className="measure-card">
      <div className="card-top">
        <span className="card-icon">
          {m.category === "consultation" ? (
            <Compass />
          ) : m.category === "grant" ? (
            <Sprout />
          ) : (
            <FileCheck2 />
          )}
        </span>
        <Badge>{categoryName[m.category]}</Badge>
      </div>
      {m.synthetic && <span className="synthetic">Учебный пример</span>}
      {m.data.publication_scope === "reference" && <Badge>Справочная карточка</Badge>}
      <h3>{m.title}</h3>
      <p>{m.data.summary}</p>
      <strong className="benefit">{m.data.benefit}</strong>
      <div className="card-status">
        {match && <Badge kind={match.status}>{statusName[match.status]}</Badge>}
        <span>
          <i className={"dot " + (m.rounds[0]?.availability === "open" ? "" : "gray")} />
          {availabilityName[m.rounds[0]?.availability] || "Нет отбора"}
        </span>
      </div>
      <button className="card-link" onClick={onOpen}>
        Условия и документы <ArrowRight size={18} />
      </button>
    </article>
  );
}
function Catalog({
  catalog,
  matches,
  onOpen,
  onEdit,
  onAnnouncements,
}: {
  catalog: Measure[];
  matches?: Match[];
  onAnnouncements: () => void;
  onOpen: (m: Measure) => void;
  onEdit: () => void;
}) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [dataset, setDataset] = useState("all");
  const measures = matches !== undefined ? matches.map((m) => m.measure) : catalog;
  const items = measures.filter(
    (m) =>
      (dataset === "all" || (dataset === "demo") === m.synthetic) &&
      `${m.title} ${m.data.summary}`.toLowerCase().includes(search.toLowerCase()) &&
      (filter === "all" ||
        matches?.find((x) => x.measure.id === m.id)?.status === filter ||
        m.category === filter),
  );
  return (
    <>
      <div className="section-heading">
        <div>
          <h1>{matches ? "Ваш подбор" : "Каталог поддержки"}</h1>
          {measures.some((measure) => measure.data.publication_scope === "reference") && (
            <p>Справочные карточки доступны для изучения и плана подготовки. Статус «Нужно уточнить»
              означает, что право участия ещё не установлено. Изменение анкеты не заменяет эту проверку.</p>
          )}
          <p>
            {matches
              ? "Условия участия и доступность подачи проверяются отдельно."
              : "Изучите варианты, затем заполните анкету для персонального подбора."}
          </p>
        </div>
        {matches && (
          <button className="secondary" onClick={onEdit}>
            Уточнить анкету
          </button>
        )}
      </div>
      {measures.length === 0 ? (
        <section className="empty" role="status">
          <Sprout size={36} />
          <h2>{matches !== undefined ? "Анкета сохранена" : "Условия мер пока проверяются"}</h2>
          <p>Персональный подбор пока недоступен: проверенные условия мер ещё не опубликованы. Это не означает, что вашему хозяйству не положена поддержка.</p>
          {matches !== undefined && <p>Ответы сохранены. Заполнять анкету повторно не нужно.</p>}
          <button className="primary" onClick={onAnnouncements}>Смотреть реальные объявления <ArrowRight size={18} /></button>
        </section>
      ) : (<>
      <div className="catalog-toolbar">
        <label className="search">
          <Search size={19} />
          <input
            aria-label="Поиск мер"
            placeholder="Найти меру поддержки…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <div className="tabs">
          {(matches
            ? ["all", "PASS", "UNKNOWN", "FAIL"]
            : ["all", "grant", "subsidy", "consultation"]
          ).map((s) => (
            <button key={s} className={filter === s ? "selected" : ""} onClick={() => setFilter(s)}>
              {s === "all" ? "Все" : statusName[s] || categoryName[s]}
            </button>
          ))}
        </div>
      </div>
      <label className="field">
        Набор данных
        <select value={dataset} onChange={(e) => setDataset(e.target.value)}>
          <option value="all">Все опубликованные</option>
          <option value="real">Реальные меры</option>
          <option value="demo">Учебные примеры</option>
        </select>
      </label>
      <p className="result-count">Найдено: {items.length}</p>
      {items.length ? (
        <div className="card-grid">
          {items.map((m) => (
            <MeasureCard
              m={m}
              key={m.id}
              match={matches?.find((x) => x.measure.id === m.id)}
              onOpen={() => onOpen(m)}
            />
          ))}
        </div>
      ) : (
        <Empty>
          По вашему запросу ничего не найдено. Измените поиск или фильтр.
        </Empty>
      )}
      </>)}
    </>
  );
}
const options: Record<string, [string, string][]> = {
  registration_region: [
    ["64", "Саратовская область"],
    ["other", "Другой регион"],
  ],
  activity_region: [
    ["64", "Саратовская область"],
    ["other", "Другой регион"],
  ],
  legal_form: [
    ["ip", "Индивидуальный предприниматель"],
    ["company", "Юридическое лицо"],
    ["cooperative", "Сельхозкооператив"],
    ["individual", "Физическое лицо"],
  ],
  tax_regime: [
    ["eshn", "ЕСХН"],
    ["usn", "УСН"],
    ["npd", "Налог на профессиональный доход"],
    ["general", "Общая система"],
  ],
  sector: [
    ["crops", "Растениеводство"],
    ["livestock", "Животноводство"],
    ["processing", "Переработка"],
    ["mixed", "Несколько направлений"],
  ],
  goal: [
    ["equipment", "Приобретение оборудования"],
    ["construction", "Создание / модернизация объекта"],
    ["working_capital", "Текущие расходы"],
    ["consultation", "Консультация"],
  ],
  expense_stage: [
    ["planned", "Расходы планируются"],
    ["incurred", "Расходы уже понесены"],
  ],
  is_kfh: [
    ["true", "Да"],
    ["false", "Нет"],
  ],
  is_sme: [
    ["true", "Да"],
    ["false", "Нет"],
  ],
  special_category: [
    ["true", "Да"],
    ["false", "Нет"],
  ],
};
const labels: Record<string, string> = {
  registration_region: "Регион регистрации",
  activity_region: "Регион деятельности",
  legal_form: "Организационная форма",
  is_kfh: "Есть статус КФХ?",
  tax_regime: "Налоговый режим",
  sector: "Направление деятельности",
  goal: "На что нужна поддержка?",
  expense_stage: "На каком этапе расходы?",
  years_active: "Полных лет деятельности",
  own_funds: "Собственные средства, ₽",
  is_sme: "Есть в реестре МСП?",
  special_category: "Есть специальная категория заявителя?",
};
function Questionnaire({
  demo,
  profile,
  setProfile,
  submit,
  busy,
  questions,
}: {
  demo: boolean;
  questions: ProfileQuestion[];
  profile: Profile;
  setProfile: (p: Profile) => void;
  submit: () => Promise<void>;
  busy: boolean;
}) {
  const [step, setStep] = useState(0);
  const fields = [
    ["registration_region", "activity_region", "legal_form", "is_kfh"],
    ["sector", "tax_regime", "years_active", "is_sme"],
    ["goal", "expense_stage", "own_funds", "special_category"],
  ];
  function update(field: string, value: string) {
    const bool = ["is_kfh", "is_sme", "special_category"].includes(field);
    setProfile({
      ...profile,
      [field]:
        value === ""
          ? null
          : bool
            ? value === "true"
            : field === "years_active"
              ? Number(value)
              : value,
    });
  }
  return (
    <>
      <div className="section-heading">
        <div>
          <h1>Ваше хозяйство</h1>
          <p>Не знаете ответ? Оставьте поле пустым — мы покажем, что нужно уточнить.</p>
        </div>
        {demo && (
          <button className="text-button" disabled={busy} onClick={() => setProfile({ ...example })}>
            Заполнить учебный пример
          </button>
        )}
      </div>
      <div className="form-layout">
        <section className="form-panel">
          <div className="step-tabs">
            {["О хозяйстве", "Деятельность", "Ваш проект"].map((s, i) => (
              <button key={s} className={step === i ? "active" : ""} onClick={() => setStep(i)}>
                <span>{i + 1}</span>
                {s}
              </button>
            ))}
          </div>
          <h2>
            {["Познакомимся с хозяйством", "Чем вы занимаетесь?", "Что вы планируете?"][step]}
          </h2>
          <div className="field-grid">
            {fields[step].map((f) => (
              <label className="field" key={f}>
                {labels[f]}
                {options[f] ? (
                  <select
                    value={String(profile[f as keyof Profile] ?? "")}
                    onChange={(e) => update(f, e.target.value)}
                  >
                    <option value="">Не знаю / уточню позже</option>
                    {options[f].map(([v, label]) => (
                      <option value={v} key={v}>
                        {label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="number"
                    min="0"
                    max={f === "years_active" ? 100 : 1000000000000}
                    step={f === "years_active" ? 1 : 0.01}
                    value={String(profile[f as keyof Profile] ?? "")}
                    placeholder="Не указано"
                    onChange={(e) => update(f, e.target.value)}
                  />
                )}{" "}
                {f === "special_category" && (
                  <small>
                    Только для учебного сценария. В реальном каталоге категория должна быть точно
                    определена условиями меры.
                  </small>
                )}
              </label>
            ))}
          </div>
          {step === 2 && questions.length > 0 && (
            <>
              <h3>Уточнения для мер поддержки</h3>
              <div className="field-grid">
                {questions.map((q) => (
                  <label className="field" key={q.field}>
                    {q.label}
                    <input
                      type="number"
                      min={q.minimum}
                      max={q.maximum}
                      step={q.step}
                      value={String(profile[q.field] ?? "")}
                      placeholder="Не знаю / уточню позже"
                      onChange={(e) =>
                        setProfile({
                          ...profile,
                          [q.field]:
                            e.target.value === ""
                              ? null
                              : q.step === "0.01"
                                ? e.target.value
                                : Number(e.target.value),
                        })
                      }
                    />
                    <small>{q.hint}</small>
                  </label>
                ))}
              </div>
            </>
          )}
          <div className="form-actions">
            <button
              className="secondary"
              disabled={step === 0 || busy}
              onClick={() => setStep(step - 1)}
            >
              <ChevronLeft size={17} />
              Назад
            </button>
            {step < 2 ? (
              <button className="primary" onClick={() => setStep(step + 1)}>
                Далее <ArrowRight size={17} />
              </button>
            ) : (
              <button className="primary" disabled={busy} onClick={() => void submit()}>
                Сохранить и подобрать <ArrowRight size={17} />
              </button>
            )}
          </div>
        </section>
        <aside className="form-hint">
          <span className="hint-icon">
            <ClipboardList />
          </span>
          <h3>
            Точнее ответы —<br />
            понятнее подбор
          </h3>
          <p>Мы проверим каждый критерий и объясним результат.</p>
          <div>
            <Badge kind="PASS">Выполнено</Badge>
            <p>Ответ соответствует условию</p>
          </div>
          <div>
            <Badge kind="UNKNOWN">Нужно уточнить</Badge>
            <p>Пока не хватает информации</p>
          </div>
          <div>
            <Badge kind="FAIL">Ограничение</Badge>
            <p>Есть подтверждённое несоответствие</p>
          </div>
        </aside>
      </div>
    </>
  );
}
function CheckList({ checks }: { checks: Check[] }) {
  return (
    <ul className="checks">
      {checks.map((c) => (
        <li key={c.id}>
          <span className={"check-dot " + c.status}>
            {c.status === "PASS" ? (
              <CheckIcon size={14} />
            ) : c.status === "FAIL" ? (
              <X size={14} />
            ) : (
              <CircleHelp size={14} />
            )}
          </span>
          <div>
            <strong>{c.label}</strong>
            <small>
              {statusName[c.status]} · {c.source_ref}
            </small>
            {c.children.length > 0 && <CheckList checks={c.children} />}
          </div>
        </li>
      ))}
    </ul>
  );
}
function Detail({
  measure: m,
  match,
  close,
  save,
  canSave,
  busy,
  selectedRoundId,
}: {
  selectedRoundId?: string;
  measure: Measure;
  match?: Match;
  close: () => void;
  save: (id: string) => Promise<void>;
  canSave: boolean;
  busy: boolean;
}) {
  const [roundId, setRoundId] = useState(
    m.rounds.find((r) => r.id === selectedRoundId)?.id || m.rounds[0]?.id || "",
  );
  const r = m.rounds.find((r) => r.id === roundId);
  const dialog = React.useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const el = dialog.current;
    el?.showModal();
    const prior = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      el?.close();
      document.body.style.overflow = prior;
    };
  }, []);
  return (
    <dialog ref={dialog} className="detail-dialog" aria-labelledby="detail-title" onCancel={close}>
      <div className="dialog-head">
        <Badge>
          {categoryName[m.category]} · Версия {m.version}
        </Badge>
        <button className="icon-button" onClick={close} aria-label="Закрыть карточку">
          <X />
        </button>
      </div>
      <div className="detail-body">
        {m.synthetic && (
          <div className="alert">Учебная мера. Условия, суммы и шифр отбора вымышлены.</div>
        )}
        <h1 id="detail-title">{m.title}</h1>
        <p className="lead">{m.data.summary}</p>
        <div className="benefit-box">
          <Leaf />
          <strong>{m.data.benefit}</strong>
        </div>
        {m.data.publication_scope === "reference" && (
          <div className="alert">
            <strong>Справочная карточка по официальным документам</strong>
            <p>Это материалы для подготовки, а не подтверждение права на поддержку.
              Ниже сохранены ограничения исследования. Перечень документов нужно уточнить у организатора.</p>
          </div>
        )}
        <h2>Условия участия</h2>
        {match ? (
          <>
            <Badge kind={match.status}>{statusName[match.status]}</Badge>
            <CheckList checks={match.checks} />
          </>
        ) : (
          <>
            <p>
              Чтобы увидеть объяснения по вашей анкете, выполните подбор в разделе «Моё хозяйство».
            </p>
            <ul>
              {(m.data.rules || []).map((r) => (
                <li key={r.id}>
                  {r.label} <small>({r.source_ref})</small>
                </li>
              ))}
            </ul>
          </>
        )}
        <h2>Конкретный отбор</h2>
        {m.rounds.length > 1 && (
          <select
            aria-label="Выбор отбора"
            value={roundId}
            onChange={(e) => setRoundId(e.target.value)}
          >
            {m.rounds.map((r) => (
              <option key={r.id} value={r.id}>
                {r.code}
              </option>
            ))}
          </select>
        )}
        {r && (
          <div className="round-box">
            <Badge kind={r.availability === "open" ? "PASS" : "UNKNOWN"}>
              {availabilityName[r.availability]}
            </Badge>
            <dl>
              <dt>Шифр</dt>
              <dd>{r.code}</dd>
              <dt>Начало приёма</dt>
              <dd>{date(r.starts_at, r.timezone)}</dd>
              <dt>Окончание</dt>
              <dd>{date(r.ends_at, r.timezone)}</dd>
              <dt>Часовой пояс</dt>
              <dd>{r.timezone}</dd>
              <dt>Канал</dt>
              <dd>{r.channel}</dd>
            </dl>
            {r.availability !== "open" && (
              <p className="warning-text">
                Не считайте этот отбор доступным для подачи: проверьте объявление организатора.
              </p>
            )}
          </div>
        )}
        <h2>{m.data.publication_scope === "reference" ? "Документы для уточнения и подготовки" : "Что подготовить"}</h2>
        <ol className="doc-preview">
          {(match?.documents?.length ? match.documents : m.data.documents || []).map((d) => (
            <li key={d.id}>
              <strong>{d.title}</strong>
              <p>{d.hint}</p>
              {d.condition && <p>Условие: {d.condition.label} · {d.condition.source_ref}</p>}
              {"applicability" in d && <p>{documentStatus[String(d.applicability)]}</p>}
            </li>
          ))}
        </ol>
        <h2>Обязательства и организатор</h2>
        <p>{m.data.obligations}</p>
        <p>
          <b>{m.data.operator}</b>
          <br />
          {m.data.contact}
        </p>
        <h2>Источники и актуальность</h2>
        {m.data.publication_scope === "reference" && (
          <div className="alert">
            <p>Исследование источников: {m.data.research_checked_at ? date(m.data.research_checked_at) : "дата не указана"}.</p>
            <p>{m.data.legal_edition}</p>
            <ul>{(m.data.missing_evidence || []).map((issue, index) => <li key={index}>{issue}</li>)}</ul>
          </div>
        )}
        <p>
          Действие условий: с {date(m.data.valid_from)};{" "}
          {m.data.valid_until
            ? `до ${date(m.data.valid_until)}`
            : m.data.validity_open_ended && m.data.validity_reference?.trim()
              ? "конечная дата не установлена источником"
              : "конечная дата не подтверждена"}
          . Срок приёма заявок указан отдельно в отборе.
        </p>
        {m.data.validity_open_ended && m.data.validity_reference && (
          <p>{m.data.validity_reference}</p>
        )}
        <p>
          Содержательная проверка: {date(m.data.verified_at)}.<br />
          Статус:{" "}
          {m.data.verification_status === "verified"
            ? "проверено в рамках набора данных"
            : m.data.verification_status === "conflict"
              ? "конфликт источников"
              : "требует проверки"}
          .
        </p>
        {m.data.sources.map((s, i) => (
          <div className="source" key={i}>
            {m.synthetic ? (
              <strong>{s.title}</strong>
            ) : (
              <a target="_blank" rel="noopener noreferrer" href={s.url}>
                {s.title} ↗
              </a>
            )}
            <small>
              {s.reference} · публикация {s.published_on}
            </small>
          </div>
        ))}
        <h2>Официальный маршрут</h2>
        <p>
          {m.synthetic
            ? "В демо ссылка ведёт на главную страницу портала для ознакомления. Отбора с этим учебным шифром на портале нет."
            : "Перейдите по ссылке организатора и найдите отбор по указанному шифру. Проверьте сроки и комплект документов."}{" "}
          Переход не означает подачу заявки.
        </p>
        {r && (
          <a
            className="secondary external"
            target="_blank"
            rel="noopener noreferrer"
            href={r.application_url}
          >
            Открыть официальный ресурс <ArrowUpRight size={17} />
          </a>
        )}
      </div>
      <div className="dialog-bottom">
        <small>Предварительный подбор — не гарантия одобрения</small>
        <button
          className="primary"
          disabled={!canSave || busy || !r || m.state !== "published"}
          onClick={() => r && void save(r.id)}
        >
          <Bookmark size={17} />
          {canSave ? "Сохранить план подготовки" : "Войдите для сохранения"}
        </button>
      </div>
    </dialog>
  );
}
function NewMeasureComposer({
  demo,
  run,
}: {
  demo: boolean;
  run: (f: () => Promise<void>) => Promise<void>;
}) {
  const [body, setBody] = useState(() =>
    JSON.stringify(
      {
        title: "Новая мера — заполните условия",
        category: "grant",
        synthetic: demo,
        data: {
          summary: "Черновик. Требуется заполнить описание и проверить каждый источник.",
          benefit: "Требует заполнения",
          operator: "Требует заполнения",
          obligations: "",
          contact: "",
          rules: [
            {
              id: "region",
              label: "Регион регистрации — уточнить",
              field: "registration_region",
              op: "eq",
              value: "64",
              source_ref: "Укажите точный пункт документа",
            },
          ],
          documents: [
            { id: "application", title: "Заявление — уточнить форму", hint: "Требует проверки" },
          ],
          sources: [
            {
              title: "Замените официальным источником",
              url: "https://example.invalid/replace",
              reference: "Требует проверки",
              published_on: "",
            },
          ],
          verified_at: null,
          verification_status: "unverified",
          valid_from: null,
          valid_until: null,
          validity_open_ended: false,
          validity_reference: "",
          legal_edition: "",
          missing_evidence: ["Проверить редакцию, условия, документы и отборы"],
        },
        rounds: [],
      },
      null,
      2,
    ),
  );
  const [created, setCreated] = useState(false);
  return (
    <details className="editor-panel">
      <summary>Добавить новую меру с нуля</summary>
      <p>
        Замените все поля шаблона. Создаётся неопубликованный черновик; реальные источники проверяет
        редактор.
      </p>
      <label className="field">
        Новая мера (JSON)
        <textarea
          className="json-editor"
          value={body}
          onChange={(e) => {
            setBody(e.target.value);
            setCreated(false);
          }}
        />
      </label>
      <button
        className="secondary"
        disabled={created}
        onClick={() =>
          void run(async () => {
            await api("/admin/measures", "POST", JSON.parse(body));
            setCreated(true);
          })
        }
      >
        Создать новую меру
      </button>
      {created && (
        <p role="status">
          Черновик создан. Выйдите из раздела редактора и откройте его снова, чтобы обновить список.
        </p>
      )}
    </details>
  );
}
function RulePreview({
  dataJson,
  run,
  busy,
}: {
  dataJson: string;
  run: (f: () => Promise<void>) => Promise<void>;
  busy: boolean;
}) {
  const [profileJson, setProfileJson] = useState("{}");
  const [result, setResult] = useState<{
    status: string;
    checks: Check[];
    input: string;
  } | null>(null);
  const previewInput = dataJson + "\n" + profileJson;
  useEffect(() => setResult(null), [dataJson]);
  return (
    <details className="editor-panel">
      <summary>Проверить правила на тестовой анкете</summary>
      <p>
        Проверяется текущий текст условий, включая несохранённые изменения. Эта анкета не
        сохраняется и не меняет профиль пользователя. Результат не публикует меру и не подтверждает
        полноту источников.
      </p>
      <div className="actions wrap">
        <button
          className="secondary"
          onClick={() => {
            setProfileJson(JSON.stringify({ legal_form: "individual", is_kfh: false }, null, 2));
            setResult(null);
          }}
        >
          Гражданин без КФХ
        </button>
        <button
          className="secondary"
          onClick={() => {
            setProfileJson(JSON.stringify({ legal_form: "ip", is_kfh: true }, null, 2));
            setResult(null);
          }}
        >
          ИП — глава КФХ
        </button>
        <button
          className="secondary"
          onClick={() => {
            setProfileJson("{}");
            setResult(null);
          }}
        >
          Все ответы неизвестны
        </button>
      </div>
      <label className="field">
        Тестовая анкета (JSON)
        <textarea
          spellCheck={false}
          value={profileJson}
          onChange={(e) => {
            setProfileJson(e.target.value);
            setResult(null);
          }}
        />
      </label>
      <button
        className="secondary"
        disabled={busy}
        onClick={() =>
          void run(async () => {
            setResult(null);
            const response = await api<{
              status: string;
              checks: Check[];
            }>("/admin/preview", "POST", {
              data: JSON.parse(dataJson).data,
              profile: JSON.parse(profileJson),
            });
            setResult({ ...response, input: previewInput });
          })
        }
      >
        Проверить правила
      </button>
      {result && result.input === previewInput && (
        <div role="status">
          <Badge kind={result.status}>{statusName[result.status]}</Badge>
          <CheckList checks={result.checks} />
        </div>
      )}
    </details>
  );
}
function Editor({
  run,
  busy,
  refresh,
}: {
  run: (f: () => Promise<void>) => Promise<void>;
  busy: boolean;
  refresh: () => Promise<void>;
}) {
  const [versions, setVersions] = useState<Measure[]>([]);
  const [selected, setSelected] = useState<Measure | null>(null);
  const [json, setJson] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [dataset, setDataset] = useState("real");
  async function reload() {
    setVersions(await api<Measure[]>("/admin/versions"));
    await refresh();
  }
  useEffect(() => {
    void run(reload);
  }, []);
  function select(m: Measure) {
    setSelected(m);
    setJson(
      JSON.stringify(
        { data: m.data, rounds: m.rounds.map(({ id, availability, ...r }) => r) },
        null,
        2,
      ),
    );
  }
  async function action(action: string) {
    if (!selected) return;
    await run(async () => {
      const m = await api<Measure>(
        `/admin/versions/${selected.version_id}/${action}`,
        "POST",
        action === "clone" ? undefined : { revision: selected.revision },
      );
      select(m);
      await reload();
    });
  }
  return (
    <>
      <div className="section-heading">
        <div>
          <h1>Управление каталогом</h1>
          <p>Черновик → проверка → публикация. Опубликованные условия сохраняются в истории.</p>
        </div>
      </div>
      <label className="field">
        Редакционный набор
        <select
          value={dataset}
          onChange={(e) => {
            setDataset(e.target.value);
            setSelected(null);
          }}
        >
          <option value="real">Реальные меры</option>
          <option value="demo">Учебные примеры</option>
          <option value="all">Все версии</option>
        </select>
      </label>
      <div className="editor-layout">
        <div className="version-list">
          {versions
            .filter((m) => dataset === "all" || (dataset === "demo") === m.synthetic)
            .map((m) => (
              <button
                key={m.version_id}
                className={selected?.version_id === m.version_id ? "selected" : ""}
                onClick={() => select(m)}
              >
                <strong>{m.title}</strong>
                <small>
                  Версия {m.version} · {stateName[m.state]}
                </small>
              </button>
            ))}
        </div>
        <section className="editor-panel">
          {selected ? (
            <>
              <Badge>
                {stateName[selected.state]} · v{selected.version} · ревизия {selected.revision}
              </Badge>
              <h2>{selected.title}</h2>
              <Badge>
                {selected.synthetic ? "Учебный пример" : "Реальная мера — редакционный контур"}
              </Badge>
              {(selected.data.missing_evidence || []).length > 0 && (
                <div className="alert">
                  <strong>Публикация заблокирована до проверки</strong>
                  <ul>
                    {(selected.data.missing_evidence || []).map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              <p>{selected.data.legal_edition}</p>
              <p>
                Исследование источников: {date(selected.data.research_checked_at)}. Полная проверка:{" "}
                {date(selected.data.verified_at)}.
              </p>
              {selected.data.sources.map((source, i) => (
                <p key={i}>
                  <a href={source.url} target="_blank" rel="noopener noreferrer">
                    {source.title} ↗
                  </a>
                </p>
              ))}
              <p>
                Правила и источники редактируются в структурированном формате. Даты — ISO 8601 с
                часовым поясом. Поля проверяются сервером.
              </p>
              <label className="field">
                Условия и отборы (JSON)
                <textarea
                  className="json-editor"
                  spellCheck={false}
                  value={json}
                  readOnly={selected.state !== "draft"}
                  onChange={(e) => setJson(e.target.value)}
                />
              </label>
              <div className="actions wrap">
                {selected.state === "draft" && (
                  <>
                    <button
                      className="primary"
                      disabled={busy}
                      onClick={() =>
                        void run(async () => {
                          const m = await api<Measure>(
                            `/admin/versions/${selected.version_id}`,
                            "PUT",
                            { ...JSON.parse(json), revision: selected.revision },
                          );
                          select(m);
                          await reload();
                        })
                      }
                    >
                      Сохранить черновик
                    </button>
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() => void action("review")}
                    >
                      На проверку
                    </button>
                  </>
                )}
                {selected.state === "review" && (
                  <>
                    <button
                      className="primary"
                      disabled={busy}
                      onClick={() => void action("publish")}
                    >
                      Опубликовать
                    </button>
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() => void action("return")}
                    >
                      Вернуть в черновик
                    </button>
                  </>
                )}
                {selected.state === "published" && (
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={() => void action("unpublish")}
                  >
                    Снять с публикации
                  </button>
                )}
                <button className="secondary" disabled={busy} onClick={() => void action("clone")}>
                  Создать новую версию
                </button>
              </div>
              <RulePreview key={selected.version_id} dataJson={json} run={run} busy={busy} />
              <div className="new-measure">
                <h3>Новая мера из этой карточки</h3>
                <p>
                  Создаётся черновик на основе выбранной карточки. После создания замените все
                  условия и источники.
                </p>
                <label className="field">
                  Название
                  <input
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="Название новой меры"
                  />
                </label>
                <button
                  className="secondary"
                  disabled={busy || newTitle.trim().length < 3}
                  onClick={() =>
                    void run(async () => {
                      const payload = JSON.parse(json);
                      payload.data.verification_status = "unverified";
                      payload.data.verified_at = null;
                      const m = await api<Measure>("/admin/measures", "POST", {
                        title: newTitle,
                        category: selected.category,
                        synthetic: selected.synthetic,
                        ...payload,
                      });
                      select(m);
                      setNewTitle("");
                      await reload();
                    })
                  }
                >
                  Создать черновик
                </button>
              </div>
            </>
          ) : (
            <Empty>Выберите версию в списке слева.</Empty>
          )}
        </section>
      </div>
    </>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
