# app/scraping/ops.py
"""CLI operations tool for scraper platform management."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Scraper platform operations")
targets_app = typer.Typer(help="Target management")
quarantine_app = typer.Typer(help="Quarantine management")
app.add_typer(targets_app, name="targets")
app.add_typer(quarantine_app, name="quarantine")

console = Console()


@targets_app.command("import")
def import_targets(
    file: Path = typer.Argument(..., help="Path to Excel/CSV file"),
    classify: bool = typer.Option(True, help="Run URL classification"),
    dry_run: bool = typer.Option(False, help="Preview without importing"),
) -> None:
    """Bulk import career page URLs from Excel/CSV."""
    from app.database import async_session_factory
    from app.scraping.control.target_registry import import_from_excel

    async def _run() -> None:
        async with async_session_factory() as db:
            from sqlalchemy import select, text

            row = await db.execute(text("SELECT id FROM users LIMIT 1"))
            user_id = row.scalar_one()

            from app.profile.models import UserProfile

            profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
            watchlist = (
                profile.watchlist_companies if profile and profile.watchlist_companies else []
            )

            stats = await import_from_excel(
                db,
                file,
                user_id,
                watchlist,
                dry_run=dry_run,
            )

        table = Table(title="Import Results" + (" (DRY RUN)" if dry_run else ""))
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        table.add_row("Total rows", str(stats["total"]))
        table.add_row("Imported", str(stats["imported"]))
        table.add_row("Skipped (duplicate)", str(stats["skipped_duplicate"]))
        table.add_row("Skipped (no URL)", str(stats["skipped_no_url"]))
        console.print(table)

    asyncio.run(_run())


@targets_app.command("list")
def list_targets_cmd(
    priority: str = typer.Option(None, help="Filter by priority class"),
    ats: str = typer.Option(None, help="Filter by ATS vendor"),
    quarantined: bool = typer.Option(False, help="Show quarantined only"),
    failing: bool = typer.Option(False, help="Show failing only"),
    limit: int = typer.Option(50, help="Max results"),
) -> None:
    """List scrape targets."""
    from app.database import async_session_factory
    from app.scraping.control.target_registry import list_targets

    async def _run() -> None:
        async with async_session_factory() as db:
            from sqlalchemy import text

            row = await db.execute(text("SELECT id FROM users LIMIT 1"))
            user_id = row.scalar_one()

            targets = await list_targets(
                db,
                user_id,
                priority=priority,
                ats=ats,
                quarantined=quarantined if quarantined else None,
                failing=failing,
                limit=limit,
            )

        table = Table(title=f"Scrape Targets ({len(targets)} results)")
        table.add_column("Company", style="cyan", max_width=25)
        table.add_column("ATS", style="yellow")
        table.add_column("Tier", style="green")
        table.add_column("Priority", style="magenta")
        table.add_column("Failures", style="red")
        table.add_column("Last Success")
        for t in targets:
            table.add_row(
                t.company_name or "—",
                t.ats_vendor or "unknown",
                str(t.start_tier),
                t.priority_class,
                str(t.consecutive_failures),
                str(t.last_success_at.date()) if t.last_success_at else "never",
            )
        console.print(table)

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Quarantine commands
# ---------------------------------------------------------------------------


@quarantine_app.command("list")
def quarantine_list() -> None:
    """Show all quarantined targets with failure reasons."""
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.scraping.models import ScrapeTarget

    async def _run() -> None:
        async with async_session_factory() as db:
            result = await db.scalars(
                select(ScrapeTarget)
                .where(ScrapeTarget.quarantined == True)  # noqa: E712
                .order_by(ScrapeTarget.last_failure_at.desc())
            )
            targets = list(result.all())

        table = Table(title=f"Quarantined Targets ({len(targets)})")
        table.add_column("Company", style="cyan", max_width=25)
        table.add_column("URL", style="blue", max_width=40)
        table.add_column("Failures", style="red")
        table.add_column("Reason", style="yellow", max_width=30)
        table.add_column("Last Failure")
        for t in targets:
            table.add_row(
                t.company_name or "—",
                t.url[:40],
                str(t.consecutive_failures),
                t.quarantine_reason or "—",
                str(t.last_failure_at.date()) if t.last_failure_at else "—",
            )
        console.print(table)

    asyncio.run(_run())


@quarantine_app.command("review")
def quarantine_review(
    target_id: str = typer.Argument(..., help="Target UUID"),
) -> None:
    """Show last 5 attempts and failure traces for a target."""
    import uuid as uuid_mod

    from sqlalchemy import select

    from app.database import async_session_factory
    from app.scraping.models import ScrapeAttempt, ScrapeTarget

    async def _run() -> None:
        async with async_session_factory() as db:
            target = await db.get(ScrapeTarget, uuid_mod.UUID(target_id))
            if not target:
                console.print(f"[red]Target {target_id} not found[/red]")
                return

            attempts = await db.scalars(
                select(ScrapeAttempt)
                .where(ScrapeAttempt.target_id == target.id)
                .order_by(ScrapeAttempt.created_at.desc())
                .limit(5)
            )

        console.print(f"\n[bold]{target.company_name or target.url}[/bold]")
        console.print(f"Quarantined: {target.quarantined}")
        console.print(f"Failures: {target.consecutive_failures}")
        console.print(f"Reason: {target.quarantine_reason or '—'}\n")

        table = Table(title="Last 5 Attempts")
        table.add_column("Date")
        table.add_column("Tier", style="green")
        table.add_column("Scraper")
        table.add_column("Status", style="yellow")
        table.add_column("Error", style="red", max_width=40)
        for a in attempts.all():
            table.add_row(
                str(a.created_at.strftime("%Y-%m-%d %H:%M")) if a.created_at else "—",
                str(a.actual_tier_used),
                a.scraper_name,
                a.status,
                a.error_message[:40] if a.error_message else "—",
            )
        console.print(table)

    asyncio.run(_run())


@quarantine_app.command("release")
def quarantine_release(
    target_id: str = typer.Argument(..., help="Target UUID"),
    force_tier: int = typer.Option(None, help="Force starting tier after release"),
) -> None:
    """Un-quarantine and reset failure count."""
    import uuid as uuid_mod
    from datetime import UTC, datetime

    from app.database import async_session_factory
    from app.scraping.models import ScrapeTarget

    async def _run() -> None:
        async with async_session_factory() as db:
            target = await db.get(ScrapeTarget, uuid_mod.UUID(target_id))
            if not target:
                console.print(f"[red]Target {target_id} not found[/red]")
                return

            target.quarantined = False
            target.quarantine_reason = None
            target.consecutive_failures = 0
            target.next_scheduled_at = datetime.now(UTC)
            if force_tier is not None:
                target.start_tier = force_tier
            await db.commit()
            console.print(
                f"[green]Released {target.company_name or target_id} from quarantine[/green]"
            )

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Health command
# ---------------------------------------------------------------------------


@app.command("health")
def health_cmd() -> None:
    """Show per-source success rates and circuit breaker states."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import func, select

    from app.database import async_session_factory
    from app.scraping.models import ScrapeAttempt

    async def _run() -> None:
        async with async_session_factory() as db:
            cutoff = datetime.now(UTC) - timedelta(hours=24)

            result = await db.execute(
                select(
                    ScrapeAttempt.scraper_name,
                    func.count().label("total"),
                    func.count().filter(ScrapeAttempt.status == "success").label("success"),
                    func.count().filter(ScrapeAttempt.status == "failed").label("failed"),
                    func.avg(ScrapeAttempt.duration_ms).label("avg_ms"),
                )
                .where(ScrapeAttempt.created_at >= cutoff)
                .group_by(ScrapeAttempt.scraper_name)
            )

        table = Table(title="Scraper Health (Last 24h)")
        table.add_column("Scraper", style="cyan")
        table.add_column("Total")
        table.add_column("Success", style="green")
        table.add_column("Failed", style="red")
        table.add_column("Rate", style="yellow")
        table.add_column("Avg ms")
        for row in result.all():
            rate = f"{(row.success / row.total * 100):.0f}%" if row.total else "—"
            table.add_row(
                row.scraper_name,
                str(row.total),
                str(row.success),
                str(row.failed),
                rate,
                f"{row.avg_ms:.0f}" if row.avg_ms else "—",
            )
        console.print(table)

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Test-fetch command
# ---------------------------------------------------------------------------


