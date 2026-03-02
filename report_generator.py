"""EU AI Act Compliance Report Generator.

Aggregates audit_results.json files produced by audit_processor.py into
batch summary reports: batch_report.csv (Plan 01) and batch_report.xlsx (Plan 02).
"""

import csv
import json
from pathlib import Path

import typer
from rich.console import Console

# ---------------------------------------------------------------------------
# Section map: 8 sections -> 80 question IDs
# Extracted from automated_testing/Hackathon Compliance Form Validation.xlsx
# ---------------------------------------------------------------------------

SECTION_MAP: dict[str, list[str]] = {
    "General Information": [
        "date_last_updated", "doc_version_number", "legal_name", "model_name",
        "model_authenticity", "release_date", "union_release_date", "model_dependencies",
    ],  # 8 questions
    "Model Properties": [
        "model_architecture", "design_specs",
        "input_modalities_text_check", "input_modalities_text_max",
        "input_modalities_images_check", "input_modalities_images_max",
        "input_modalities_audio_check", "input_modalities_audio_max",
        "input_modalities_video_check", "input_modalities_video_max",
        "input_modalities_other_check", "input_modalities_other_max",
        "output_modalities_text_check", "output_modalities_text_max",
        "output_modalities_images_check", "output_modalities_images_max",
        "output_modalities_audio_check", "output_modalities_audio_max",
        "output_modalities_video_check", "output_modalities_video_max",
        "output_modalities_other_check", "output_modalities_other_max",
        "total_model_size", "total_model_size_500m", "total_model_size_5b",
        "total_model_size_15b", "total_model_size_50b", "total_model_size_100b",
        "total_model_size_500b", "total_model_size_1t", "total_model_size_max",
    ],  # 31 questions
    "Methods of Distribution": [
        "distribution_channels_aio_nca", "distribution_channels_dps",
        "license_link", "license_category", "license_assets",
    ],  # 5 questions
    "Use": [
        "acceptable_use_policy", "intended_uses", "type_and_nature",
        "technical_means", "required_hardware", "required_software",
    ],  # 6 questions
    "Training Process": [
        "design_specifications", "decision_rationale",
    ],  # 2 questions
    "Information on Data": [
        "data_training_type_text", "data_training_type_images",
        "data_training_type_audio", "data_training_type_video",
        "data_training_type_other",
        "data_provenance_web", "data_provenance_private",
        "data_provenance_user", "data_provenance_public",
        "data_provenance_synthetic", "data_provenance_other_check",
        "data_provenance_other", "how_data_obtained",
        "data_points_ncas", "data_points_aio",
        "scope", "data_curation", "detect_unsuitability", "detect_biases",
    ],  # 19 questions
    "Computational Resources": [
        "training_time_ncas", "training_time_aio",
        "computation_used_ncas", "computation_used_aio",
        "computation_methodology",
    ],  # 5 questions
    "Energy Consumption": [
        "energy_used", "energy_methodology",
        "benchmark_computation", "computation_measurement_methodology",
    ],  # 4 questions
}
# Total: 80 questions -- matches questions.json exactly (verified)

# ---------------------------------------------------------------------------
# Startup assertion: SECTION_MAP must cover all IDs in questions.json exactly
# ---------------------------------------------------------------------------

_mapped_ids = {qid for qids in SECTION_MAP.values() for qid in qids}
_expected_ids = {
    q["id"]
    for q in json.load(open(Path(__file__).parent / "questions.json"))
}
assert _mapped_ids == _expected_ids, (
    f"SECTION_MAP drift: missing={_expected_ids - _mapped_ids}, "
    f"extra={_mapped_ids - _expected_ids}"
)

# ---------------------------------------------------------------------------
# CSV field names
# ---------------------------------------------------------------------------

CSV_FIELDNAMES = [
    "model_id",
    "status",
    "total_fields",
    "score_1",
    "score_1i",
    "score_2",
    "score_3",
    "score_4",
    "accuracy_pct",
    "hallucination_pct",
    "pass_pct",
    "fail_pct",
]

# ---------------------------------------------------------------------------
# Module-level console
# ---------------------------------------------------------------------------

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_audit_results(model_dir: Path) -> dict | None:
    """Load audit_results.json from model_dir.

    Returns a dict with keys:
      - scores_by_qid: {question_id: score}
      - summary: raw summary dict from audit_results.json
      - model_id: str
      - audit_timestamp: str

    Returns None if audit_results.json is missing.
    """
    audit_path = model_dir / "audit_results.json"
    if not audit_path.exists():
        return None
    with open(audit_path, encoding="utf-8") as f:
        data = json.load(f)
    scores_by_qid = {fa["question_id"]: fa["score"] for fa in data["field_audits"]}
    return {
        "scores_by_qid": scores_by_qid,
        "summary": data.get("summary", {}),
        "model_id": data.get("model_id", model_dir.name),
        "audit_timestamp": data.get("audit_timestamp", ""),
    }


def compute_metrics(score_counts: dict) -> dict:
    """Compute compliance audit metrics from score counts.

    Args:
        score_counts: dict with keys score_1, score_1i, score_2, score_3,
                      score_4, total_fields.

    Returns:
        dict with keys: accuracy_rate, hallucination_rate, gap_rate, na_rate,
        pass_rate, fail_rate. All values are floats in [0.0, 1.0].
    """
    total = score_counts.get("total_fields", 0)
    if total == 0:
        return {
            "accuracy_rate": 0.0,
            "hallucination_rate": 0.0,
            "gap_rate": 0.0,
            "na_rate": 0.0,
            "pass_rate": 0.0,
            "fail_rate": 0.0,
        }

    s1 = score_counts.get("score_1", 0)
    s1i = score_counts.get("score_1i", 0)
    s2 = score_counts.get("score_2", 0)
    s3 = score_counts.get("score_3", 0)
    s4 = score_counts.get("score_4", 0)

    return {
        "accuracy_rate": (s1 + s1i) / total,
        "hallucination_rate": s2 / total,
        "gap_rate": s3 / total,
        "na_rate": s4 / total,
        "pass_rate": (s1 + s1i + s4) / total,
        "fail_rate": (s2 + s3) / total,
    }


