import json
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.official_notices import Announcement, SNAPSHOT, announcements


def test_public_facts_separate_from_drafts_and_eligibility(client):
    response = client.get('/api/official-announcements')
    assert response.status_code == 200
    data = response.json()
    assert len(data['items']) == 10
    assert all(x['verification_scope'] == 'announcement_facts_only' and
               x['acceptance_status'] == 'unconfirmed' for x in data['items'])
    farm = next(x for x in data['items'] if x['measure_id'] == 'saratov-farm')
    assert farm['budget_rub'] == '94292134.84'
    assert farm['recipient_limit_rub'] == '10000000.00'
    crop = next(x for x in data['items'] if x['measure_id'] == 'saratov-crop-insurance')
    assert crop['recipient_limit_rub'] is None
    assert crop['limit_status'] == 'not_set_in_announcement'
    # Facts must not promote a measure or invent an eligible saved plan.
    assert all(x['synthetic'] for x in client.get('/api/catalog').json())
    assert client.get('/api/measures/saratov-farm').status_code == 404
    assert 'rules' not in farm and 'documents' not in farm


def test_notice_end_exact_moscow_boundary_and_no_open_inference():
    end = datetime.fromisoformat('2026-09-26T22:59:00+03:00')
    before = announcements(now=end-timedelta(microseconds=1))
    at = announcements(now=datetime.fromisoformat('2026-09-26T19:59:00+00:00'))
    farm = lambda data: next(x for x in data.items if x.measure_id == 'saratov-farm')
    assert farm(before).deadline_status == 'within_notice_dates'
    assert farm(at).deadline_status == 'ended_in_notice'
    assert farm(before).acceptance_status == farm(at).acceptance_status == 'unconfirmed'
    late = announcements(now=end+timedelta(days=100))
    assert all(x.deadline_status == 'ended_in_notice' for x in late.items)


def test_notice_validation_prevents_unverified_open_and_imprecise_money():
    raw = json.loads(SNAPSHOT.read_text(encoding='utf-8'))['items'][0]
    for field, value in [('budget_rub', 0.1), ('recipient_limit_rub', '-1'), ('checked_at', '2026-09-20T12:00:00')]:
        with pytest.raises(ValidationError):
            Announcement.model_validate({**raw, field:value})
    item = deepcopy(raw)
    item['round']['state'] = 'announced'
    with pytest.raises(ValidationError):
        Announcement.model_validate(item)
    item = deepcopy(raw)
    item['recipient_limit_rub'] = None
    with pytest.raises(ValidationError):
        Announcement.model_validate(item)
    item = deepcopy(raw)
    item['source']['url'] = 'https://unreviewed.example.org/document.pdf'
    with pytest.raises(ValidationError):
        Announcement.model_validate(item)
    parsed = Announcement.model_validate(raw)
    assert parsed.budget_rub == Decimal('1763367.35')


def test_duplicate_notices_and_future_verification_are_rejected(tmp_path):
    raw = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    raw['items'].append(raw['items'][0])
    path = tmp_path/'notices.json'
    path.write_text(json.dumps(raw), encoding='utf-8')
    with pytest.raises(ValueError):
        announcements(path=path)
    with pytest.raises(ValueError):
        announcements(now=datetime.fromisoformat('2026-09-19T12:00:00+00:00'))
