"""Batch Analytical Report Generator for EU AI Act Compliance Audits.

Aggregates audit_results.json files produced by audit_processor.py into
publication-ready analytical tables and a Markdown report.

Usage:
    python generate_report.py <audit_dir> --models-csv test_models.csv --output-dir <out>

Pipeline stages:
    1. Load  — walk audit_dir, read each audit_results.json
    2. Join  — load models-csv manifest, enrich audits with org_type / domain
    3. Agg   — build combined_field_audits.csv + df_models for Tables 1-4
    4. Render — write CSVs (Tables 1-4), stub for Plan 02 Markdown assembly
"""

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import typer
from rich.console import Console

from report_generator import SECTION_MAP

# ---------------------------------------------------------------------------
# Module-level derived mapping
# ---------------------------------------------------------------------------

SECTION_MAP_INVERTED: dict[str, str] = {
    qid: section
    for section, qids in SECTION_MAP.items()
    for qid in qids
}

app = typer.Typer(help="Generate analytical Markdown report from batch audit results.")
console = Console()


# ---------------------------------------------------------------------------
# Stage 1 — Load
# ---------------------------------------------------------------------------


def load_batch_audits(audit_dir: Path) -> tuple[list[dict], list[str]]:
    """Walk audit_dir and load each audit_results.json.

    Args:
        audit_dir: Root directory whose immediate subdirectories each contain
                   one audited model's artifacts.

    Returns:
        (audits_list, skipped_dirs) where:
          - audits_list: list of raw audit dicts (with "field_audits" key)
          - skipped_dirs: directory names that had no audit_results.json
    """
    audits: list[dict] = []
    skipped: list[str] = []

    for child in sorted(audit_dir.iterdir()):
        if not child.is_dir():
            continue

        audit_path = child / "audit_results.json"
        if not audit_path.exists():
            skipped.append(child.name)
            continue

        try:
            data = json.loads(audit_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            console.print(
                f"[yellow]Warning: could not load {audit_path}: {exc}[/yellow]"
            )
            skipped.append(child.name)
            continue

        field_audits = data.get("field_audits")
        if not field_audits:
            console.print(
                f"[yellow]Warning: {child.name} has no field_audits — skipping.[/yellow]"
            )
            skipped.append(child.name)
            continue

        audits.append(data)

    return audits, skipped


# ---------------------------------------------------------------------------
# Stage 2 — Manifest
# ---------------------------------------------------------------------------


def load_manifest(models_csv: Path) -> pd.DataFrame:
    """Load and normalise the models CSV manifest.

    Expected columns: model_id, org_type, domain
    All string columns are stripped of surrounding whitespace.

    Returns:
        DataFrame with at least columns: model_id, org_type, domain
    """
    df = pd.read_csv(models_csv)
    # Strip column names
    df.columns = df.columns.str.strip()
    # Strip all string column values
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
    return df


# ---------------------------------------------------------------------------
# Stage 3 — Build combined DataFrame
# ---------------------------------------------------------------------------


def build_combined_df(
    audits: list[dict],
    manifest: pd.DataFrame,
) -> pd.DataFrame:
    """Build the combined field-level DataFrame from all audits.

    Each row represents one question's audit result for one model.

    Args:
        audits: list of raw audit dicts (from load_batch_audits)
        manifest: DataFrame with model_id, org_type, domain columns

    Returns:
        DataFrame with columns:
            model_id, org_type, domain, question_id, section,
            score, score_label, confidence, reasoning
    """
    # Build manifest lookup for fast access
    manifest_index = manifest.set_index("model_id")

    rows: list[dict] = []

    for audit in audits:
        model_id = audit.get("model_id", "unknown")

        # Look up org_type / domain from manifest
        if model_id in manifest_index.index:
            org_type = manifest_index.at[model_id, "org_type"]
            domain = manifest_index.at[model_id, "domain"]
        else:
            console.print(
                f"[yellow]Warning: model '{model_id}' not in manifest — "
                f"using 'unknown' for org_type and domain.[/yellow]"
            )
            org_type = "unknown"
            domain = "unknown"

        for fa in audit["field_audits"]:
            question_id = fa.get("question_id", "")
            section = SECTION_MAP_INVERTED.get(question_id, "Unknown")
            reasoning_raw = fa.get("reasoning", "")
            rows.append(
                {
                    "model_id": model_id,
                    "org_type": org_type,
                    "domain": domain,
                    "question_id": question_id,
                    "section": section,
                    "score": fa.get("score", ""),
                    "score_label": fa.get("score_label", ""),
                    "confidence": fa.get("confidence", ""),
                    "reasoning": (reasoning_raw[:200] if reasoning_raw else ""),
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "model_id", "org_type", "domain", "question_id",
                "section", "score", "score_label", "confidence", "reasoning",
            ]
        )

    df = pd.DataFrame(rows)

    # Warn about unmapped question_ids
    unknown_mask = df["section"] == "Unknown"
    if unknown_mask.any():
        unmapped = df.loc[unknown_mask, "question_id"].unique().tolist()
        console.print(
            f"[yellow]Warning: {len(unmapped)} question_id(s) not in SECTION_MAP: "
            f"{unmapped}[/yellow]"
        )

    return df


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def fmt_pct(val, decimals: int = 1) -> str:
    """Format a numeric value as a percentage string, or '-' if NaN."""
    if pd.isna(val):
        return "-"
    return f"{val:.{decimals}f}%"


def fmt_mean_sd(mean, sd, n: int, decimals: int = 1) -> str:
    """Format mean with optional SD in parentheses.

    SD is shown only when n > 2 and sd is not NaN.
    """
    if n > 2 and not pd.isna(sd):
        return f"{mean:.{decimals}f}% ({sd:.{decimals}f}%)"
    return f"{mean:.{decimals}f}%"


def render_md_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub-flavoured Markdown table.

    Caller is responsible for pre-formatting columns as strings.
    Float values are NOT automatically formatted.
    """
    header = "| " + " | ".join(str(c) for c in df.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    data_rows = [
        "| " + " | ".join(str(v) for v in row) + " |"
        for row in df.itertuples(index=False)
    ]
    return "\n".join([header, sep] + data_rows)


# ---------------------------------------------------------------------------
# Table builders
# ---------------------------------------------------------------------------


def _build_df_models(audits: list[dict], manifest: pd.DataFrame) -> pd.DataFrame:
    """Build per-model score summary DataFrame.

    Returns DataFrame with columns:
        model_id, org_type, domain,
        score_1, score_1i, score_2, score_3, score_4, total,
        accuracy_pct, completeness_pct, hallucination_pct, na_pct
    """
    manifest_index = manifest.set_index("model_id")
    model_rows: list[dict] = []

    for audit in audits:
        model_id = audit.get("model_id", "unknown")
        summary = audit.get("summary", {})

        if model_id in manifest_index.index:
            org_type = manifest_index.at[model_id, "org_type"]
            domain = manifest_index.at[model_id, "domain"]
        else:
            org_type = "unknown"
            domain = "unknown"

        s1 = summary.get("score_1_count", 0)
        s1i = summary.get("score_1i_count", 0)
        s2 = summary.get("score_2_count", 0)
        s3 = summary.get("score_3_count", 0)
        s4 = summary.get("score_4_count", 0)
        total = summary.get("total_fields", 0)

        # Guard against division by zero
        if total > 0:
            accuracy_pct = (s1 + s1i + s4) / total * 100
            completeness_pct = (s1 + s1i) / total * 100
            hallucination_pct = s2 / total * 100
            na_pct = s4 / total * 100
        else:
            accuracy_pct = completeness_pct = hallucination_pct = na_pct = float("nan")

        model_rows.append(
            {
                "model_id": model_id,
                "org_type": org_type,
                "domain": domain,
                "score_1": s1,
                "score_1i": s1i,
                "score_2": s2,
                "score_3": s3,
                "score_4": s4,
                "total": total,
                "accuracy_pct": accuracy_pct,
                "completeness_pct": completeness_pct,
                "hallucination_pct": hallucination_pct,
                "na_pct": na_pct,
            }
        )

    return pd.DataFrame(model_rows) if model_rows else pd.DataFrame()


def make_table1(df_models: pd.DataFrame) -> pd.DataFrame:
    """Table 1: Aggregate summary statistics across all models.

    Rows: per-score-category counts + derived rates.
    Columns: Metric, Mean, Median, SD, Min, Max, N

    Returns:
        Formatted DataFrame ready to export as CSV.
    """
    count_cols = ["score_1", "score_1i", "score_2", "score_3", "score_4"]
    rate_cols = ["accuracy_pct", "completeness_pct", "hallucination_pct", "na_pct"]

    label_map_counts = {
        "score_1": "Direct (1)",
        "score_1i": "Inferred (1i)",
        "score_2": "Hallucinated (2)",
        "score_3": "Incomplete (3)",
        "score_4": "Unavailable (4)",
    }
    label_map_rates = {
        "accuracy_pct": "Accuracy Rate",
        "completeness_pct": "Completeness Rate",
        "hallucination_pct": "Hallucination Rate",
        "na_pct": "N/A Rate",
    }

    output_rows: list[dict] = []
    n_models = len(df_models)

    for col, label in label_map_counts.items():
        if col not in df_models.columns:
            continue
        series = df_models[col]
        mean_val = series.mean()
        median_val = series.median()
        sd_val = series.std(ddof=1) if n_models > 1 else float("nan")
        min_val = series.min()
        max_val = series.max()

        output_rows.append(
            {
                "Metric": label,
                "Mean": f"{mean_val:.1f}",
                "Median": f"{median_val:.1f}",
                "SD": "-" if pd.isna(sd_val) else f"{sd_val:.1f}",
                "Min": str(int(min_val)),
                "Max": str(int(max_val)),
                "N": str(n_models),
            }
        )

    for col, label in label_map_rates.items():
        if col not in df_models.columns:
            continue
        series = df_models[col].dropna()
        n = len(series)
        if n == 0:
            continue
        mean_val = series.mean()
        median_val = series.median()
        sd_val = series.std(ddof=1) if n > 1 else float("nan")
        min_val = series.min()
        max_val = series.max()

        output_rows.append(
            {
                "Metric": label,
                "Mean": fmt_pct(mean_val),
                "Median": fmt_pct(median_val),
                "SD": "-" if pd.isna(sd_val) else fmt_pct(sd_val),
                "Min": fmt_pct(min_val),
                "Max": fmt_pct(max_val),
                "N": str(n),
            }
        )

    return pd.DataFrame(output_rows, columns=["Metric", "Mean", "Median", "SD", "Min", "Max", "N"])


def make_table2(df_models: pd.DataFrame, manifest: pd.DataFrame) -> pd.DataFrame:
    """Table 2: Per-model score detail, sorted by Accuracy% descending.

    Columns: Model, Org Type, Domain, Direct(1), Inferred(1i),
             Hallucinated(2), Incomplete(3), N/A(4), Accuracy%, Completeness%

    Includes an Average row at the bottom.

    Returns:
        Formatted DataFrame ready to export as CSV.
    """
    if df_models.empty:
        return pd.DataFrame()

    sorted_df = df_models.sort_values("accuracy_pct", ascending=False)

    output_rows: list[dict] = []
    for _, row in sorted_df.iterrows():
        output_rows.append(
            {
                "Model": row["model_id"],
                "Org Type": row["org_type"],
                "Domain": row["domain"],
                "Direct(1)": str(int(row["score_1"])),
                "Inferred(1i)": str(int(row["score_1i"])),
                "Hallucinated(2)": str(int(row["score_2"])),
                "Incomplete(3)": str(int(row["score_3"])),
                "N/A(4)": str(int(row["score_4"])),
                "Accuracy%": fmt_pct(row["accuracy_pct"]),
                "Completeness%": fmt_pct(row["completeness_pct"]),
            }
        )

    # Average row
    count_cols = ["score_1", "score_1i", "score_2", "score_3", "score_4"]
    output_rows.append(
        {
            "Model": "Average",
            "Org Type": "-",
            "Domain": "-",
            "Direct(1)": f"{df_models['score_1'].mean():.1f}",
            "Inferred(1i)": f"{df_models['score_1i'].mean():.1f}",
            "Hallucinated(2)": f"{df_models['score_2'].mean():.1f}",
            "Incomplete(3)": f"{df_models['score_3'].mean():.1f}",
            "N/A(4)": f"{df_models['score_4'].mean():.1f}",
            "Accuracy%": fmt_pct(df_models["accuracy_pct"].mean()),
            "Completeness%": fmt_pct(df_models["completeness_pct"].mean()),
        }
    )

    return pd.DataFrame(
        output_rows,
        columns=[
            "Model", "Org Type", "Domain",
            "Direct(1)", "Inferred(1i)", "Hallucinated(2)",
            "Incomplete(3)", "N/A(4)", "Accuracy%", "Completeness%",
        ],
    )


def _make_group_table(
    df_models: pd.DataFrame,
    group_col: str,
    display_col_name: str,
) -> pd.DataFrame:
    """Shared logic for Tables 3 and 4 (group by org_type or domain)."""
    if df_models.empty:
        return pd.DataFrame()

    rate_cols = {
        "accuracy_pct": "Avg Accuracy%",
        "completeness_pct": "Avg Completeness%",
        "hallucination_pct": "Avg Hallucination%",
        "na_pct": "Avg N/A%",
    }

    output_rows: list[dict] = []
    grouped = df_models.groupby(group_col, observed=True)

    # Sorted group rows
    for group_val, group_df in sorted(grouped, key=lambda kv: str(kv[0])):
        n = len(group_df)
        row: dict = {display_col_name: group_val, "N": n}
        for col, header in rate_cols.items():
            mean_val = group_df[col].mean()
            sd_val = group_df[col].std(ddof=1) if n > 1 else float("nan")
            row[header] = fmt_mean_sd(mean_val, sd_val, n)
        output_rows.append(row)

    # "All" row
    n_all = len(df_models)
    all_row: dict = {display_col_name: "All", "N": n_all}
    for col, header in rate_cols.items():
        mean_val = df_models[col].mean()
        sd_val = df_models[col].std(ddof=1) if n_all > 1 else float("nan")
        all_row[header] = fmt_mean_sd(mean_val, sd_val, n_all)
    output_rows.append(all_row)

    cols = [display_col_name, "N"] + list(rate_cols.values())
    return pd.DataFrame(output_rows, columns=cols)


def make_table3(df_models: pd.DataFrame) -> pd.DataFrame:
    """Table 3: Accuracy and completeness grouped by org_type.

    Columns: Org Type, N, Avg Accuracy%, Avg Completeness%, Avg Hallucination%, Avg N/A%
    Rows: one per org_type (alphabetical), plus All at bottom.
    """
    return _make_group_table(df_models, "org_type", "Org Type")


def make_table4(df_models: pd.DataFrame) -> pd.DataFrame:
    """Table 4: Accuracy and completeness grouped by domain.

    Columns: Domain, N, Avg Accuracy%, Avg Completeness%, Avg Hallucination%, Avg N/A%
    Rows: one per domain (alphabetical), plus All at bottom.
    """
    return _make_group_table(df_models, "domain", "Domain")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


@app.command()
def run(
    audit_dir: Path = typer.Argument(
        ...,
        help="Batch root directory containing one subdirectory per audited model.",
    ),
    models_csv: Optional[Path] = typer.Option(
        None,
        "--models-csv",
        "-m",
        help="Path to models CSV with model_id, org_type, domain columns.",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Directory to write output files. Defaults to audit_dir.",
    ),
    batch_name: Optional[str] = typer.Option(
        None,
        "--batch-name",
        "-n",
        help="Optional label for the batch (used in report header).",
    ),
) -> None:
    """Generate analytical compliance report tables from a batch of audits."""

    # Resolve output directory
    out_dir = output_dir if output_dir is not None else audit_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(
        f"[bold green]Batch Report Generator[/bold green]\n"
        f"  Audit dir:  {audit_dir}\n"
        f"  Models CSV: {models_csv}\n"
        f"  Output dir: {out_dir}\n"
        f"  Batch name: {batch_name or '(none)'}\n"
    )

    # ------------------------------------------------------------------
    # Stage 1 — Load
    # ------------------------------------------------------------------
    audits, skipped = load_batch_audits(audit_dir)
    console.print(
        f"[cyan]Stage 1 — Load:[/cyan] {len(audits)} audit(s) loaded, "
        f"{len(skipped)} dir(s) skipped."
    )
    if skipped:
        for name in skipped:
            console.print(f"  [yellow]Skipped: {name}[/yellow]")

    if not audits:
        console.print("[red]No valid audits found. Exiting.[/red]")
        raise typer.Exit(1)

    # ------------------------------------------------------------------
    # Stage 2 — Load manifest
    # ------------------------------------------------------------------
    if models_csv is None:
        console.print(
            "[yellow]Warning: no --models-csv provided. "
            "org_type and domain will be 'unknown' for all models.[/yellow]"
        )
        manifest = pd.DataFrame(columns=["model_id", "org_type", "domain"])
    else:
        manifest = load_manifest(models_csv)
        console.print(
            f"[cyan]Stage 2 — Manifest:[/cyan] {len(manifest)} models in CSV."
        )

    # Check for manifest models that have no audit result
    if not manifest.empty and "model_id" in manifest.columns:
        audited_model_ids = {a.get("model_id", "") for a in audits}
        missing_from_audits = [
            mid for mid in manifest["model_id"]
            if mid not in audited_model_ids
        ]
        if missing_from_audits:
            console.print(
                f"[yellow]Warning: {len(missing_from_audits)} model(s) in manifest "
                f"have no audit_results.json:[/yellow]"
            )
            for mid in missing_from_audits:
                console.print(f"  [yellow]  Missing audit: {mid}[/yellow]")

    # ------------------------------------------------------------------
    # Stage 3 — Build combined field-level DataFrame
    # ------------------------------------------------------------------
    df_combined = build_combined_df(audits, manifest)
    combined_path = out_dir / "combined_field_audits.csv"
    df_combined.to_csv(combined_path, index=False, encoding="utf-8")
    console.print(
        f"[cyan]Stage 3 — Combined:[/cyan] {len(df_combined)} field-audit rows. "
        f"Written to {combined_path}"
    )

    # Build per-model summary DataFrame for Tables 1-4
    df_models = _build_df_models(audits, manifest)

    # ------------------------------------------------------------------
    # Stage 4 — Aggregate (Tables 1-4) and render CSVs
    # ------------------------------------------------------------------
    console.print("[cyan]Stage 4 — Aggregating Tables 1-4 ...[/cyan]")

    # Table 1: Summary statistics
    df_t1 = make_table1(df_models)
    t1_path = out_dir / "table1_summary_stats.csv"
    df_t1.to_csv(t1_path, index=False, encoding="utf-8")
    console.print(f"  Table 1 (summary stats):    {t1_path}")

    # Table 2: Per-model detail
    df_t2 = make_table2(df_models, manifest)
    t2_path = out_dir / "table2_per_model_detail.csv"
    df_t2.to_csv(t2_path, index=False, encoding="utf-8")
    console.print(f"  Table 2 (per-model detail): {t2_path}")

    # Table 3: By org_type
    df_t3 = make_table3(df_models)
    t3_path = out_dir / "table3_by_org_type.csv"
    df_t3.to_csv(t3_path, index=False, encoding="utf-8")
    console.print(f"  Table 3 (by org type):      {t3_path}")

    # Table 4: By domain
    df_t4 = make_table4(df_models)
    t4_path = out_dir / "table4_by_domain.csv"
    df_t4.to_csv(t4_path, index=False, encoding="utf-8")
    console.print(f"  Table 4 (by domain):        {t4_path}")

    # Store tables dict for Plan 02 report assembly
    tables = {1: df_t1, 2: df_t2, 3: df_t3, 4: df_t4}

    console.print(
        "\n[bold green]Tables 1-4 complete. "
        "Run Plan 02 to add Tables 5-8 and generate batch_report.md[/bold green]"
    )


if __name__ == "__main__":
    app()
