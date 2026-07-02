# API Key Handling Policy

This packet does not request, create, find, use, print, or store any TruMedia key, token, password, or credential.

## Policy

1. Prefer vendor-generated sample exports for first-pass source admission.
2. Do not attempt API access unless TruMedia grants written authorization.
3. If API access is approved, credentials must be provided by TruMedia or an approved customer admin through a secure channel.
4. Credentials must never be committed to git, written into docs, copied into tickets, printed in logs, or embedded in scripts.
5. Store credentials only in an approved local secrets location or environment variable outside the repository.
6. Use least privilege and rotate credentials according to vendor guidance.
7. Mask credentials in logs and screenshots.
8. Do not place credentials in query strings that may be copied into logs unless TruMedia requires it and the request path is approved.
9. If any local key, token, password, or credential value is discovered, stop and report `possible secret exposure` without printing the value.

## TruMedia-Specific Note

Public TruMedia baseball help documentation describes a pattern where a master token is provided by TruMedia and used to create temporary tokens. That public baseball documentation is not NFL access approval. For NWR, it only establishes the policy expectation that any TruMedia credential must come from TruMedia or an approved customer admin and remain private.

## Allowed In Future Approved Lane

- Reference a secret by environment variable name.
- Record that TruMedia provides credentials under a Customer License.
- Record credential rotation and storage requirements.
- Commit sanitized schema receipts and validation results when rights permit.

## Disallowed

- Discovering endpoints by probing.
- Creating trial credentials without approval.
- Using another user's credentials.
- Scraping behind login.
- Printing tokens, passwords, request headers, signed URLs, or credential-bearing query strings.
- Committing `.env`, local secrets, raw API payloads, cache files, or credentialed exports.

