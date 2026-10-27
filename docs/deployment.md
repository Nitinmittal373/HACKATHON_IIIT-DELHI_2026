# Deploying NeevCheck

NeevCheck is two services: the **API** (FastAPI) on Render and the **web app** (Next.js) on Vercel. Deploy the API first, because the web app needs its address.

You need: a GitHub account with this repository, a [Render](https://render.com) account, a [Vercel](https://vercel.com) account and your TinyFish API key (<https://agent.tinyfish.ai/api-keys>). Keep the key to yourself: it only ever goes into the Render dashboard.

NeevCheck covers Uttar Pradesh RERA projects. Nothing here selects a state or a set of sources: every deployment reads UP-RERA, the company registry, group companies, lender notices, insolvency, land dues, consumer cases and news.

Make one long random string for the webhook secret first, for example:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 1. The API on Render

1. Sign in to Render and click **New +** → **Blueprint**.
2. Connect your GitHub account if asked, pick this repository and click **Connect**.
3. Render reads `render.yaml` and shows one service, `neevcheck-api`. Give the Blueprint a name and click **Apply**.
4. Render asks for the values marked `sync: false`. Fill in:
   - `TINYFISH_API_KEY`: paste your TinyFish key.
   - `FRONTEND_ORIGINS`: leave a placeholder such as `https://example.com` for now; you set the real value in step 3 below.
   - `WEBHOOK_SECRET`: paste the random string you made.
   - `PUBLIC_BASE_URL` (optional): this service's own address, for example `https://<your-service>.onrender.com`. With `WEBHOOK_SECRET` set, watching a project also creates TinyFish Monitors that call the webhook; leave it empty to keep the weekly Sentinel schedule only.
   - `SITE_URL` (optional): the web app's address, for example `https://<your-app>.vercel.app`. Alert emails end with a link to its `/alerts/stop` page.
   - `DATABASE_URL`, `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`: leave empty (see "Keeping data" and "Email" below).
5. Click **Apply** and wait for the first deploy (a few minutes). When the log says the service is live, open `https://<your-service>.onrender.com/api/health`. It must answer `{"status":"ok"}`.
6. Copy the service address (`https://<your-service>.onrender.com`). You need it next.

### Keeping data (recommended)

Without a database, the API keeps checks and Sentinel watches in a SQLite file that Render deletes on every deploy.

1. In Render click **New +** → **PostgreSQL**, name it `neevcheck-db`, pick the free plan and click **Create Database**.
2. When it is ready, open it and copy the **Internal Database URL**.
3. Open `neevcheck-api` → **Environment**, set `DATABASE_URL` to that URL and click **Save, rebuild and deploy**. The API creates its tables itself.

The free Render database expires after a period set by Render; use a paid plan for anything you want to keep.

### Email (optional)

Alerts always show on the Alerts page. To also email them, set `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` and `SMTP_FROM` under **Environment** (any SMTP provider works; the API uses port 587 with STARTTLS). Leave them empty to send nothing.

> **Redeploying the API.** The Render service was created from the public repository URL, so Render does **not** deploy on its own when `main` changes (the `autoDeploy` line in `render.yaml` applies only to services made from the Blueprint). After each merge: **Render → `neevcheck-api` → Manual Deploy → Deploy latest commit**. Vercel does deploy on every push to `main`.

## 2. The web app on Vercel

1. Sign in to Vercel and click **Add New…** → **Project**.
2. Import this repository.
3. Under **Configure Project** click **Edit** next to **Root Directory**, choose `frontend` and confirm. Vercel detects Next.js; leave the build settings as they are.
4. Open **Environment Variables** and add:
   - `NEXT_PUBLIC_API_URL` = the Render address from step 1.6, with no trailing slash.
   - `NEXT_PUBLIC_SITE_URL` = the address Vercel will give the site. If you do not know it yet, deploy once, copy the address Vercel shows, then add this variable and redeploy.
5. Click **Deploy**. When it finishes, open the address.

## 3. Tell the API which site may call it

1. Go back to Render → `neevcheck-api` → **Environment**.
2. Set `FRONTEND_ORIGINS` to the Vercel address, for example `https://neevcheck-up.vercel.app`. If you also use your own domain, list both, separated by a comma. No trailing slash.
3. Click **Save, rebuild and deploy**.

Until this is set, the browser blocks every call to the API (CORS), so the live check cannot start.

## 4. Check that it works

1. Open the Vercel address and search for `UPRERAPRJ8334`. The confirm screen should show the project.
2. Start the check. The Agent Cam should fill with findings. A live check runs paid browser agents, so do this on purpose.
3. Open `https://<your-service>.onrender.com/api/health` again, and `https://<your-service>.onrender.com/docs` for the API documentation.

## Sign in with Google (optional)

Without these settings the site works as before and `/login` says sign-in is not set up. To turn it on:

1. In Google Cloud, create an OAuth client (type **Web application**) with the authorised redirect URIs `https://neevcheck-up.vercel.app/api/auth/callback/google` and, for local work, `http://localhost:3000/api/auth/callback/google`.
2. On **Vercel** (Project → Environment Variables) add `AUTH_SECRET` (a long random string), `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET`, `AUTH_BRIDGE_SECRET` (another long random string) and `NEXTAUTH_URL` (the site's address). Redeploy.
3. On **Render** add `AUTH_BRIDGE_SECRET` with the same value as on Vercel, then redeploy the API.

Never put these in a `NEXT_PUBLIC_` variable.

## Weekly Sentinel re-checks

The API re-checks watched projects every `SENTINEL_INTERVAL_HOURS` (168, one week) while it is running. On Render's free plan the service sleeps when idle, which also pauses that schedule. To re-check on time, call the webhook from an external cron (for example a free cron service, or a scheduled GitHub Action):

```bash
curl -X POST https://<your-service>.onrender.com/api/sentinel/run \
  -H "X-Webhook-Secret: <your WEBHOOK_SECRET>"
```

It answers `202`. Calls without the right secret get `401`.

## Cost and safety settings

- `MAX_CHECKS_PER_DAY` (default 30) is the most checks the API will start per day, Sentinel included. Lower it to cap your TinyFish spend.
- `RATE_LIMIT_PER_MINUTE` (default 6) limits checks per visitor.
- A finished check of the same project from the last 24 hours is reused, so repeat visitors cost nothing.
- Never put `TINYFISH_API_KEY` into Vercel or any `NEXT_PUBLIC_` variable: those are sent to every visitor's browser.
