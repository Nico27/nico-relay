"""FastAPI application: two read endpoints and the static dashboard."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException, Query, Request, Response

from . import models
from .config import Settings
from .db import create_pool
from .repository import PostgresRepository
from .service import AccountNotFound, DashboardService, DataUnavailable, Repository


def create_app(
    settings: Settings | None = None,
    *,
    service: DashboardService | None = None,
    repository: Repository | None = None,
) -> FastAPI:
    """Build the app.

    Passing `service` (or `repository`) skips the database entirely, which is how
    the API tests run without Postgres.
    """
    settings = settings or Settings.from_env()

    lifespan: Callable[[FastAPI], AsyncIterator[None]] | None = None
    if service is None and repository is None:

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncIterator[None]:
            pool = create_pool(settings.database_url)
            app.state.pool = pool
            repo = PostgresRepository(pool)
            app.state.service = DashboardService(
                repo, baseline_weeks=settings.baseline_weeks
            )
            app.state.ready = repo.ping
            try:
                yield
            finally:
                pool.close()

    app = FastAPI(
        title="Relay — is this normal for us?",
        version="1.0.0",
        summary="DASH-247 activity baseline dashboard",
        lifespan=lifespan,
    )
    if service is not None:
        app.state.service = service
    elif repository is not None:
        app.state.service = DashboardService(
            repository, baseline_weeks=settings.baseline_weeks
        )

    def get_service(request: Request) -> DashboardService:
        return request.app.state.service

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz(request: Request, response: Response) -> dict[str, str]:
        probe = getattr(request.app.state, "ready", None)
        if probe is None:
            return {"status": "ok", "database": "not checked"}
        try:
            probe()
        except Exception as error:  # noqa: BLE001 - report the class, not the secret
            response.status_code = 503
            return {"status": "degraded", "database": type(error).__name__}
        return {"status": "ok", "database": "ok"}

    @app.get("/api/v1/accounts", response_model=models.AccountsResponse)
    def list_accounts(request: Request) -> models.AccountsResponse:
        return get_service(request).list_accounts()

    @app.get(
        "/api/v1/accounts/{account_id}/dashboard",
        response_model=models.DashboardResponse,
    )
    def account_dashboard(
        request: Request,
        account_id: int,
        as_of: date | None = Query(None, description="clamp the analysis horizon"),
        baseline_weeks: int | None = Query(None, ge=1, le=26),
    ) -> models.DashboardResponse:
        try:
            return get_service(request).dashboard(
                account_id, as_of=as_of, baseline_weeks=baseline_weeks
            )
        except AccountNotFound as error:
            raise HTTPException(status_code=404, detail="Account not found") from error
        except DataUnavailable as error:
            raise HTTPException(
                status_code=503, detail="No activity data available yet"
            ) from error

    return app


app = create_app()
