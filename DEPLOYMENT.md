# StockSensei Deployment

Recommended setup:

- Frontend: Netlify
- Backend: Railway

## Backend on Railway

1. Push this repo to GitHub.
2. Go to Railway and create a new project from the GitHub repo.
3. Railway should detect Python.
4. Use this start command if Railway asks:

```bash
gunicorn --chdir backend app:app
```

5. Add environment variables in Railway:

```bash
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4.1-mini
ASK_TEMPERATURE=0.35
ASK_MAX_TOKENS=450
SUPABASE_URL=your_supabase_url
SUPABASE_SECRET_KEY=your_supabase_service_role_or_backend_key
```

6. Generate a public Railway domain.
7. Test:

```text
https://your-railway-url.up.railway.app/health
```

## Frontend on Netlify

1. Go to Netlify and create a new site from the same GitHub repo.
2. Set:

```text
Base directory: leave blank
Build command: leave blank
Publish directory: frontend
```

3. After the backend is live, edit `frontend/config.js`:

```js
window.STOCKSENSEI_API_BASE = "https://your-railway-url.up.railway.app";
```

4. Commit and push again.

## Local Development

For local Flask testing, leave `frontend/config.js` empty. The app will fall back to:

```text
http://127.0.0.1:5000
http://localhost:5000
```
