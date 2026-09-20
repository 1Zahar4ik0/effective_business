"""Создание PDF-обзора. Не является зависимостью приложения."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'/'pdf'
OUT.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='ArialBold')
c=canvas.Canvas(str(OUT/'opora-apk-overview.pdf'),pagesize=(960,540))
c.setTitle('Опора АПК — локальный MVP')
GREEN='#244d38'; INK='#2b4634'; MUTED='#71806b'; BG='#f5f6f1'

def text(value,x,y,w,size=18,color=INK,bold=False):
    style=ParagraphStyle('t',fontName='ArialBold' if bold else 'Arial',fontSize=size,leading=size*1.4,textColor=HexColor(color))
    p=Paragraph(value,style);_,h=p.wrap(w,500);p.drawOn(c,x,y-h)
    return h

def page(number,title,kicker='ЛОКАЛЬНЫЙ MVP · 18.09.2026'):
    c.setFillColor(HexColor(BG));c.rect(0,0,960,540,fill=1,stroke=0)
    text('ОПОРА АПК',48,505,350,13,GREEN,True)
    text(kicker,550,505,360,10,MUTED)
    text(title,48,450,860,32,GREEN,True)
    c.setStrokeColor(HexColor('#dbe2d4'));c.line(48,47,912,47)
    text('Синтетические данные. Не действующие условия господдержки.',48,33,760,9,MUTED)
    text(str(number),875,33,40,9,MUTED)

def card(x,y,w,title,body):
    c.setFillColor(HexColor('#ffffff'));c.roundRect(x,y-170,w,170,12,fill=1,stroke=0)
    text(title,x+22,y-22,w-44,20,GREEN,True)
    text(body,x+22,y-67,w-44,15,MUTED)

page(1,'Навигация по поддержке бизнеса и АПК')
text('Анкета хозяйства → объяснимый подбор → план документов',48,375,780,24)
text('Для КФХ и ИП Саратовской области. Кооперативы проверяются как отдельная категория.',48,295,730,19,MUTED)
c.setFillColor(HexColor(GREEN));c.roundRect(48,108,864,100,14,fill=1,stroke=0)
text('Работающий локальный сценарий',73,188,800,22,'#ffffff',True)
text('React + TypeScript · Python / FastAPI · PostgreSQL · Docker Compose',73,149,800,15,'#d8e2cc')
c.showPage()

page(2,'Путь пользователя')
card(48,365,274,'01 · Анкета','Регион, статус хозяйства, направление и цель. Неизвестные ответы можно уточнить позже.')
card(343,365,274,'02 · Подбор','Причина по каждому условию. Соответствие анкете отделено от доступности подачи.')
card(638,365,274,'03 · Подготовка','Сохранённый список документов. Отметки остаются после повторного входа.')
text('Затем — официальный маршрут',48,151,860,21,GREEN,True)
text('Портал и шифр связаны с конкретным отбором. Навигатор не отправляет и не подписывает заявку.',48,113,850,15,MUTED)
c.showPage()

page(3,'Данные и проверка условий')
card(48,368,274,'Мера поддержки','Стабильная сущность: название, категория, признак синтетического набора.')
card(343,368,274,'Версия условий','Правила, источники, дата проверки, документы. Опубликованная история сохраняется.')
card(638,368,274,'Конкретный отбор','Сроки с часовым поясом, шифр, канал и адрес подачи. Связан с применимой версией.')
text('PASS',60,153,200,20,'#47794b',True);text('FAIL',354,153,200,20,'#aa654b',True);text('UNKNOWN',650,153,220,20,'#a18543',True)
text('Условие выполнено',60,119,230,15,MUTED);text('Есть несоответствие',354,119,240,15,MUTED);text('Нужно уточнить ответ',650,119,260,15,MUTED)
c.showPage()

page(4,'Архитектура и редактор')
text('React / TypeScript',48,367,390,24,GREEN,True)
text('Анкета, карточки, планы, мобильная навигация и минимальная панель редактора.',48,320,380,17,MUTED)
text('FastAPI + PostgreSQL',506,367,400,24,GREEN,True)
text('Серверные правила, сессии и роли, миграции, история версий, очередь ответов MAX.',506,320,400,17,MUTED)
c.setFillColor(HexColor('#e8eee0'));c.roundRect(48,108,864,105,12,fill=1,stroke=0)
text('Черновик → проверка → публикация → архив',70,191,820,22,GREEN,True)
text('Изменение опубликованной карточки создаёт новую версию. Старый план предупреждает об изменении условий.',70,150,800,15,MUTED)
c.showPage()

page(5,'Что проверено')
card(48,365,274,'22 теста','PostgreSQL: правила, сроки, доступ, версии, подпись MAX, повторные события и очередь.')
card(343,365,274,'14 шагов API','Проверки DATA-API.yaml выполнены против работающего приложения в Docker.')
card(638,365,274,'50 секунд','Измеренная сборка без кеша при уже загруженных базовых образах. Условия сети влияют на время.')
text('Также проверены TypeScript и сборка React',48,155,860,21,GREEN,True)
text('В браузере пройдены анкета, подбор, карточка, сохранение плана и восстановление отметки после перезагрузки.',48,112,860,15,MUTED)
c.showPage()

page(6,'Границы версии и следующий этап')
text('Сейчас: 6 учебных мер и изолированный демовход',48,372,850,23,GREEN,True)
text('Рабочий режим запрещает демоданные. Нет реального каталога, автоматического обновления источников, отправки заявок и ведомственных статусов.',48,319,850,18,MUTED)
text('Для подключения MAX',48,233,850,23,GREEN,True)
text('Нужны зарегистрированный бот, серверный токен, HTTPS-адрес, webhook и проверка на телефоне и в веб-MAX. Браузерная проверка ширины экрана их не заменяет.',48,185,850,18,MUTED)
text('Источники адаптера: dev.max.ru/docs/webapps/validation · dev.max.ru/docs/webapps/bridge',48,99,860,10,MUTED)
text('Подробности запуска и ограничений: README.md · docs/MAX.md · docs/PROGRESS.md',48,77,860,10,MUTED)
c.showPage();c.save()
print(OUT/'opora-apk-overview.pdf')
