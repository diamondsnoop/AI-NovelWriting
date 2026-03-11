# Codex Novel System

First-pass project skeleton for a long-form novel creation system.

## Current scope

The current skeleton implements a minimal structural chain:

- `init`
- `plan`
- `write`
- `resume`
- `query`

The first version keeps these architectural rules:

- `workflow` is the only flow controller
- model calls go through `agent_runtime -> llm_client`
- `llm_client` loads concrete providers from `foundation.providers`
- project state and task state are stored separately

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
novel init demo --root projects/demo
novel plan --project projects/demo --chapter 1
novel write --project projects/demo --chapter 1
novel resume --project projects/demo
novel query --project projects/demo --type progress
```

## Provider selection

The default provider is `mock`.

You can configure providers either through shell environment variables or a project-root `.env` file.

Environment variables:

```bash
set NOVEL_LLM_PROVIDER=openai
set NOVEL_LLM_MODEL=gpt-5
set OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
set NOVEL_LLM_TIMEOUT_SECONDS=150
set NOVEL_PLAN_TIMEOUT_SECONDS=150
set NOVEL_WRITE_TIMEOUT_SECONDS=240
set NOVEL_WRITE_MAX_RETRIES=0
set NOVEL_WRITE_TARGET_CHARS=1000
set NOVEL_REVIEW_TIMEOUT_SECONDS=150
set NOVEL_SUMMARY_TIMEOUT_SECONDS=150
set NOVEL_EXTRACTION_TIMEOUT_SECONDS=150
set NOVEL_CHARACTER_PROFILE_TIMEOUT_SECONDS=150
set NOVEL_LLM_MAX_RETRIES=2
set OPENAI_API_KEY=...
```

If `openai` is selected, install the `openai` package first.
`OPENAI_BASE_URL` is optional for official OpenAI and required for third-party OpenAI-compatible providers.

Example `.env`:

```env
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://9985678.xyz/v1
NOVEL_LLM_PROVIDER=openai
NOVEL_LLM_MODEL=gpt-5.4
NOVEL_LLM_TIMEOUT_SECONDS=150
NOVEL_PLAN_TIMEOUT_SECONDS=150
NOVEL_WRITE_TIMEOUT_SECONDS=240
NOVEL_WRITE_MAX_RETRIES=0
NOVEL_WRITE_TARGET_CHARS=1000
NOVEL_REVIEW_TIMEOUT_SECONDS=150
NOVEL_SUMMARY_TIMEOUT_SECONDS=150
NOVEL_EXTRACTION_TIMEOUT_SECONDS=150
NOVEL_CHARACTER_PROFILE_TIMEOUT_SECONDS=150
NOVEL_LLM_MAX_RETRIES=2
```
