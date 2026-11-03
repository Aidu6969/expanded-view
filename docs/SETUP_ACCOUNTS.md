# Expanded View: one-time account setup (owner)

Everything here is done once by you (Ahadu). Never paste passwords, keys or tokens into a chat. Keys go
only into the **environment variables of the cloud environment the scheduled tasks run in**, where only the
runs can read them. You can revoke any of them at any time.

Two kinds of settings are needed:

- **Allowed domains:** on claude.ai (in a web browser): Settings → Capabilities → allowed domains.
  The runs can only reach websites on this list.
- **Environment variables:** in the settings of the cloud environment used by the Expanded View
  scheduled tasks. If you can't find where to add them, ask me in a session and we'll find it together.

| What | Allowed domains to add | Environment variables |
|---|---|---|
| 1. Narrator + sound effects (ElevenLabs) | `api.elevenlabs.io` | `ELEVENLABS_API_KEY` |
| 2. Direct YouTube uploads | `oauth2.googleapis.com`, `www.googleapis.com`, `youtube.googleapis.com` | `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` |
| 3. Licensed photos (long-form) | `commons.wikimedia.org`, `upload.wikimedia.org` | none |
| 4. Licensed video clips (long-form) | `api.pexels.com`, `videos.pexels.com`, `images.pexels.com` | `PEXELS_API_KEY` |

Until step 1 is done, scheduled runs **stop without posting** and message you, because every video must use
voice B (Brian). Steps 2–4 are optional: without step 2, YouTube keeps going through Metricool; without 3–4,
no long-form videos can be built.

---

## 1. ElevenLabs (narrator "Brian" + realistic sound effects), about 5 minutes

1. Sign up at elevenlabs.io. Pick a **paid** plan (paid plans include commercial use) with at least
   **~100,000 characters a month**: about 60 Shorts (~1,000 characters each) + 4 long videos (~9,000 each),
   plus a little for sound effects. Check elevenlabs.io/pricing for the current plans.
2. Profile (bottom left) → **API Keys** → Create API key. Name it "Expanded View". Give it access to
   **Text to Speech**, **Sound Effects** and **User (read)**. Copy the key.
3. Add the environment variable `ELEVENLABS_API_KEY` = that key.
4. Add the allowed domain `api.elevenlabs.io`.

The voice is the premade "Brian" (`nPczCjzI2devNBz1zQrb`), so nothing to set up inside ElevenLabs.

## 2. Direct YouTube uploads (skip Metricool for YouTube), about 15 minutes

Google says videos uploaded through your own, unverified API project are **not** forced to private, and
allows up to 100 uploads a day.

1. Go to console.cloud.google.com → create a project called "Expanded View Uploader".
2. **APIs & Services → Library** → search "YouTube Data API v3" → **Enable**.
3. **OAuth consent screen** (also called "Google Auth Platform"):
   - User type **External**; app name "Expanded View Uploader"; your email for support and developer contact.
   - Scopes: add `https://www.googleapis.com/auth/youtube.upload` and
     `https://www.googleapis.com/auth/youtube.force-ssl` (the second one lets it post the first comment).
   - Then set the publishing status to **In production** ("Publish app"). Important: in "Testing" mode
     Google's tokens expire after 7 days and uploads would stop.
     You don't need Google's verification; you'll just see an "unverified app" warning when you sign in, because it's your own app.
4. **Credentials → Create credentials → OAuth client ID** → type **Web application** → under
   "Authorized redirect URIs" add `https://developers.google.com/oauthplayground` → Create.
   Copy the **Client ID** and **Client secret**.
5. Get the refresh token:
   - Open developers.google.com/oauthplayground → gear icon (top right) → tick
     **Use your own OAuth credentials** → paste the Client ID and secret.
   - In "Step 1", type both scopes from step 3 (space-separated) into the box → **Authorize APIs**.
   - Sign in with the Google account that owns the Expanded View channel. If it asks which channel,
     pick **Expanded View**. On "Google hasn't verified this app" → Advanced → continue.
   - "Step 2" → **Exchange authorization code for tokens** → copy the **Refresh token**.
6. Add the environment variables `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
7. Add the allowed domains `oauth2.googleapis.com`, `www.googleapis.com`, `youtube.googleapis.com`.

A run checks it with `python tools/youtube_upload.py --check` (prints the channel name).
Scheduled direct uploads go up as **private** with a publish time. To cancel one, open it in YouTube Studio
and delete it, or leave it private, before that time.
To stop access completely: myaccount.google.com → Security → Third-party connections → remove the app.

## 3–4. Licensed photos and clips for the long-form videos, about 3 minutes

- Wikimedia Commons needs no account: just add `commons.wikimedia.org` and `upload.wikimedia.org`.
  Only freely licensed files are used (public domain, CC0, CC BY, CC BY-SA), and every one is credited in the
  description automatically.
- Pexels (free stock video): sign up at pexels.com → pexels.com/api → request an API key (free, instant).
  Add `PEXELS_API_KEY`, plus the domains `api.pexels.com`, `videos.pexels.com`, `images.pexels.com`.

## Things only you can do in the apps

- **Metricool plan:** the free plan allows 20 scheduled posts a month. At 2 Shorts a day it runs out about
  Nov 5–6. TikTok has to stay on Metricool (TikTok forces private posts from unapproved apps), so the Starter
  plan is needed to keep TikTok at 2 a day. Check the current price at metricool.com/pricing.
- **Reconnect TikTok in Metricool** (Connections → TikTok → reconnect): its TikTok stats stopped updating
  on Oct 29.
- **YouTube Studio:** open the manual-gearbox Short (`ypZtFjtbodg`). It got 55 views while every other Short
  got 1,300+. Check for a restriction, copyright claim or "processing" problem.