@app.command("test-fetch")
def test_fetch(
    url: str = typer.Argument(..., help="URL to test-scrape"),
    tier: int = typer.Option(None, help="Force specific tier (0-3)"),
    dry_run: bool = typer.Option(False, help="Show execution plan without fetching"),
) -> None:
    """Test-scrape a single URL through the full pipeline."""
    from types import SimpleNamespace

    from app.scraping.control.classifier import classify_target
    from app.scraping.control.tier_router import TierRouter

    classification = classify_target(url)
    target = SimpleNamespace(
        ats_vendor=classification["ats_vendor"],
        start_tier=tier if tier is not None else classification["start_tier"],
        max_tier=3,
        last_success_tier=None,
        consecutive_failures=0,
    )
    plan = TierRouter.route(target)

    console.print(f"\n[bold]Test Fetch: {url}[/bold]")
    console.print(f"ATS: {classification['ats_vendor'] or 'unknown'}")
    console.print(f"Source kind: {classification['source_kind']}")
    console.print(f"Primary tier: {plan.primary_tier}")
    console.print(f"Primary scraper: {plan.primary_step.scraper_name}")

    if plan.fallback_chain:
        console.print(
            f"Fallback chain: {' -> '.join(s.scraper_name for s in plan.fallback_chain)}"
        )

    if dry_run:
        console.print("\n[yellow]Dry run — no actual fetch performed[/yellow]")
        return

    console.print(
        "\n[yellow]Live fetch not implemented yet — use --dry-run to see execution plan[/yellow]"
    )


if __name__ == "__main__":
    app()
