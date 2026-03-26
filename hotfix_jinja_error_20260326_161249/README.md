# Jinja2 Template Error Hotfix
Generated: 2026-03-26 16:12:49

## Problem
Live environment showing Jinja2 template syntax error:
```
jinja2.exceptions.TemplateSyntaxError: expected token ',', got 'for'
```

## Solution
Simplified complex Jinja2 expressions in milk templates to avoid parsing issues.

## Files Fixed
- `templates/milk/summary_traditional.html` - Simplified complex expressions
- `modules/milk.py` - Added pre-calculated values for template

## Deployment
1. Upload this hotfix package to live server
2. Run: `./apply_hotfix.sh`
3. Verify milk entries page works

## Verification
After applying hotfix:
- [ ] Milk entries page loads without errors
- [ ] Milk summary page displays correctly
- [ ] All calculations show properly
- [ ] No Jinja2 errors in logs

## Root Cause
Complex nested Jinja2 expressions can cause parsing issues in some environments.
By pre-calculating values in Python and simplifying template expressions,
we avoid these parsing errors.
