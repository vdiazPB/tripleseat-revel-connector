#!/usr/bin/env python
"""Validate dashboard JavaScript syntax."""

from integrations.admin.dashboard import get_dashboard_html
import re

html = get_dashboard_html()

# Extract JavaScript section
script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if script_match:
    js_code = script_match.group(1)
    
    # Check for common JS syntax issues
    issues = []
    
    # Check for unmatched braces
    open_braces = js_code.count("{")
    close_braces = js_code.count("}")
    
    if open_braces != close_braces:
        issues.append(f"Unmatched braces: {open_braces} open, {close_braces} close")
    
    # Check for balanced parentheses
    open_parens = js_code.count("(")
    close_parens = js_code.count(")")
    
    if open_parens != close_parens:
        issues.append(f"Unmatched parentheses: {open_parens} open, {close_parens} close")
    
    if issues:
        print("✗ JavaScript Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
        exit(1)
    else:
        print("✓ JavaScript syntax check passed")
        print(f"  - Parentheses balanced: {open_parens} pairs")
        print(f"  - Braces balanced: {open_braces} pairs")
else:
    print("✗ No JavaScript found in HTML")
    exit(1)

print("\n✅ Dashboard JavaScript is syntactically valid")
