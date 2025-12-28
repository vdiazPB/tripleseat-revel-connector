#!/usr/bin/env python
"""Test authorization denial handling in webhook."""

import asyncio
from dotenv import load_dotenv
load_dotenv()
from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook

async def test_auth_denied():
    """Test that authorization denials are handled gracefully."""
    payload = {
        'event': {
            'id': '55521609',
            'site_id': '1',
            'triggered_at': '2025-12-27T10:00:00Z'
        }
    }
    result = await handle_tripleseat_webhook(
        payload, 
        'authz_test_001', 
        dry_run=True, 
        enable_connector=True
    )
    
    print('=' * 60)
    print('AUTHORIZATION DENIED TEST')
    print('=' * 60)
    print('Webhook response ok:', result.get('ok'))
    print('Authorization status:', result.get('authorization_status'))
    print('Reason:', result.get('reason'))
    print('Site ID:', result.get('site_id'))
    print('Dry run:', result.get('dry_run'))
    
    print('\n' + '=' * 60)
    print('VERIFICATION')
    print('=' * 60)
    
    checks = {
        'ok is True': result.get('ok') == True,
        'acknowledged': result.get('acknowledged') == True,
        'authorization_status is DENIED': result.get('authorization_status') == 'DENIED',
        'reason is TRIPLESEAT_AUTHORIZATION_DENIED': result.get('reason') == 'TRIPLESEAT_AUTHORIZATION_DENIED',
        'site_id preserved': result.get('site_id') == '1',
        'dry_run preserved': result.get('dry_run') == True
    }
    
    for check, passed in checks.items():
        status = '✓' if passed else '✗'
        print(f'{status} {check}')
    
    all_passed = all(checks.values())
    print('\n' + '=' * 60)
    if all_passed:
        print('✓ ALL CHECKS PASSED')
        print('Authorization denial is handled safely and transparently')
    else:
        print('✗ SOME CHECKS FAILED')
    print('=' * 60)

if __name__ == '__main__':
    asyncio.run(test_auth_denied())
