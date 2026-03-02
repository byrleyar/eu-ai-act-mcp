import csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from audit_service import AuditService, AuditResult
from compliance_service import ProcessingContext

app = typer.Typer(help="EU AI Act Compliance Audit Processor")
console = Console()


def reverse_sanitize_model_id(dirname: str) -> str:
    """Reverse the sanitize_model_id transform: replace '__' with '/'."""
    return dirname.replace("__", "/")


def discover_model_dirs(batch_dir: Path) -> list[Path]:
    """Return subdirectories of batch_dir that contain a model_card.txt file."""
    model_dirs = []
    for child in sorted(batch_dir.iterdir()):
        if child.is_dir() and (child / "model_card.txt").exists():
            model_dirs.append(child)
    return model_dirs


@app.command()
def run(
    batch_dir: Path = typer.Argument(..., help="Path to batch directory to audit"),
    model_filter: Optional[str] = typer.Option(
        None, "--model", "-m", help="Audit single model only (directory name)"
    ),
) -> None:
    """Audit all models in a batch directory using AuditService."""
    # ---- Validate batch_dir ----
    if not batch_dir.exists():
        console.print(f"[red]Error: batch directory '{batch_dir}' does not exist.[/red]")
        raise typer.Exit(1)

    # ---- Discover model subdirectories ----
    model_dirs = discover_model_dirs(batch_dir)

    # ---- Apply model_filter if provided ----
    if model_filter is not None:
        model_dirs = [d for d in model_dirs if d.name == model_filter]

    if not model_dirs:
        console.print(
            f"[yellow]No model directories with model_card.txt found in '{batch_dir}'.[/yellow]"
        )
        raise typer.Exit()

    console.print(f"[bold green]Starting audit run for: {batch_dir}[/bold green]")
    console.print(f"Models to audit: {len(model_dirs)}\n")

    # ---- Initialize AuditService (reads ANTHROPIC_API_KEY from env) ----
    service = AuditService()

    results = []

    # ---- Audit loop with rich Progress bar ----
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        audit_task = progress.add_task("[cyan]Audit progress", total=len(model_dirs))

        for model_dir in model_dirs:
            model_id = reverse_sanitize_model_id(model_dir.name)
            progress.update(audit_task, description=f"Auditing [bold]{model_id}[/bold]")

            start_time = time.time()
            try:
                ctx = ProcessingContext(
                    model_id=model_id,
                    output_path=str(model_dir),
                    data_dir=str(model_dir),
                )

                result: AuditResult = service.audit_model(ctx)
                duration = time.time() - start_time

                s = result.summary
                progress.console.print(
                    f"[green]✓[/green] {model_id} — "
                    f"Scores: 1={s.score_1_count}, 1i={s.score_1i_count}, "
                    f"2={s.score_2_count}, 3={s.score_3_count}, 4={s.score_4_count}"
                )

                results.append(
                    {
                        "model_id": model_id,
                        "status": "SUCCESS",
                        "duration": f"{duration:.2f}s",
                        "total_fields": s.total_fields,
                        "score_1": s.score_1_count,
                        "score_1i": s.score_1i_count,
                        "score_2": s.score_2_count,
                        "score_3": s.score_3_count,
                        "score_4": s.score_4_count,
                        "error": "",
                    }
                )

            except Exception as e:
                duration = time.time() - start_time
                error_msg = str(e)
                progress.console.print(
                    f"[red]✗[/red] {model_id} failed: {error_msg}"
                )
                results.append(
                    {
                        "model_id": model_id,
                        "status": "FAIL",
                        "duration": f"{duration:.2f}s",
                        "total_fields": 0,
                        "score_1": 0,
                        "score_1i": 0,
                        "score_2": 0,
                        "score_3": 0,
                        "score_4": 0,
                        "error": error_msg,
                    }
                )

            progress.advance(audit_task)

    # ---- Generate audit_summary.csv ----
    summary_path = batch_dir / "audit_summary.csv"
    fieldnames = [
        "model_id",
        "status",
        "duration",
        "total_fields",
        "score_1",
        "score_1i",
        "score_2",
        "score_3",
        "score_4",
        "error",
    ]
    try:
        with open(summary_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        console.print(f"\n[bold green]Audit complete![/bold green]")
        console.print(f"Summary saved to: [cyan]{summary_path}[/cyan]")
    except Exception as e:
        console.print(f"[red]Error saving audit_summary.csv: {e}[/red]")

    # ---- Print summary table to console ----
    console.print("\n[bold]Audit Summary[/bold]")
    console.print(
        f"{'Model':<40} {'Status':<8} {'Fields':>6} {'1':>4} {'1i':>4} "
        f"{'2':>4} {'3':>4} {'4':>4}"
    )
    console.print("-" * 80)
    for r in results:
        console.print(
            f"{r['model_id']:<40} {r['status']:<8} {r['total_fields']:>6} "
            f"{r['score_1']:>4} {r['score_1i']:>4} {r['score_2']:>4} "
            f"{r['score_3']:>4} {r['score_4']:>4}"
        )


if __name__ == "__main__":
    app()
