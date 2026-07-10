# Ronda Internal Tools

Off-Platform Activity Tracker + Knowledge Base, backed by a real shared
database (Postgres on Railway). Everyone who signs in sees the same data —
this is not a per-browser or per-file thing.

## What's inside

- `app.py` — the whole backend (Flask): login, the tracker API, the
  knowledge base API.
- `templates/login.html` — sign-in page (name + shared team password).
- `templates/index.html` — the Off-Platform Activity Tracker.
- `templates/kb.html` — the Knowledge Base.
- `requirements.txt` — Python packages Railway needs to install.
- `Procfile` — tells Railway how to start the app.

## Deploying on Railway

1. Push this whole folder to a new GitHub repository.
2. In your Railway project (the one with the Postgres database already
   added), click **New** → **GitHub Repo**, and select this repository.
3. Once it's linked, go to the new service's **Variables** tab and add:
   - `SECRET_KEY` — any long random string (used to secure login sessions).
   - `TEAM_PASSWORD` — the password your team will use to sign in.
   - `DATABASE_URL` — only add this manually if Railway hasn't already
     linked it automatically from the Postgres service in the same
     project. If Postgres is in the same project, Railway usually wires
     this up for you.
4. Go to the service's **Settings** tab → **Generate Domain** to get a
   public URL (something like `yourapp.up.railway.app`).
5. Open that URL, sign in with your name + the `TEAM_PASSWORD` you set,
   and you're in.

Share that one URL with Katy, Ibra, and Dimitra. Everyone signs in with
their own name and the same shared password — everyone sees the same
tracker and knowledge base, live.

## Running locally (optional, for testing before you deploy)

```
pip install -r requirements.txt
SECRET_KEY=devsecret TEAM_PASSWORD=devpass python app.py
```

Then open http://127.0.0.1:5050 — without a `DATABASE_URL` set, it falls
back to a local SQLite file for quick testing, so you don't need Postgres
running locally just to look around.

## Notes on the shared team password

This uses one shared password for everyone (simplest to set up). It's
enough to keep the tracker off the open internet, but it isn't
per-person login security — anyone with the password and URL can act as
anyone by typing any name in. If you later want individual accounts per
person, that's a bigger change (proper user accounts) I can build when
you're ready for it.
