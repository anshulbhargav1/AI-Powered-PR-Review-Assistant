# Performance Standards

Standards enforced by the performance review agent. Retrieved into the agent prompt
when the diff mentions databases, loops, caches, or async I/O.

## Database access
- N+1 query patterns (a query inside a loop that iterates over rows from another
  query) are a blocking finding. Batch, join, or eager-load instead.
- Queries returning collections must be bounded (explicit `LIMIT`, pagination, or a
  documented small fixed set). Unbounded `SELECT *` on a user-visible table is a
  finding.
- Long-running write transactions must be kept short - do not perform external HTTP
  calls or LLM calls while holding a DB transaction.

## Algorithms
- Nested loops over user-controlled inputs are a finding if a linear or logarithmic
  alternative exists (set/dict lookup, sorted + binary search, hash join).
- Repeated computation inside a loop that could be hoisted out is a finding.

## Memory
- Unbounded caches (a `dict` that only ever grows) must have an eviction policy or a
  documented maximum size.
- Reading an entire large file/response into memory when streaming would work is a
  finding for anything user-uploaded or externally supplied.

## Async I/O
- Blocking calls (`requests`, sync DB drivers, `time.sleep`) inside an `async` function
  block the event loop and are a finding. Use the async equivalent or a thread pool.
- Sequential `await` calls that are independent should be `asyncio.gather`ed.
