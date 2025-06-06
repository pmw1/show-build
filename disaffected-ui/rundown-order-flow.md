
- The request payload is a JSON array of segment objects, typically including:
- `filename` (e.g. `1A.md`)
- optionally other metadata (e.g. `title`, `slug`, `asset_id`)

---

## 🧠 What Happens in the Backend

1. The backend receives the new list.
2. It loops through the list and assigns new `order:` values:
 - `10`, `20`, `30`, etc.
3. For each segment:
 - The backend opens the corresponding `.md` file from:
   ```
   /home/episodes/{episode}/rundown/{filename}
   ```
 - It updates the YAML frontmatter to set the new `order:` value.
 - It preserves all other metadata (like `title`, `slug`, `asset_id`).
 - It writes the file back to disk.

---

## ✅ Result

- Files stay the same (no renaming).
- Asset IDs remain untouched.
- YAML `order:` values reflect the new UI sequence.
- Obsidian or any plugin that reads frontmatter can now sort segments properly.

---

This process maintains a stable structure, avoids filename churn, and allows consistent ordering across UI, backend, and local markdown tools.

