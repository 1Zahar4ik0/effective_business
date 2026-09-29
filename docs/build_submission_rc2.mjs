import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile,FileBlob} from '@oai/artifact-tool';
const root='C:/EffectiveBusiness';
const skill='C:/Users/Пользователь/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const python='C:/Users/Пользователь/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const green='#214B38',ink='#213C32',light='#F5F6EF',muted='#66766C';
function text(s,t,x,y,w,h,size=30,color=ink,bold=false){const b=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});b.text=t;b.text.style={typeface:'Arial',fontSize:size,color,bold,autoFit:'none'};}
function slide(p,title,notes='',dark=false){const s=p.slides.add();s.background.fill=dark?green:light;if(title)text(s,title,64,48,1152,100,44,dark?'#FFFFFF':ink,true);s.speakerNotes.textFrame.setText(notes);return s;}
function lines(s,a,y=190,size=31,step=90){a.forEach((t,i)=>text(s,t,64,y+i*step,1152,step-12,size));}
const version='opora-apk-20260929-rc2';
async function build(jury){const p=Presentation.create({slideSize:{width:1280,height:720}});
if(jury){const s=slide(p,'Доступ для технической проверки','Служебный слайд по странице 10 задания. Секреты передаются организаторам отдельно по закрытому каналу, в комплекте отсутствуют. Редактор использует назначенный владельцем MAX-аккаунт; гостевого редакторского входа в production нет.');lines(s,[
'MAX: max.ru/t761_hakaton_max_bot?startapp',
'HTTPS: opora-apk.159-194-249-97.sslip.io',
'Исходники: source.zip; контрольная сумма в SHA256SUMS.txt',
'Версия: '+version+'; API: /docs',
'Локальные тестовые роли: farmer, second, editor',
'Доступы и порядок проверки: jury/ACCESS.md'],175,27,72);}
let s=slide(p,'','Опора АПК. Кандидат сдаваемой версии от 29.09.2026. Состав команды требуется указать перед отправкой организаторам.',true);
text(s,'Опора АПК',64,165,1100,120,88,'#FFFFFF',true);text(s,'Поддержка сельского хозяйства\nв мини-приложении MAX',68,340,1100,150,44,'#DFE9DC');text(s,'Саратовская область • 29 сентября 2026',68,587,1120,44,27,'#DFE9DC');
s=slide(p,'Кому помогает продукт','Задание «Эффективный бизнес», стр. 5, 8, 16–18. Наблюдение по собранным нормативным документам и объявлениям minagro.saratov.gov.ru/subsidii/. Интервью и измеренная экономия времени не заявляются.');
text(s,'КФХ и сельскохозяйственные ИП\nСаратовской области',64,185,1100,120,42,green,true);
lines(s,['Фермер сопоставляет правила программы, поправки и отборы.','От категории хозяйства зависят допуск и документы.','Ошибка в сроке или редакции меняет результат подготовки.'],350,31,94);
s=slide(p,'Основной пользовательский путь','Реализовано в коде и проверяется на отдельном синтетическом стенде. Десять справочных карточек доступны для изучения и плана. Полный допуск не подтверждается. Пользователь подтвердил работу пути, ранее указал веб-MAX и Android; детальный протокол не предоставлен.');
lines(s,['01  Вход через бота и анкета хозяйства','02  Проверка критериев с объяснениями','03  Карточка меры и конкретного отбора','04  Сохранённый план подготовки документов','05  Официальный маршрут подачи'],177,32,83);
s=slide(p,'Официальные документы в продукте','Снимок размещённого интерфейса output/submission-20260929/site.png. Источник: приказ 186-пр от 08.07.2026. Пределы относятся к конкретным условиям, не гарантируют выплату или открытый приём.');
s.images.add({blob:new Uint8Array(await fs.readFile(path.join(root,'output/submission-20260929/site.png'))),contentType:'image/png',alt:'Каталог официальных документов Опора АПК',fit:'contain',position:{left:64,top:165,width:1152,height:450}});
text(s,'Сумма программы, бюджет отбора и выплата заявителю различаются.',64,634,1152,42,25,muted);
s=slide(p,'Объяснимый подбор','backend/app/matching.py; тесты на PostgreSQL. UNKNOWN обозначает неизвестный факт, а не подтверждённый допуск. Справочные версии всегда сохраняют UNKNOWN, кроме подтверждённого несоответствия по отдельно сверенным критериям.');
text(s,'PASS',64,194,250,65,44,green,true);text(s,'Указанные сведения выполняют критерий.',330,194,880,85,32);
text(s,'FAIL',64,314,250,65,44,green,true);text(s,'Есть конкретное несоответствие с объяснением.',330,314,880,85,32);
text(s,'UNKNOWN',64,434,265,65,42,green,true);text(s,'Нужен ответ пользователя или проверка документа.',330,434,880,85,32);
text(s,'Срок приёма проверяется отдельно от соответствия хозяйства.',64,596,1152,70,29,muted);
s=slide(p,'Архитектура','ARCHITECTURE.md; модули FastAPI и модели PostgreSQL. Подключение MAX и HTTPS реально работает. История версий отделена от конкретных отборов и сохранённых планов.');
const vals=[['Компонент','Назначение'],['React + TypeScript','Анкета, каталог, планы, редактор'],['Python + FastAPI','Правила, сессии, права, версии'],['PostgreSQL + Alembic','Профили, история условий, планы'],['MAX + HTTPS','Вход, мини-приложение, события бота']];
const tb=s.tables.add({rows:5,columns:2,left:64,top:176,width:1150,height:380,columnWidths:[400,750],values:vals});
tb.borders.assign({fill:'#DDE3D7',width:1,style:'solid'});for(let row=0;row<5;row++)for(let col=0;col<2;col++){const c=tb.getCell(row,col);c.fill=row===0?green:light;c.text.style={typeface:'Arial',fontSize:28,color:row===0?'#FFFFFF':ink,bold:row===0};}
text(s,'Мера, редакция условий и отбор хранятся отдельно.\nПлан сохраняет снимок проверки и версию правил.',64,590,1152,85,29,muted);
s=slide(p,'Проверки сдаваемой сборки','29.09.2026: Docker --no-cache, базовые образы загружены заранее. 117 pytest PASS, 20 DATA-API PASS. Первый прогон: отсутствовал mount архива источников; после исправления полный повтор PASS. Два предупреждения зависимостей сохранены. Результаты в RELEASE-20260929-RC2.md.');
text(s,'78,6 с',64,190,510,110,78,green,true);text(s,'Сборка Docker без кеша\nпри лимите задания 5 минут',64,325,510,115,30);
text(s,'117',692,190,500,110,78,green,true);text(s,'Автоматических тестов\nна отдельной PostgreSQL',692,325,500,115,30);
text(s,'20 сценариев API; миграции; сохранение профиля и плана.\nВеб-MAX и Android: подтверждение пользователя.',64,540,1150,115,30);
s=slide(p,'Пилот и ожидаемый эффект','Предложение для следующего этапа. Пилот и количественные результаты не проводились. Партнёры не заявляются.');
lines(s,['Первый сегмент: КФХ Саратовской области.','Задача пилота: подобрать поддержку и составить план.','Сравнение с самостоятельным поиском по тем же источникам.','Метрики: время, ошибки и доля завершивших сценарий.'],185,31,98);
text(s,'Гипотеза: сохранённый план уменьшит повторный поиск документов.',64,606,1152,68,27,muted);
s=slide(p,'Расширение на другой регион','Предлагаемый следующий регион: Пензенская область. Исследование её каталога не завершено. Новые условия проходят самостоятельную проверку.');
text(s,'Сохраняем',64,188,510,70,38,green,true);text(s,'Движок правил\nВерсии и отборы\nПрофиль и личный план\nАвторизацию MAX',64,293,530,260,32);
text(s,'Адаптируем',692,188,510,70,38,green,true);text(s,'Региональные документы\nКатегории и справочники\nМаршруты подачи\nРаботу редактора',692,293,530,260,32);
text(s,'Следующий шаг: исследование Пензенской области и ограниченный пилот.',64,613,1152,64,27,muted);
s=slide(p,'Текущие границы','Фактическое состояние кандидата сдачи. Публичный API содержит 10 справочных карточек и 11 отборов. Полных публикаций допуска 0. Присланные документы подлинны по заявлению пользователя, но полнота редакций и применимость требуют отдельной сверки. Доступы жюри и состав команды требуют подготовки.');
lines(s,['MAX, HTTPS и сохранение анкеты работают.','Закрытые отборы не отображаются открытыми.','10 справочных карточек доступны для личного плана.','Полный допуск требует дальнейшей сверки условий.','Заявки подписывает и подаёт сам пользователь.'],176,30,84);
s=slide(p,'Источники','Источники данных сохранены с SHA-256; точные области проверки в реестре evidence.');
lines(s,['Минсельхоз Саратовской области: minagro.saratov.gov.ru','Объявления отборов: promote.budget.gov.ru','Публикации нормативных актов: publication.pravo.gov.ru'],177,29,86);
const label=jury?'jury':'public';const tmp=path.join(root,'tmp/submission-20260929-rc2/slides',label);await fs.mkdir(tmp,{recursive:true});
const candidate=path.join(tmp,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
const dest=path.join(root,'output/submission-20260929-rc2',label,'opora-apk.pptx');
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:dest,pythonExecutable:python,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--require-native-table-slide',jury?'7':'6'],requiredNativeTableOwnerSlides:[jury?7:6],fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(tmp,'validation.json')});
const loaded=await PresentationFile.importPptx(await FileBlob.load(dest));for(let i=0;i<loaded.slides.items.length;i++){const png=await loaded.export({slide:loaded.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(tmp,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));}console.log(label,loaded.slides.items.length,'slides validated/rendered');}
await build(false);await build(true);process.exit(0);
