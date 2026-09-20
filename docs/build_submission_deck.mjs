// Artifact Tool builder. Run a copy in tmp/presentation with the bundled node_modules.
// Required: PRESENTATION_SKILL_DIR, RUNTIME_PYTHON, RUNTIME_NODE_MODULES. Does not read .env.
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const root = process.cwd();
const skill = process.env.PRESENTATION_SKILL_DIR;
const python = process.env.RUNTIME_PYTHON;
if (!skill || !python) throw new Error('Set PRESENTATION_SKILL_DIR and RUNTIME_PYTHON');
const { finalizePresentation } = await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const version = 'opora-apk-20260918-local-r1';
const timing = JSON.parse((await fs.readFile(path.join(root,'docs/assets/release-build-timing.json'),'utf8')).replace(/^\uFEFF/,''));
const seconds = timing.seconds.toLocaleString('ru-RU');
const green='#214B38', ink='#213C32', muted='#67786E', light='#F5F6EF', ochre='#AF7A29';
const fonts={basis:'design',families:['Arial']};
const titles=[];
function box(s,text,x,y,w,h,size=28,color=ink,bold=false) {
  const b=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  b.text=text;b.text.style={typeface:'Arial',fontSize:size,color,bold,autoFit:'none'};return b;
}
function slide(p,title,notes='',dark=false) {
  const s=p.slides.add();s.background.fill=dark?green:light;
  if(title) box(s,title,64,52,1152,105,44,dark?'#FFFFFF':ink,true);
  box(s,`${String(p.slides.items.length).padStart(2,'0')}     ОПОРА АПК`,64,664,600,25,16,dark?'#C8D8CC':muted);
  s.speakerNotes.textFrame.setText(notes);titles.push(title);return s;
}
async function picture(s,name,x,y,w,h) {
  s.images.add({blob:new Uint8Array(await fs.readFile(path.join(root,'docs/assets',name))),contentType:'image/png',alt:'Скриншот локальной синтетической демонстрации Опора АПК',fit:'contain',position:{left:x,top:y,width:w,height:h}});
}
function lines(s,items,x=64,y=190,w=1120,size=29,step=100) {
  items.forEach((text,i)=>box(s,text,x,y+i*step,w,step-15,size));
}
async function create(jury) {
  const p=Presentation.create({slideSize:{width:1280,height:720}});
  if(jury) {
    let s=slide(p,'Служебные данные для проверки', 'Служебный слайд по стр. 10 задания. Секреты не переданы и не встроены. Комплект является локальным кандидатом, не подтверждением допуска.');
    lines(s,[
      'Версия: '+version,
      'Исходники: архив source.zip и SHA256SUMS.txt в комплекте',
      'Локальный стенд: http://localhost:8000    API: /docs',
      'Демо: farmer / editor / second, без пароля, только localhost',
      'MAX и публичный HTTPS API: не настроены. Токен отсутствует.',
      'Проверка: анкета, подбор, карточка, план, официальный маршрут'
    ],64,180,1140,27,67);
    box(s,'Данные команды и реальные доступы нужно заполнить до отправки жюри.',64,606,1140,36,23,ochre,true);
  }
  let s=slide(p,'', 'Рабочее название проекта. Состав команды пользователем не передан. Статус и границы версии: docs/RELEASE-AUDIT.md.',true);
  box(s,'Опора АПК',64,160,1100,112,88,'#FFFFFF',true);
  box(s,'Навигация по мерам поддержки\nдля фермеров Саратовской области',68,318,1050,132,42,'#DFE9DC');
  box(s,'Локальный MVP / 18 сентября 2026',68,548,1100,50,26,'#CBDDCD');

  s=slide(p,'Пользователь и проблема','Основание: исходное задание, стр. 5, 8, 18; официальный раздел https://minagro.saratov.gov.ru/subsidii/; сохранённые комплекты data/official/sources. Интервью не проводились. Оценки затрат времени пока являются гипотезой.');
  box(s,'КФХ и ИП в сельском хозяйстве\nСаратовской области',64,188,530,125,35,green,true);
  box(s,'Хозяйство планирует оборудование или расходы и хочет понять, какая поддержка подходит и что подготовить.',64,345,530,175,28);
  box(s,'Что приходится сопоставлять',692,188,520,72,32,green,true);
  lines(s,['Правила программы и поправки к ним','Условия конкретного отбора и сроки','Категорию заявителя и документы'],692,284,520,28,104);
  box(s,'Наблюдение по документам. Интервью и замер времени ещё нужны.',64,586,1120,46,24,muted);

  s=slide(p,'Основной путь пользователя','Локальная браузерная проверка 18.09.2026. Скриншот docs/assets/release-plan-phone.png, ширина 390 px. Это браузер, не мобильный клиент MAX. Демонстрируются синтетические данные.');
  lines(s,['01  Анкета хозяйства','02  Подбор с объяснениями','03  Карточка меры и отбора','04  Сохранённый план документов','05  Официальный ресурс подачи'],64,174,735,31,79);
  await picture(s,'release-plan-phone.png',923,160,244,500);
  box(s,'Отметка документа сохраняется после повторного входа.\nПереход на портал не означает подачу заявки.',64,585,820,65,23,muted);

  s=slide(p,'Как объясняется результат','Серверная реализация backend/app/matching.py, тесты test_core.py/test_official.py/test_release.py. Предварительное сопоставление анкеты не гарантирует одобрение. Все числовые примеры на слайде учебные.');
  const labels=[['PASS','Ответ соответствует','Регион 64 совпал\nс условием учебной меры.',green],['UNKNOWN','Нужно уточнить','Статус заявителя неизвестен.\nСоответствие не подтверждаем.',ochre],['FAIL','Есть ограничение','Регион не совпал.\nПоказываем причину отказа.', '#985343']];
  labels.forEach(([a,b,c,d],i)=>{let x=64+i*396;box(s,a,x,207,360,78,52,d,true);box(s,b,x,315,355,75,29,ink,true);box(s,c,x,411,355,126,27);});
  box(s,'Доступность приёма проверяется отдельно: срок, часовой пояс, версия и свежесть источника.',64,585,1145,66,26,muted);

  s=slide(p,'Мера, редакция и отбор','Модель backend/app/models.py; неизменяемость опубликованной версии и старого плана проверена интеграционными тестами. docs/RELEASE-AUDIT.md.');
  lines(s,['Мера поддержки: постоянная карточка программы.','Версия условий: конкретная редакция правил и источников.','Отбор: срок, канал подачи и ссылка на применимую версию.'],64,197,1140,32,114);
  box(s,'План хранит версию условий. При новой публикации пользователь получает предупреждение о повторной проверке.',64,563,1120,82,29,green,true);

  s=slide(p,'Архитектура решения','ARCHITECTURE.md, разделы 16–18. FastAPI обслуживает API и статический React. MAX подготовлен, но не подключён. Один PostgreSQL и модульный монолит.');
  const values=[['Компонент','Ответственность'],['React + TypeScript','Анкета, карточки, планы, редактор'],['Python + FastAPI','Сессии, правила, версии, права доступа'],['PostgreSQL + Alembic','Профили, планы, снимки проверок, очередь'],['Адаптер MAX','Подпись запуска, webhook, повторы событий']];
  const table=s.tables.add({rows:5,columns:2,left:64,top:176,width:1150,height:390,columnWidths:[380,770],values});
  table.borders.assign({fill:'#DDE3D7',width:1,style:'solid'});
  for(let r=0;r<5;r++)for(let c=0;c<2;c++) {const cell=table.getCell(r,c);cell.fill=r===0?green:'#F5F6EF';cell.text.style={typeface:'Arial',fontSize:27,color:r===0?'#FFFFFF':ink,bold:r===0};}
  box(s,'Docker Compose запускает локальные компоненты.\nДля размещения подготовлен отдельный Nginx с HTTPS.',64,597,1150,64,26,muted);

  s=slide(p,'Данные и источники','Официальный источник: https://minagro.saratov.gov.ru/subsidii/. Реестр data/official/catalog.json, docs/CATALOG-REVIEW.md. Исследование 18.09.2026, полная содержательная проверка не завершена. Портал promote.budget.gov.ru недоступен проверяющей среде.');
  [['6','учебных мер','Опубликованы только\nдля локальной демонстрации.',green],['10','реальных черновиков','Есть документы и отборы.\nПробелы указаны редактору.',ochre],['0','реальных публикаций','Неполные условия\nне попадают в подбор.',ink]].forEach(([a,b,c,d],i)=>{let x=64+i*396;box(s,a,x,182,360,124,91,d,true);box(s,b,x,335,360,78,30,ink,true);box(s,c,x,440,360,120,27);});
  box(s,'Источник и дата исследования видны отдельно от подтверждения условий.',64,592,1140,45,25,muted);

  s=slide(p,'Результаты проверки',`docs/RELEASE-AUDIT.md и docs/PROGRESS.md. 38 pytest на отдельной PostgreSQL; 14 шагов DATA-API; 10 сценариев локального TLS. Сборка --no-cache: ${seconds} с, базовые образы уже загружены. Это результат данного компьютера, не универсальная гарантия скорости.`);
  [['38','автоматических тестов'],['14','сценариев API'],[seconds+' с','сборка без кеша']].forEach(([a,b],i)=>{let x=64+i*396;box(s,a,x,180,365,113,72,green,true);box(s,b,x,310,365,85,28,ink,true);});
  lines(s,['Миграции с нуля и сохранение данных после перезапуска','Подпись MAX, права владельца, версии и повторные события','10 локальных HTTPS-проверок, экраны 390 и 1440 px'],64,430,1140,27,66);
  box(s,'Лимит задания: 5 минут без первоначальной загрузки базовых образов.',64,630,1140,29,22,muted);

  s=slide(p,'Что ещё мешает сдаче','Исходное задание стр. 7, 9–11: живой MAX и HTTPS API обязательны. MAX preflight: конфигурация отсутствует. Отчёт пользователя о телефоне на момент подготовки не получен.');
  lines(s,['Нет живого запуска в MAX и публичного HTTPS API.','Мобильный и веб-MAX фактически не проверены.','Реальные меры требуют завершения юридической проверки.','Нет пилота и измеренного эффекта для пользователей.'],64,190,1140,31,91);
  box(s,'Следующий обязательный шаг: разрешённое размещение,\nнастройка MAX и проверка обеих версий клиента.',64,575,1130,83,29,ochre,true);

  s=slide(p,'План пилота и ожидаемый эффект','Предложение, а не выполненный пилот. Участники, сроки, партнёры и числовые целевые показатели не согласованы. Метод оценки: сравнение одинаковых задач с исходными порталами и навигатором, оценка условий независимым редактором.');
  box(s,'Гипотеза',64,185,500,50,34,green,true);
  box(s,'Объяснения условий и сохранённый список документов сократят повторный поиск и пропуски при подготовке.',64,267,515,217,32);
  box(s,'Как проверять',692,185,500,50,34,green,true);
  lines(s,['Время до подходящего варианта','Доля завершивших основной путь','Ошибки относительно проверки эксперта'],692,267,510,29,109);
  box(s,'Первый сегмент: небольшая группа КФХ Саратовской области после готовности каталога и MAX.',64,583,1150,72,26,muted);

  s=slide(p,'Расширение на другой регион','Кандидат для следующего региона: Пензенская область, как проектное предложение. Исследование её мер не проводилось. Потребуется адаптация справочников и фиксированных названий региона в интерфейсе, а не простое копирование саратовских правил.');
  box(s,'Сохраняем ядро',64,187,525,60,34,green,true);
  box(s,'Модель версий и отборов\nДвижок PASS / FAIL / UNKNOWN\nЛичный план и роли пользователей',64,290,540,196,29);
  box(s,'Меняем региональную часть',692,187,530,85,33,green,true);
  box(s,'Первоисточники и местные условия\nСправочники и тексты интерфейса\nКаналы подачи и редакторскую проверку',692,290,530,211,29);
  box(s,'Порядок: исследование Пензенской области, черновики, проверка экспертом, ограниченный пилот. Это предложение.',64,572,1145,90,26,muted);

  s=slide(p,'Источники и границы доказательств','Исходное задание пользователя «Эффективный бизнес», 22 страницы. Официальные веб-страницы проверены 18.09.2026. Точные локальные результаты см. docs/RELEASE-AUDIT.md.');
  lines(s,['Задание «Эффективный бизнес», страницы 5–13, 18–20','Минсельхоз Саратовской области: minagro.saratov.gov.ru/subsidii/','MAX: dev.max.ru/docs/webapps/validation и /bridge','MAX API: dev.max.ru/docs-api/changelog-api','Реестр источников и испытания: документы в комплекте проекта'],64,185,1150,28,79);
  box(s,'Интервью, партнёры, статистика спроса и результаты пилота не заявляются.',64,601,1140,57,25,muted);

  const label=jury?'jury':'public';
  const dir=path.join(root,'tmp/presentation',label);await fs.mkdir(dir,{recursive:true});
  const candidate=path.join(dir,'candidate.pptx');
  await (await PresentationFile.exportPptx(p)).save(candidate);
  const finalPath=path.join(root,'output/submission',label,`opora-apk-${label}-v2.pptx`);
  await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath,pythonExecutable:python,
    integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
    layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
    layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide',jury?'7':'6'],
    requiredNativeTableOwnerSlides:[jury?7:6],fontPolicy:fonts,verifyArtifactToolImport:true,
    receiptPath:path.join(dir,'validation-v2.json')});
  const imported=await PresentationFile.importPptx(await (await import('@oai/artifact-tool')).FileBlob.load(finalPath));
  for(let i=0;i<imported.slides.items.length;i++) {
    const png=await imported.export({slide:imported.slides.items[i],format:'png',scale:1.5});
    await fs.writeFile(path.join(dir,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
  }
  console.log(`${label}: ${p.slides.items.length} slides, editable PPTX and renders complete`);
}
await create(false);
await create(true);
// Native raster resources in this Windows runtime may crash during late cleanup.
// All finalizers, checks and file writes above have completed before explicit exit.
process.exit(0);
