# FastAPI app entrypoint — creates the app, registers routers and middleware.
# For now: also serves the static vanilla-JS frontend, so `uvicorn app.main:app`
# is the single command that runs the whole thing during this mockup stage.

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope

from app.logging_setup import setup_logging

setup_logging()

from app.api.routes import analyze, auth, documents, findings, organizations, review_comments  # noqa: E402

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

app = FastAPI(title="ISO Certification Platform API")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(analyze.router, prefix="/api")
app.include_router(organizations.router, prefix="/api/organizations", tags=["organizations"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(review_comments.router, prefix="/api", tags=["review_comments"])
app.include_router(findings.router, prefix="/api", tags=["findings"])

# app/api/routes/users.py deliberately has no router — see that file's
# comment for why there's no "list all users" endpoint.


class NoCacheStaticFiles(StaticFiles):
    """Plain StaticFiles lets browsers cache app.js/styles.css heuristically —
    editing a file on disk mid-session doesn't guarantee the browser re-fetches
    it, which looks exactly like a backend bug (stale UI hitting endpoints that
    no longer exist) until you realize it's just cache. Cache-Control: no-cache
    forces revalidation on every load — the browser still avoids re-downloading
    unchanged bytes (via the file's mtime/ETag), it just never trusts a cached
    copy blindly."""

    async def get_response(self, path: str, scope: Scope) -> Any:
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


# Mounted last and at "/" so it doesn't shadow any /api/* routes added above.
app.mount("/", NoCacheStaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

