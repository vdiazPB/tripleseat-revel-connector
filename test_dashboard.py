#!/usr/bin/env python
"""Test dashboard functionality."""

from integrations.admin.dashboard import get_current_config, get_status, get_dashboard_html

print("Testing Dashboard Functionality...\n")

# Test 1: get_current_config
print("Test 1: get_current_config()")
config = get_current_config()
assert "api_credentials" in config
assert "establishment_mapping" in config
assert "sync_settings" in config
print("  ✓ Config structure valid")
print(f"  ✓ Dining Option ID: {config['establishment_mapping']['dining_option_id']}")
print(f"  ✓ Connector enabled: {config['sync_settings']['enabled']}")

# Test 2: get_status
print("\nTest 2: get_status()")
status = get_status()
assert status["status"] == "online"
assert "connector" in status
print(f"  ✓ Status: {status['status']}")
print(f"  ✓ Mode: {status['connector']['mode']}")

# Test 3: get_dashboard_html
print("\nTest 3: get_dashboard_html()")
html = get_dashboard_html()
assert len(html) > 1000
print(f"  ✓ HTML generated: {len(html)} bytes")

# Test 4: HTML content validation
print("\nTest 4: HTML Content Validation")
required_sections = [
    "System Status",
    "API Credentials",
    "Establishment Mapping",
    "Sync Settings",
    "Manual Sync",
    "TripleSeat-Revel Connector"
]
for section in required_sections:
    assert section in html, f"Missing section: {section}"
    print(f"  ✓ {section} present")

# Test 5: JavaScript validation
print("\nTest 5: JavaScript Validation")
js_functions = [
    "refreshStatus",
    "triggerSync",
    "triggerBulkSync"
]
for func in js_functions:
    assert f"function {func}" in html, f"Missing JS function: {func}"
    print(f"  ✓ {func}() function present")

# Test 6: API endpoints validation
print("\nTest 6: HTML Structure Validation")
required_elements = [
    'id="connStatus"',
    'id="connMode"',
    'id="eventId"',
    'id="lookback"',
    'id="syncResult"',
    'fetch("/admin/api/status")',
    '/admin/api/sync/trigger'
]
for element in required_elements:
    assert element in html, f"Missing element: {element}"
    print(f"  ✓ {element} present")

print("\n✅ All Dashboard Tests Passed!")
print("\nDashboard is ready for production deployment.")
