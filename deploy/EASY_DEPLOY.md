# Easy deploy — Render (API) + Vercel (frontend)

Free hobby tiers. RDS stays on AWS (eu-north-1).

---

## Architecture

```
Vercel (frontend)  →  Render (FastAPI Docker)  →  AWS RDS (database-1)
                              ↓
                         OpenAI API
```

---

## Part 1 — Allow Render to reach RDS

1. AWS Console (personal account `761186487372`) → **RDS** → `database-1`
2. **VPC security group** → **Inbound rules** → **Edit**
3. Ensure **PostgreSQL 5432** from **`0.0.0.0/0`** exists (demo only; password still required)
4. **Publicly accessible: Yes** on RDS

---

## Part 2 — Render (API)

1. https://render.com → sign up with **GitHub**
2. **New +** → **Web Service** → connect repo **cricchat**
3. Settings:

| Field | Value |
|-------|--------|
| Name | `cricchat-api` |
| Region | **Frankfurt (EU Central)** — closer to Stockholm RDS |
| Branch | `main` |
| Root Directory | *(leave empty — repo root)* |
| Runtime | **Docker** |
| Dockerfile Path | `./Dockerfile` |
| Instance type | **Free** |

4. **Environment variables:**

| Key | Value |
|-----|--------|
| `DATABASE_URL` | `postgresql://postgres:YOUR_PASSWORD@database-1.ch8wa2ai4vzv.eu-north-1.rds.amazonaws.com:5432/cricchat?sslmode=require` |
| `OPENAI_API_KEY` | from local `.env` |
| `OPENAI_MODEL` | `gpt-4o-mini` |
| `CORS_ORIGINS` | `http://localhost:3000` *(update after Vercel)* |
| `XDG_CACHE_HOME` | `/app/.cache` |

5. **Create Web Service** — first deploy ~10–15 min (Docker + Chroma build)
6. Copy URL: `https://cricchat-api.onrender.com` (yours may differ)

### Test Render

```bash
curl https://YOUR_RENDER_URL/health
curl -X POST https://YOUR_RENDER_URL/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Kohli strike rate in ODI"}'
```

---

## Part 3 — Vercel (frontend)

1. https://vercel.com → sign up with **GitHub**
2. **Add New Project** → import **cricchat**
3. **Root Directory:** `frontend`
4. Framework: **Next.js** (auto)
5. **Environment variable:**

| Name | Value |
|------|--------|
| `NEXT_PUBLIC_API_URL` | `https://YOUR_RENDER_URL` (no trailing slash) |

6. **Deploy**

7. Open site: `https://your-app.vercel.app`

---

## Part 4 — Fix CORS

1. **Render** → `cricchat-api` → **Environment**
2. Set `CORS_ORIGINS` to your Vercel URL, e.g. `https://cricchat.vercel.app`
3. **Manual Deploy** → wait for redeploy

---

## Done checklist

- [ ] Render `/health` returns ok
- [ ] Render `/chat` returns Kohli ~93.8
- [ ] Vercel site loads
- [ ] Chat works in browser

---

## Costs

| Service | Cost |
|---------|------|
| Render Free | $0 (sleeps when idle) |
| Vercel Hobby | $0 |
| RDS free tier | $0 first ~12 months |
| OpenAI | Pay per use |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Render build fails | Check Render logs; Dockerfile at repo root |
| DB connection error | RDS SG `0.0.0.0/0` on 5432, public access Yes |
| CORS in browser | `CORS_ORIGINS` = exact Vercel URL |
| Slow first chat | Render waking from sleep — wait 30–60s |
