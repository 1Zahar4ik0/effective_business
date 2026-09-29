from .schemas import VersionData

QUESTIONS = {
    "requested_grant": {
        "label": "Какую сумму гранта вы запрашиваете, ₽?",
        "hint": "Укажите сумму гранта, а не стоимость проекта или бюджет отбора. Доля софинансирования и документы проверяются отдельно.",
        "minimum": 0,
        "maximum": 1000000000000,
        "step": "0.01",
    },
    "expense_year": {
        "label": "В каком году понесены расходы, для которых нужна поддержка?",
        "hint": "Если расходы относятся к нескольким годам или пока планируются, оставьте поле пустым. Для разных периодов может потребоваться отдельная проверка.",
        "minimum": 2000,
        "maximum": 2100,
    },
    "family_kfh_members": {
        "label": "Сколько членов семьи входит в КФХ по вашему проекту, включая главу?",
        "hint": "Учитывайте членов КФХ, связанных родством или свойством. Если состав или статус ещё не определён, оставьте поле пустым. Подтверждающие документы проверяются отдельно.",
        "minimum": 0,
        "maximum": 100,
    },
}


def additional_questions(versions):
    sources_by_field = {}

    def collect_sources(rules):
        for rule in rules:
            if rule.field in QUESTIONS:
                sources_by_field.setdefault(rule.field, set()).add(rule.source_ref)
            collect_sources(rule.children)

    for data in versions:
        version = VersionData.model_validate(data)
        collect_sources(version.rules)
        for document in version.documents:
            if document.condition:
                collect_sources([document.condition])
    questions = []
    for field, question_settings in QUESTIONS.items():
        if field not in sources_by_field:
            continue
        questions.append({
            "field": field,
            **question_settings,
            "source_refs": sorted(sources_by_field[field]),
        })
    return questions
