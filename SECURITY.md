# Security & Secrets Handling

## How credentials are loaded

`dashboards/app.py` reads the Groq and Tavily API keys used by the AI Copilot
page in this order:

1. Environment variable (`os.environ.get("GROQ_API_KEY", "")`, same for
   `TAVILY_API_KEY`) — the path used in deployment.
2. Fallback to `st.secrets.get(...)` for local development via
   `.streamlit/secrets.toml`.

No key is ever hardcoded in source. `.streamlit/secrets.toml` and `*.db` are
listed in `.gitignore` and have never been committed to the repository.

## Known past incident — zip export, not git

Two local zip exports of this project (for portfolio review) included
`.streamlit/secrets.toml` and `PraxisIQ.db` even though both are gitignored.
This happened because a raw folder zip does not respect `.gitignore` —
only `git` operations do. The keys included in those exports were rotated
immediately after discovery.

**Fix applied going forward:** exports are created with
`git archive -o praxisiq.zip HEAD`, which packages exactly what git tracks
and nothing else, so gitignored files can no longer leak into a shared zip.

## Local setup

To run this project locally, create your own `.streamlit/secrets.toml`
(never commit it) or set environment variables:

```bash
export GROQ_API_KEY="your_key_here"
export TAVILY_API_KEY="your_key_here"
```

The AI Copilot page runs in a degraded mode with clear on-screen messaging
if neither is set — the rest of the dashboard (Overview, Patient Analytics,
Review Intelligence, Anomaly Screening, Trust & Safety, LLM Evaluation,
Investigation Playbooks, Data Quality) has no dependency on these keys.

## Data privacy

`PraxisIQ.db` and all files under `reports/` are gitignored. The dataset
used throughout this project is synthetic/sample dental clinic data, not
real patient records — see `README.md` and `METHODOLOGY.md` for the data
provenance and the T&S-relevance framing.
