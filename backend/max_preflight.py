"""Safe, read-only MAX readiness check. No tokens, launch data or response bodies in output."""
import json
import ssl
import sys
from urllib.parse import urlsplit
import httpx
from app.config import settings

def check(config, transport=None):
    report = {'token_configured': bool(config.max_bot_token),
              'webhook_secret_configured': bool(config.max_webhook_secret),
              'miniapp_link_configured': bool(config.max_app_url),
              'editor_ids_configured': bool(config.max_admin_ids),
              'https_origin_configured': urlsplit(config.public_origin).scheme == 'https',
              'bot_api': 'not_configured', 'webhook_registered': False,
              'real_launch_test': 'not_performed'}
    if not config.max_bot_token:
        return report
    if config.max_api_base.rstrip('/') != 'https://platform-api2.max.ru':
        report['bot_api'] = 'blocked_unreviewed_api_origin'
        return report
    try:
        with httpx.Client(base_url=config.max_api_base, headers={'Authorization': config.max_bot_token},
                          verify=ssl.create_default_context(cafile=config.max_ca_bundle or None),
                          timeout=15, follow_redirects=False, trust_env=False, transport=transport) as client:
            response = client.get('/me')
            if response.status_code != 200:
                report['bot_api'] = f'http_{response.status_code}'
                return report
            if response.json().get('is_bot') is not True:
                report['bot_api'] = 'invalid_bot_response'
                return report
            report['bot_api'] = 'authenticated'
            subscriptions = client.get('/subscriptions')
            report['subscriptions_api'] = subscriptions.status_code
            if subscriptions.status_code == 200:
                expected = config.public_origin.rstrip('/') + '/api/max/webhook'
                report['webhook_registered'] = any(s.get('url') == expected for s in subscriptions.json().get('subscriptions', []))
    except Exception:
        # Never print an exception: upstream messages may contain credentials or user details.
        report['bot_api'] = 'network_tls_or_invalid_response'
    return report

if __name__ == '__main__':
    try:
        result = check(settings())
    except Exception:
        print('Некорректная конфигурация. Значения и секреты скрыты.')
        sys.exit(2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['bot_api'] == 'authenticated' else 2)
