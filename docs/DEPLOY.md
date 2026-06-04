# Deploying the showcase (`web/`)

`web/` is **static, no-build, CDN-pinned three.js** — it serves as-is from any static host.
All asset paths are relative; three.js loads from jsdelivr. Nothing to compile.

> These are prepared steps. Pick one; run it yourself when ready.

## Option A — Netlify Drop (simplest, no git, ~30 s)
1. Go to **https://app.netlify.com/drop**
2. Drag the **`web/`** folder onto the page.
3. You get an instant public URL (e.g. `https://vara-xxxx.netlify.app`). Done.
   - To get a custom subdomain or redeploys, claim the site (free account) and re-drag to update.

## Option B — GitHub Pages (versioned, from this repo)
First publish the repo (no remote yet):
```bash
# create the GitHub repo (needs `gh auth login` once)
gh repo create vara --public --source=. --remote=origin --push
```
Then serve only `web/` via a `gh-pages` branch:
```bash
git subtree push --prefix web origin gh-pages
```
Enable Pages: **repo → Settings → Pages → Source: Deploy from a branch → `gh-pages` / `/ (root)`**.
Live at `https://<your-user>.github.io/vara/` within a minute.

To update after edits to `web/`: re-run the `git subtree push` line.

*(Alternative for Pages without a second branch: a GitHub Action that uploads `web/` as the
Pages artifact — heavier setup; the subtree push is simpler for a no-build site.)*

## Option C — Cloudflare Pages / Vercel
Connect the repo, set **build command: none**, **output directory: `web`**. Deploys on push.

## Sanity check before sharing the link
- Open the URL, confirm all three scenes load (the GLBs are ~1.3 MB total) and there are no
  console errors.
- The honesty footer must be present: *"…validated-by-design, not hardware-tested…"*.
