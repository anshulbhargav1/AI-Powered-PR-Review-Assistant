# Code Quality Standards

These are the code quality and maintainability standards enforced by the code-quality
review agent. When retrieved by the RAG layer, they are injected into the agent's user
prompt as authoritative context.

## Error handling
- Never use bare `except:` or `except Exception: pass`. Always log the exception with
  context, or re-raise a domain-specific exception. Swallowing errors silently is a
  blocking finding.
- I/O operations (file, network, DB) must have explicit error handling and clear error
  messages that identify the failing resource.
- Return typed error results or raise; do not return `None` to mean "something went
  wrong".

## API design
- HTTP status codes must be consistent within a service: 400 for client validation, 401
  for missing auth, 403 for forbidden, 404 for missing, 409 for conflict, 422 for
  semantic validation, 500 only for genuine server-side bugs.
- Every request handler must validate its inputs (via Pydantic, a schema library, or
  explicit checks) before touching a database or external service.
- Response shapes must be stable: adding a required field to a response is a breaking
  change and requires a new endpoint version.

## Naming and structure
- Names must describe intent, not implementation (`fetch_active_user_orders` not
  `get_data`). Single-letter variables are only allowed for loop indices and math.
- Functions doing more than one clearly separable thing (>~40 lines, or multiple levels
  of nesting) must be decomposed.
- Dead code (unused imports, unreachable branches, commented-out blocks) must be
  removed before merge, not left "just in case".

## Types
- All new Python code must include type hints on public function signatures. Missing
  hints in a codebase that already uses them elsewhere is a finding.
- Do not use `Any` to bypass type errors; introduce a proper type or narrow with
  `isinstance`.

## Concurrency
- Shared mutable state accessed from multiple threads/tasks requires an explicit lock,
  queue, or atomic primitive. Reason about this in the review, do not defer to "it
  probably won't race".
