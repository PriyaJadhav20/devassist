# Security checklist

## Secrets and credentials
Never commit API keys, passwords or tokens. Load credentials from environment variables or a secret manager and rotate anything that leaked.

## SQL injection and parameterized queries
Always pass user input to the database as query parameters. Never build SQL with f-strings, string concatenation or format.

## Eval exec arbitrary code
Do not call eval or exec on input. Parse data with json or ast.literal_eval.

## Shell command injection and subprocess
Call subprocess with an argument list and shell=False. Validate any value that reaches a command line.

## Hashing passwords and weak hash functions
Use bcrypt, scrypt or argon2 for passwords and SHA-256 or stronger for integrity. MD5 and SHA-1 are not acceptable.

## TLS certificate verification
Never disable certificate verification. Install the proper CA bundle instead.

## Unsafe deserialization pickle yaml
Do not unpickle untrusted data. Use json or yaml.safe_load.

## XSS innerHTML sanitize
Render user content with textContent. Sanitize HTML before assigning innerHTML.