# ---------------------------------------------------------------------------
# ReportGenerator class
# ---------------------------------------------------------------------------


class ReportGenerator:
    """Aggregates audit_results.json files into batch summary reports."""

    def discover_audited_models(self, batch_dir: Path) -> list[dict]:
        """Iterate sorted subdirectories of batch_dir and collect audit data.

        For each subdirectory that contains audit_results.json, load the
        results and compute metrics. Summary keys (score_1_count, etc.) are
        remapped to compute_metrics keys (score_1, etc.) before calling
        compute_metrics.

        Returns:
            List of dicts with keys:
              model_id, model_dir, scores_by_qid, summary, metrics
        """
        models = []
        for child in sorted(batch_dir.iterdir()):
            if not child.is_dir():
                continue
            result = load_audit_results(child)
            if result is None:
                continue

            summary = result["summary"]
            # Remap _count suffixed keys to plain keys expected by compute_metrics
            score_counts = {
                "score_1": summary.get("score_1_count", 0),
                "score_1i": summary.get("score_1i_count", 0),
                "score_2": summary.get("score_2_count", 0),
                "score_3": summary.get("score_3_count", 0),
                "score_4": summary.get("score_4_count", 0),
                "total_fields": summary.get("total_fields", 0),
            }
            metrics = compute_metrics(score_counts)

            models.append({
                "model_id": result["model_id"],
                "model_dir": child,
                "scores_by_qid": result["scores_by_qid"],
                "summary": summary,
                "metrics": metrics,
                "score_counts": score_counts,
            })

        return models

    def write_csv(self, batch_dir: Path, models: list[dict]) -> Path:
        """Write batch_report.csv to batch_dir.

        Each row contains per-model score counts and percentage metrics.
        Percentages are 0-100 floats (rate * 100, rounded to 2 decimals).

        Returns:
            Path to the written CSV file.
        """
        csv_path = batch_dir / "batch_report.csv"
        with open(csv_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            for model in models:
                sc = model["score_counts"]
                m = model["metrics"]
                writer.writerow({
                    "model_id": model["model_id"],
                    "status": "audited",
                    "total_fields": sc["total_fields"],
                    "score_1": sc["score_1"],
                    "score_1i": sc["score_1i"],
                    "score_2": sc["score_2"],
                    "score_3": sc["score_3"],
                    "score_4": sc["score_4"],
                    "accuracy_pct": round(m["accuracy_rate"] * 100, 2),
                    "hallucination_pct": round(m["hallucination_rate"] * 100, 2),
                    "pass_pct": round(m["pass_rate"] * 100, 2),
                    "fail_pct": round(m["fail_rate"] * 100, 2),
                })
        return csv_path

    def generate(self, batch_dir: Path) -> None:
        """Orchestrate report generation for a batch directory.

        1. Discover all model subdirectories with audit_results.json
        2. Validate at least one model was audited
        3. Write batch_report.csv
        4. Write batch_report.xlsx (placeholder -- Plan 02)
        5. Write executive_summary.txt (placeholder -- Plan 02)
        6. Print summary to console
        """
        if not batch_dir.exists():
            console.print(
                f"[red]Error: batch directory '{batch_dir}' does not exist.[/red]"
            )
            raise typer.Exit(1)

        console.print(f"[bold green]Generating report for: {batch_dir}[/bold green]")

        models = self.discover_audited_models(batch_dir)

        if not models:
            console.print(
                "[red]No audit_results.json found. Run audit_processor.py first.[/red]"
            )
            raise typer.Exit(1)

        console.print(f"Models with audit data: {len(models)}")

        # Write CSV
        csv_path = self.write_csv(batch_dir, models)
        console.print(f"CSV report: [cyan]{csv_path}[/cyan]")

        # Placeholder: Plan 02 will add xlsx and executive_summary.txt
        # write_xlsx(batch_dir, models)
        # write_executive_summary(batch_dir, models)

        # Print console summary table
        console.print("\n[bold]Audit Report Summary[/bold]")
        console.print(
            f"{'Model':<45} {'Fields':>6} {'1':>4} {'1i':>4} "
            f"{'2':>4} {'3':>4} {'4':>4} {'Acc%':>6} {'Pass%':>6}"
        )
        console.print("-" * 90)
        for model in models:
            sc = model["score_counts"]
            m = model["metrics"]
            console.print(
                f"{model['model_id']:<45} {sc['total_fields']:>6} "
                f"{sc['score_1']:>4} {sc['score_1i']:>4} {sc['score_2']:>4} "
                f"{sc['score_3']:>4} {sc['score_4']:>4} "
                f"{m['accuracy_rate']*100:>6.1f} {m['pass_rate']*100:>6.1f}"
            )

        console.print(f"\n[bold green]Report complete![/bold green]")
        console.print(f"Models processed: {len(models)}")


# ---------------------------------------------------------------------------
# Typer CLI
# ---------------------------------------------------------------------------

app = typer.Typer(help="EU AI Act Compliance Report Generator")


@app.command()
def run(
    batch_dir: Path = typer.Argument(..., help="Path to batch directory"),
) -> None:
    """Generate aggregate compliance audit report for a batch directory."""
    generator = ReportGenerator()
    generator.generate(batch_dir)


if __name__ == "__main__":
    app()
