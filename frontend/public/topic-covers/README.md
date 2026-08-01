# Topic cover pool

Illustrative covers used in the app and Telegram (not publisher photos).

## Layout

```
topic-covers/
  manifest.json
  politics/001.jpg …
  economy/001.jpg …
  life/001.jpg …

Also keep in sync:
  frontend/src/data/topicCoversManifest.json
  backend/app/data/topic_covers_manifest.json
```

## Adding images

1. Drop new files into the topic folder (`002.jpg`, `003.jpg`, …).
2. Append the filename to that topic’s array in **all three** manifests:
   - `frontend/public/topic-covers/manifest.json`
   - `frontend/src/data/topicCoversManifest.json`
   - `backend/app/data/topic_covers_manifest.json`
3. Prefer illustrative / abstract style; avoid logos, real people, party symbols.
4. Redeploy frontend (and backend if only the backend manifest changed).

Selection is stable per news id: `files[newsId % files.length]` (same on web and Telegram).
