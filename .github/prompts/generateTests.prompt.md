---
name: generateTests
description: Generate comprehensive test coverage
argument-hint: Select function or class to test
tools: [ 'edit', 'search', 'run_in_terminal' ]
mode: agent
---

Generate tests for {{argument}}.

## Test Coverage

- **Happy path**: Normal operation scenarios
- **Edge cases**: Boundary conditions, empty inputs
- **Error handling**: Invalid inputs, exceptions

## Output

Provide complete test file with:
1. Test setup/fixtures
2. Individual test cases
3. Assertions with clear expectations
4. Cleanup if needed
