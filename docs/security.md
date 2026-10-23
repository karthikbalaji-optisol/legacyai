# LegacyLens AI — Security and Hardening Specification

## 1. Archive & Filesystem Defense

Uploaded archives pose high security risks. LegacyLens AI implements defensive safeguards:

- **Path Traversal Defense**: All entry paths inside ZIP archives are checked. Entries containing `..` or leading `/` are immediately rejected with `SecurityValidationError`.
- **Sandbox Boundary Enforcement**: Decompressed file targets must resolve to a subpath of the designated temporary extraction sandbox.
- **Symlink Protection**: Unix symlink bitmasks (`0o120000`) are checked and rejected.
- **Decompression Bomb Mitigation**: Enforces `MAX_FILE_COUNT` (1,000 files) and `MAX_SINGLE_FILE_SIZE_BYTES` (5 MB), with maximum decompressed archive size caps.
- **Binary Exclusion**: Dangerous extensions (`.exe`, `.dll`, `.so`, `.bin`, `.key`, `.pem`, `.env`) are excluded from extraction and processing.

## 2. Model Context & Prompt Injection Defense

- **Untrusted Input Treatment**: Code comments, READMEs, and source string literals are treated as untrusted data.
- **No Command Execution**: Uploaded code, build scripts, `.csproj` targets, and `.bat` files are never executed.
- **Isolated Model Transports**: Code snippets sent to Amazon Bedrock use authenticated TLS transports with least-privilege IAM roles.

## 3. Human-in-the-Loop Governance

- **Zero LLM Self-Approval**: A model is never permitted to approve its own generated requirements.
- **Explicit Review Gate**: Requirements require manual review and sign-off by a designated business analyst or architect.
- **Audit Logging**: Every review decision (approval, rejection, revision request) is logged to the `review_decisions` table with timestamps, reviewer identity, and notes.
