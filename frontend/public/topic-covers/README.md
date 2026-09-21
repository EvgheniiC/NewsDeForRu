# Topic cover pool

Illustrative covers used in the app and Telegram (not publisher photos).

## Layout

```
topic-covers/
  manifest.json
  politics/   economy/   life/          ← fallback pools (feed filters)
  government/ elections/ eu/ security/
  money/ jobs/ energy/ construction/ transport/
  health/ education/ sport/ family/ weather/ culture/
```

Also keep in sync:

- `frontend/src/data/topicCoversManifest.json`
- `backend/app/data/topic_covers_manifest.json`

LLM and moderators set `cover_tag` (illustration). Public filters stay `politics | economy | life`.
If `cover_tag` is missing or its folder is empty, the app uses the feed-topic folder.

## Adding images

1. Drop files into the illustration folder (`001.jpg`, `002.jpg`, …).
2. Append the filename to that key’s array in **all three** manifests.
3. Prefer illustrative / abstract style; avoid logos, real people, party symbols.
4. Keep one motif per folder (sport is sport, not fruit).
5. Redeploy frontend (and backend if only the backend manifest changed).

Selection is stable per news id: `files[newsId % files.length]` (same on web and Telegram).
