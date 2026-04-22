from typing import Dict

from fastapi import FastAPI

app: FastAPI = FastAPI(title="newsForGermanyRU Backend", version="0.1.0")


@app.get("/health")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}
