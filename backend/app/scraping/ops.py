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

            profile = await db.scalar(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            watchlist = (
                profile.watchlist_companies
                if profile and profile.watchlist_companies
                else []
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


if __name__ == "__main__":
    app()
