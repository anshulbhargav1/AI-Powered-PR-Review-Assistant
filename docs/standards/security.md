# Security Standards

Standards enforced by the security review agent. Injected via RAG retrieval into the
agent prompt when the changed diff mentions related concepts.

## Injection
- All SQL must be parameterized. String concatenation or `%` formatting into a SQL
  string is a blocking `critical` finding, no exceptions.
- Shell/subprocess calls must pass argument lists, never a formatted string with
  `shell=True`.

## Secrets and credentials
- API keys, tokens, private keys, and passwords must never be committed to source.
  Any string that matches a credential pattern (e.g. `AKIA...`, `gsk_...`, `glpat-...`,
  `sk-...`) added in a diff is a blocking `critical` finding.
- Credentials must be loaded from environment variables or a secrets manager; hardcoded
  fallback values are not allowed.

## Authentication and authorization
- Every non-public endpoint must check authentication before doing work.
- Authorization checks must happen after the resource is resolved but before it is
  returned or modified; missing an authorization check on a resource-scoped endpoint
  is a `high` or `critical` finding depending on data sensitivity.

## Cryptography
- Use vetted libraries (`cryptography`, `bcrypt`, `argon2`) - never roll your own.
- Password hashing must use `bcrypt`, `argon2`, or `scrypt`. MD5 and SHA1 for passwords
  are blocking findings.

## Input handling
- Deserializing untrusted data with `pickle`, `yaml.load` (unsafe), or `eval` is a
  blocking `critical` finding.
- File path parameters coming from user input must be validated against traversal
  (`..`, absolute paths outside an allow-listed root).
