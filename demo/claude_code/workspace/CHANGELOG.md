# Changelog

Every notable change, newest first ([Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
[SemVer](https://semver.org/)). Each change adds its line under Unreleased; `tools/release/release`
dates them at release time. Spec: knowledge/policies/engineering.md

## [Unreleased]

### Added
- Idea Board scaffold: Fresh 2 + Vite app in `app/`, Hono API under `/api` with `GET /api/health`.
- Ideas API on Deno KV: `POST /api/ideas` with strict validation (stable `{error, field, reason}`), `GET /api/ideas`, `GET /api/ideas/:id`.
