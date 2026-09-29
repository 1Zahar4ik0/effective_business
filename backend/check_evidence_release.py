import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'frontend/public'
DATA = json.loads((PUBLIC/'official/20260929/manifest.json').read_text(encoding='utf8'))

class EvidenceReleaseTests(unittest.TestCase):
    def test_all_documents_match_archive_and_manifest(self):
        self.assertEqual(len(DATA['documents']), 7)
        for d in DATA['documents']:
            raw = (PUBLIC/d['file'].lstrip('/')).read_bytes()
            self.assertTrue(raw.startswith(b'%PDF'))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), d['sha256'])
            archived = ROOT/'data/official/sources/user-20260929'/f"{d['id']}.pdf"
            self.assertEqual(raw, archived.read_bytes())

    def test_grant_limits_are_distinct_from_general_programme_caps(self):
        facts={x['id']:x for x in DATA['grant_limits']}
        self.assertEqual([r['amount'] for r in facts['farm']['rows']], ['5000000.00','8000000.00','10000000.00'])
        self.assertEqual([r['amount'] for r in facts['agromotivator']['rows']], ['4500000.00','4000000.00'])
        self.assertEqual(facts['agroprogress']['rows'][0]['amount'],'16853932.59')
        self.assertTrue(all(f['source']=='186-pr' for f in facts.values()))

    def test_historical_bundle_does_not_change_round(self):
        m=json.loads((ROOT/'data/official/sources/user-20260929/manifest.json').read_text(encoding='utf8'))
        self.assertEqual(m['agroprogress_bundle_round'],'26-009-R0164-1-0113')

    def test_original_programme_and_insurance_not_claimed_current(self):
        docs={d['id']:d for d in DATA['documents']}
        self.assertIn('489',docs['521']['scope'])
        self.assertIn('не включён',docs['489']['scope'])
        self.assertIn('не завершена',docs['209-pr']['scope'])

if __name__=='__main__': unittest.main(verbosity=2)
