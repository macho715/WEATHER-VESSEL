# Weather Vessel Logistics Control Tower

A Next.js 15 application that powers a marine logistics control tower. It merges vessel scheduling, marine forecasts, and daily notifications to coordinate twice-daily operations in the Asia/Dubai timezone.

## ✨ Highlights

- **Stabilised APIs** – `/api/marine` now includes guarded fetch with timeout, retries, circuit breaker, and stale-cache fallback.
- **Automated Daily Reports** – `/api/report` fans out to Slack and email and records results for diagnostics.
- **Operations Dashboard** – Real-time marine weather intelligence with vessel tracking and risk assessment.
- **Scheduler Ready** – Vercel Cron triggers and a self-hosted Node scheduler script keep the 06:00 / 17:00 (Asia/Dubai) reporting cadence.

## 🛠️ Requirements

| Tool       | Version                        |
| ---------- | ------------------------------ |
| Node.js    | 18+ (tested on 20.x)           |
| npm / pnpm | npm 10+ or pnpm 8+             |
| TypeScript | Included via `devDependencies` |
| Vitest     | Included via `devDependencies` |

## 🚀 Getting Started

```bash
npm install
npm run dev
# visit http://localhost:3000
```

## 🔐 Environment Variables

Create a `.env.local` (for Next.js) or `.env` (for tooling) file based on `.env.local.example`.

```dotenv
SLACK_WEBHOOK_URL= # Incoming webhook for Slack notifications
RESEND_API_KEY=    # Resend API key for transactional email
REPORT_SENDER=no-reply@example.com
REPORT_RECIPIENTS=ops@example.com,owner@example.com
REPORT_TIMEZONE=Asia/Dubai
REPORT_ENDPOINT=http://localhost:3000/api/report
REPORT_LOCK_PATH=.report.lock
```

> ℹ️ `REPORT_TIMEZONE` defaults to Asia/Dubai. Keep Slack, email, scheduler, and dashboards aligned to this timezone for consistent reporting windows.

## 📡 Core Commands

```bash
npm run lint         # ESLint (Next.js configuration)
npm run typecheck    # tsc --noEmit
npm run test         # vitest run --coverage
npx prettier --check .
```

All four checks must succeed before deploying. Vitest coverage is kept ≥ 70% through dedicated tests for notifier success/failure paths, the report route, assistant/briefing flows, and the guarded fetch utility.

## 🧪 Local Verification

### Triggering a Report

```bash
curl -s http://localhost:3000/api/report?slot=am | jq
```

Expect a JSON payload with `ok`, `sent`, `slot`, `generatedAt`, and `sample` fields. Slack/email failures surface per channel without breaking the overall `ok` flag when at least one delivery succeeds.

### PowerShell Health Check

```powershell
pwsh ./scripts/health-check.ps1
pwsh ./scripts/health-check.ps1 -Path "http://localhost:3001/api/health"
```

The script auto-detects the listening Node port (via `WEATHER_PORT`, `Get-NetTCPConnection`, or `netstat` fallback). Responses are printed as JSON; failures show a warning and non-zero exit code.

## ⏰ Scheduling Options

### Vercel (Serverless)

`vercel.json` registers two Cron jobs:

| Local Slot       | UTC Cron     | Endpoint              |
| ---------------- | ------------ | --------------------- |
| 06:00 Asia/Dubai | `0 2 * * *`  | `/api/report?slot=am` |
| 17:00 Asia/Dubai | `0 13 * * *` | `/api/report?slot=pm` |

Deploying to Vercel automatically keeps the reporting rhythm without extra infrastructure.

### Self-hosted Node Scheduler

Use the provided script when running the app outside Vercel:

```bash
# Build once (optional)
npm run build

# Start the Next.js server (or ensure it is already running)
npm run start

# In a separate process
node scripts/scheduler.ts
```

The scheduler honours `REPORT_ENDPOINT`, `REPORT_TIMEZONE`, and writes a lock file (`REPORT_LOCK_PATH`) to avoid duplicate executions when a slot already ran within the TTL window.

## 🧭 Operations Guide

1. **Before each shift** – Run the PowerShell health check (Windows) or `curl` the `/api/health` endpoint to ensure the deployment is reachable.
2. **Manual report** – Trigger `curl http://localhost:3000/api/report?slot=am` for ad-hoc dispatches; Slack/email partial failures surface within the `sent` array.
3. **Scheduler monitoring** – Watch the scheduler logs (`[scheduler]`) to confirm that both 06:00 and 17:00 slots fire. Delete the lock file if you intentionally need to rerun a slot.

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
