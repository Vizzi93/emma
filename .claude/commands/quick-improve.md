---
description: Quick improvements and fixes for eMMA - fast, focused enhancements
argument-hint: [area]
---

# Quick Improvement Command for eMMA

Fast, focused improvements for immediate impact. Use when you need quick wins without deep analysis.

## Target Area
Improvement area: $ARGUMENTS

Available areas:
- `types` - Add missing type hints (Python) or TypeScript types
- `tests` - Generate missing unit tests
- `docs` - Add missing docstrings and comments
- `errors` - Improve error handling
- `security` - Quick security fixes
- `performance` - Simple performance optimizations
- `cleanup` - Code cleanup and formatting

## Quick Improvement Workflows

### Types (`/quick-improve types`)

**Backend (Python):**
```python
# Find functions without type hints
# Add return types and parameter types
def get_service(service_id: int) -> Service:
    ...
```

**Frontend (TypeScript):**
```typescript
// Find any types and replace with proper interfaces
interface ServiceProps {
  service: Service;
  onUpdate: (id: number) => void;
}
```

Actions:
1. Scan for functions without type hints
2. Add appropriate types based on usage
3. Run mypy/tsc to verify
4. Commit with `fix(types):` prefix

### Tests (`/quick-improve tests`)

**Use api-testing and webapp-testing skills**

Actions:
1. Identify untested functions/components
2. Generate test files using skills
3. Run tests to verify
4. Target 70%+ coverage

### Docs (`/quick-improve docs`)

Actions:
1. Find public functions without docstrings
2. Add Google-style docstrings (Python)
3. Add JSDoc comments (TypeScript)
4. Update README if needed

### Errors (`/quick-improve errors`)

**Use error-handling skill**

Actions:
1. Find bare except clauses
2. Add specific exception handling
3. Improve error messages
4. Add logging for errors

### Security (`/quick-improve security`)

Actions:
1. Check for hardcoded secrets
2. Validate input sanitization
3. Review CORS settings
4. Check dependency vulnerabilities
5. Verify JWT configuration

### Performance (`/quick-improve performance`)

Actions:
1. Add database indexes for slow queries
2. Implement pagination where missing
3. Add caching for repeated calls
4. Optimize imports

### Cleanup (`/quick-improve cleanup`)

Actions:
1. Remove unused imports
2. Format code (ruff/prettier)
3. Remove dead code
4. Fix linting errors

## Execution Rules

1. **Stay Focused**: Only fix the specified area
2. **Small Changes**: Keep changes minimal and targeted
3. **Test After**: Run tests after changes
4. **Commit Often**: Use conventional commits
5. **Document**: Add brief comments for complex fixes

## Output Format

For each improvement:
```
File: path/to/file.py
Issue: Description of what was wrong
Fix: What was changed
Impact: Low/Medium/High
```

## Auto-Commit Template

After improvements, commit with:
```
fix(<area>): quick improvements for <area>

- List of changes made
- Files modified

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Now Execute

Run quick improvements for: **$ARGUMENTS**

1. Scan relevant files
2. Identify issues in target area
3. Apply fixes
4. Verify with tests/linting
5. Report changes made
