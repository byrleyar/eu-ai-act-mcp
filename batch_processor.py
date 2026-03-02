import os
import csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from pathvalidate import sanitize_filename

from compliance_service import ComplianceService, ProcessingContext

app = typer.Typer(help="EU AI Act Compliance Batch Processor")
console = Console()
service = ComplianceService()

def get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M")

def sanitize_model_id(model_id: str) -> str:
    """Sanitize HF model ID for filesystem use."""
    safe_name = model_id.replace("/", "__")
    return sanitize_filename(safe_name, replacement_text="_")

@app.command()
def run(
    models: Optional[List[str]] = typer.Option(None, "--models", "-m", help="List of Hugging Face model IDs"),
    input_csv: Optional[Path] = typer.Option(None, "--input-csv", "-i", help="Path to CSV file containing model IDs"),
    output_dir: Path = typer.Option(Path("batches"), "--output-dir", "-o", help="Root directory for batch outputs")
):
    """Run compliance checks for a batch of models."""
    model_list = []
    
    # 1. Gather model IDs
    if models:
        model_list.extend(models)
    
    if input_csv:
        if not input_csv.exists():
            console.print(f"[red]Error: CSV file {input_csv} not found.[/red]")
            raise typer.Exit(1)
        
        try:
            with open(input_csv, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if 'model_id' not in reader.fieldnames:
                    f.seek(0)
                    reader = csv.reader(f)
                    for row in reader:
                        if row: model_list.append(row[0])
                else:
                    for row in reader:
                        model_list.append(row['model_id'])
        except Exception as e:
            console.print(f"[red]Error reading CSV: {e}[/red]")
            raise typer.Exit(1)

    if not model_list:
        console.print("[yellow]No models provided. Use --models or --input-csv.[/yellow]")
        raise typer.Exit()

    # 2. Setup batch directory
    batch_id = get_timestamp()
    batch_root = output_dir / f"batch_{batch_id}"
    batch_root.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[bold green]Starting batch run: {batch_id}[/bold green]")
    console.print(f"Output directory: {batch_root}")
    console.print(f"Processing {len(model_list)} models sequentially.\n")

    results = []

    # 3. Process loop with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        batch_task = progress.add_task("[cyan]Batch progress", total=len(model_list))
        
        for model_id in model_list:
            safe_name = sanitize_model_id(model_id)
            model_dir = batch_root / safe_name
            model_dir.mkdir(parents=True, exist_ok=True)
            
            progress.update(batch_task, description=f"Processing [bold]{model_id}[/bold]")
            
            start_time = time.time()
            try:
                # State Isolation: Fresh context for each model
                ctx = ProcessingContext(
                    model_id=model_id,
                    output_path=str(model_dir),
                    data_dir=str(model_dir),
                    base_url=None # No public URL needed for batch JSONs
                )
                
                # Step 1: Fetch and discover (BAT-01, BAT-02)
                card_text = service.fetch_hf_model_card(model_id)
                
                # Save raw card text
                with open(model_dir / "model_card.txt", "w", encoding="utf-8") as f:
                    f.write(card_text)
                
                # Step 2: Extract links (to satisfy discovery requirement)
                links = service.discover_relevant_links(card_text, model_id)
                with open(model_dir / "discovered_links.json", "w", encoding="utf-8") as f:
                    json.dump(links, f, indent=2)

                # Placeholder for BAT-05: Since Automated Analysis is Phase 12,
                # we save an empty compliance template to show artifact persistence.
                with open("questions.json", "r") as f:
                    questions = json.load(f)
                
                # Create empty template
                template_data = {q['id']: "" for q in questions}
                template_data["model_name"] = model_id
                
                with open(model_dir / "compliance_data_template.json", "w", encoding="utf-8") as f:
                    json.dump(template_data, f, indent=2)

                duration = time.time() - start_time
                results.append({
                    "model_id": model_id,
                    "status": "SUCCESS",
                    "duration": f"{duration:.2f}s",
                    "error": "",
                    "output_path": str(model_dir)
                })
                progress.console.print(f"[green]✓[/green] Successfully processed {model_id}")
                
            except Exception as e:
                duration = time.time() - start_time
                error_msg = str(e)
                results.append({
                    "model_id": model_id,
                    "status": "FAIL",
                    "duration": f"{duration:.2f}s",
                    "error": error_msg,
                    "output_path": ""
                })
                progress.console.print(f"[red]✗[/red] Failed to process {model_id}: {error_msg}")
            
            progress.advance(batch_task)

    # 4. Generate Summary Report (Task 4)
    summary_path = batch_root / "batch_summary.csv"
    try:
        with open(summary_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["model_id", "status", "duration", "error", "output_path"])
            writer.writeheader()
            writer.writerows(results)
        
        console.print(f"\n[bold green]Batch completed![/bold green]")
        console.print(f"Summary report saved to: [cyan]{summary_path}[/cyan]")
    except Exception as e:
        console.print(f"[red]Error saving summary report: {e}[/red]")

if __name__ == "__main__":
    app()
