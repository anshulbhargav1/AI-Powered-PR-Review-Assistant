# Testing Standards

Standards enforced by the testing review agent. Injected via RAG retrieval into the
agent prompt.

## Coverage expectations
- Every new public function or method must have at least one test in the same diff.
  New production code with zero test changes is a finding.
- Every new conditional branch (if/else, try/except, match arm) must be covered by a
  test that exercises it. Uncovered branches on error paths are a common finding.

## Assertion quality
- Tests must assert on observable behavior (return values, DB state, emitted events),
  not on internal implementation details (private attributes, mock call counts as the
  only assertion).
- `assert x` (truthiness only) on a non-boolean value is a weak assertion; assert on
  the actual expected value or shape.
- One meaningful behavior per test. Tests that mix many unrelated assertions make
  failures hard to diagnose.

## Edge cases
- Every test suite for a function that accepts collections must cover: empty input,
  single-element input, and a "large" input. Missing empty-input tests is a finding.
- Every test suite for a function that can raise must cover at least one raising path.

## Test hygiene
- No `time.sleep` in tests - use explicit synchronization, fake clocks, or event-based
  waits. `time.sleep` is a flake-source finding.
- No real network I/O in unit tests - use recorded fixtures, `responses`, or
  `respx`. Real network calls are a finding.
- Tests must not depend on order. Shared mutable module-level state used across tests
  is a finding.

## Structure
- Test names must describe the scenario and the expected outcome
  (`test_get_orders_returns_empty_when_user_has_none`), not just the function under
  test (`test_get_orders`).
- Prefer arrange/act/assert structure with visual separation. Test methods longer than
  ~30 lines usually need to be split.
