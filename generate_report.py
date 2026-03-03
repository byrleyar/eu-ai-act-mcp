"""Batch Analytical Report Generator for EU AI Act Compliance Audits.

Aggregates audit_results.json files produced by audit_processor.py into
publication-ready analytical tables and a Markdown report.

Usage:
    python generate_report.py <audit_dir> --models-csv test_models.csv --output-dir <out>

Pipeline stages:
    1. Load  — walk audit_dir, read each audit_results.json
    2. Join  — load models-csv manifest, enrich audits with org_type / domain
    3. Agg   — build combined_field_audits.csv + df_models for Tables 1-4
    4. Render — write CSVs (Tables 1-8) + batch_report.md Markdown assembly
"""

import json
import math
from datetime import datetime, timezone
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
    for col in df.select_dtypes(include=["object", "string"]).columns:
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
# Tables 5-8 — section-level and question-level analytics
# ---------------------------------------------------------------------------


def make_table5(combined_df: pd.DataFrame) -> pd.DataFrame:
    """Table 5: Section-Level Unavailability (N/A Rate).

    Columns: Section, Questions in Section, Avg Score-4 Count, Avg N/A%, SD, Min, Max

    For each (section, model_id) pair, counts how many field_audits have score == "4",
    then aggregates across models per section, sorted by avg_na_pct descending.

    Returns:
        Formatted DataFrame ready for Markdown and CSV export.
    """
    if combined_df.empty:
        return pd.DataFrame(
            columns=[
                "Section", "Questions in Section", "Avg Score-4 Count",
                "Avg N/A %", "SD", "Min", "Max",
            ]
        )

    # Step 1: count score-4 per (section, model_id) pair
    section_model_df = (
        combined_df
        .groupby(["section", "model_id"], observed=True)
        .apply(lambda x: (x["score"] == "4").sum(), include_groups=False)
        .reset_index(name="na_count")
    )

    # Step 2: questions per section from SECTION_MAP
    questions_per_section: dict[str, int] = {
        section: len(qids) for section, qids in SECTION_MAP.items()
    }

    # Step 3: aggregate across models per section
    grouped = (
        section_model_df
        .groupby("section", observed=True)
        .agg(
            avg_na_count=("na_count", "mean"),
            sd_na_count=("na_count", "std"),
            min_na=("na_count", "min"),
            max_na=("na_count", "max"),
        )
        .reset_index()
    )

    # Step 4: add questions_in_section
    grouped["questions_in_section"] = grouped["section"].map(
        lambda s: questions_per_section.get(s, 0)
    )

    # Step 5: compute avg_na_pct
    grouped["avg_na_pct"] = grouped.apply(
        lambda row: (row["avg_na_count"] / row["questions_in_section"] * 100)
        if row["questions_in_section"] > 0
        else float("nan"),
        axis=1,
    )

    # Step 6: sort by avg_na_pct descending
    grouped = grouped.sort_values("avg_na_pct", ascending=False).reset_index(drop=True)

    # Step 7: format output columns
    output_rows = []
    for _, row in grouped.iterrows():
        sd_val = row["sd_na_count"]
        sd_str = "-" if pd.isna(sd_val) else f"{sd_val:.1f}"
        output_rows.append(
            {
                "Section": row["section"],
                "Questions in Section": int(row["questions_in_section"]),
                "Avg Score-4 Count": f"{row['avg_na_count']:.1f}",
                "Avg N/A %": fmt_pct(row["avg_na_pct"]),
                "SD": sd_str,
                "Min": int(row["min_na"]),
                "Max": int(row["max_na"]),
            }
        )

    return pd.DataFrame(
        output_rows,
        columns=[
            "Section", "Questions in Section", "Avg Score-4 Count",
            "Avg N/A %", "SD", "Min", "Max",
        ],
    )


def make_table6(
    combined_df: pd.DataFrame,
) -> tuple[pd.DataFrame, str]:
    """Table 6: Section-Level Unavailability by Organization Type.

    Implements the 15pp highlighting rule: cells where abs(cell - section_avg) > 15
    have a "*" suffix in the formatted string.

    Returns:
        (formatted_df, footnote_str) where footnote_str is the markdown footnote
        string to include below the table.
    """
    footnote = "* = differs from overall section average by >15 percentage points"

    if combined_df.empty:
        return pd.DataFrame(columns=["Section"]), footnote

    # Step 1: get org_types (exclude "unknown")
    all_org_types = sorted(
        [ot for ot in combined_df["org_type"].unique() if ot != "unknown"]
    )
    if not all_org_types:
        return pd.DataFrame(columns=["Section"]), footnote

    # Step 2: count score-4 per (section, org_type, model_id)
    section_org_model = (
        combined_df
        .groupby(["section", "org_type", "model_id"], observed=True)
        .apply(lambda x: (x["score"] == "4").sum(), include_groups=False)
        .reset_index(name="na_count")
    )

    # Step 3: avg na_pct per (section, org_type) across models
    questions_per_section: dict[str, int] = {
        section: len(qids) for section, qids in SECTION_MAP.items()
    }

    section_org_agg = (
        section_org_model
        .groupby(["section", "org_type"], observed=True)
        .agg(avg_na_count=("na_count", "mean"))
        .reset_index()
    )
    section_org_agg["q_in_section"] = section_org_agg["section"].map(
        lambda s: questions_per_section.get(s, 0)
    )
    section_org_agg["avg_na_pct"] = section_org_agg.apply(
        lambda row: (row["avg_na_count"] / row["q_in_section"] * 100)
        if row["q_in_section"] > 0
        else float("nan"),
        axis=1,
    )

    # Step 4: pivot — rows=section, columns=org_type, values=avg_na_pct
    pivot = section_org_agg.pivot(
        index="section", columns="org_type", values="avg_na_pct"
    ).reset_index()

    # Ensure all org_type columns present (fill NaN for missing combos)
    for ot in all_org_types:
        if ot not in pivot.columns:
            pivot[ot] = float("nan")

    # Step 5: compute overall avg N/A% per section (across all org_types)
    # Use combined_df directly for the overall per-section na_pct
    section_overall = (
        combined_df
        .groupby(["section", "model_id"], observed=True)
        .apply(lambda x: (x["score"] == "4").sum(), include_groups=False)
        .reset_index(name="na_count")
        .groupby("section", observed=True)
        .agg(avg_na_count=("na_count", "mean"))
        .reset_index()
    )
    section_overall["q_in_section"] = section_overall["section"].map(
        lambda s: questions_per_section.get(s, 0)
    )
    section_overall["overall_avg_pct"] = section_overall.apply(
        lambda row: (row["avg_na_count"] / row["q_in_section"] * 100)
        if row["q_in_section"] > 0
        else float("nan"),
        axis=1,
    )
    overall_dict: dict[str, float] = dict(
        zip(section_overall["section"], section_overall["overall_avg_pct"])
    )

    # Step 6: apply 15pp highlighting, build formatted output
    output_rows = []
    for _, row in pivot.iterrows():
        section = row["section"]
        overall_avg = overall_dict.get(section, float("nan"))
        out_row: dict = {"Section": section}
        for ot in all_org_types:
            cell_val = row.get(ot, float("nan"))
            if pd.isna(cell_val):
                out_row[ot] = "-"
            else:
                cell_str = fmt_pct(cell_val)
                if not pd.isna(overall_avg) and abs(cell_val - overall_avg) > 15.0:
                    cell_str += "*"
                out_row[ot] = cell_str
        output_rows.append(out_row)

    formatted_df = pd.DataFrame(output_rows, columns=["Section"] + all_org_types)
    return formatted_df, footnote


def question_problem_table(
    combined_df: pd.DataFrame,
    score_val: str,
    top_n: int = 15,
) -> tuple[pd.DataFrame, bool]:
    """Shared helper for Tables 7 and 8.

    Args:
        combined_df: Combined field-level DataFrame.
        score_val: Score value to filter on ("2" for hallucinated, "3" for incomplete).
        top_n: Maximum number of rows to return.

    Returns:
        (result_df, has_data) where has_data=False when no matching scores exist.
    """
    if combined_df.empty:
        return pd.DataFrame(), False

    n_models = combined_df["model_id"].nunique()
    flagged = combined_df[combined_df["score"] == score_val]

    if flagged.empty:
        return pd.DataFrame(), False

    agg = (
        flagged
        .groupby(["question_id", "section"], observed=True)
        .agg(
            count=("model_id", "count"),
            models_affected=("model_id", lambda x: ", ".join(sorted(set(x)))),
        )
        .reset_index()
    )
    agg["rate_pct"] = agg["count"] / n_models * 100
    agg = agg.sort_values("rate_pct", ascending=False).head(top_n).reset_index(drop=True)
    agg.insert(0, "rank", range(1, len(agg) + 1))

    return (
        agg[["rank", "question_id", "section", "count", "rate_pct", "models_affected"]],
        True,
    )


def make_table7(combined_df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """Table 7: Most commonly hallucinated questions (score == "2").

    Columns: Rank, Question ID, Section, Hallucination Count, Rate (%), Models Affected

    Returns:
        (formatted_df, has_data)
    """
    df, has_data = question_problem_table(combined_df, score_val="2")
    if not has_data:
        return df, False

    df = df.rename(
        columns={
            "rank": "Rank",
            "question_id": "Question ID",
            "section": "Section",
            "count": "Hallucination Count",
            "rate_pct": "Rate (%)",
            "models_affected": "Models Affected",
        }
    )
    df["Rate (%)"] = df["Rate (%)"].apply(fmt_pct)
    return df, True


def make_table8(combined_df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """Table 8: Most commonly incomplete questions (score == "3").

    Columns: Rank, Question ID, Section, Incomplete Count, Rate (%), Models Affected

    Returns:
        (formatted_df, has_data)
    """
    df, has_data = question_problem_table(combined_df, score_val="3")
    if not has_data:
        return df, False

    df = df.rename(
        columns={
            "rank": "Rank",
            "question_id": "Question ID",
            "section": "Section",
            "count": "Incomplete Count",
            "rate_pct": "Rate (%)",
            "models_affected": "Models Affected",
        }
    )
    df["Rate (%)"] = df["Rate (%)"].apply(fmt_pct)
    return df, True


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------


def _commentary_table1(df: pd.DataFrame) -> str:
    """Auto-generate 1-2 sentence commentary for Table 1."""
    if df.empty:
        return "No data available for aggregate statistics."
    count_rows = df[df["Metric"].isin(
        ["Direct (1)", "Inferred (1i)", "Hallucinated (2)", "Incomplete (3)", "Unavailable (4)"]
    )]
    if count_rows.empty:
        return "Aggregate statistics computed across all audited models."
    # Find the score category with the highest mean count
    # Mean column is a string like "21.0" or "38.0"
    try:
        count_rows = count_rows.copy()
        count_rows["_mean_float"] = count_rows["Mean"].str.rstrip("%").astype(float)
        best = count_rows.loc[count_rows["_mean_float"].idxmax()]
        n_models = best["N"]
        return (
            f"{best['Metric']} has the highest mean count ({best['Mean']}) across "
            f"{n_models} model(s), suggesting this is the dominant outcome in the batch."
        )
    except Exception:
        return "Aggregate statistics computed across all audited models."


def _commentary_table2(df_models: pd.DataFrame) -> str:
    """Auto-generate 1-2 sentence commentary for Table 2."""
    if df_models.empty:
        return "No per-model data available."
    acc = df_models["accuracy_pct"].dropna()
    if acc.empty:
        return "Per-model accuracy data not available."
    min_acc = acc.min()
    max_acc = acc.max()
    if len(acc) == 1:
        return f"Only one model was audited, with an accuracy rate of {min_acc:.1f}%."
    return (
        f"Accuracy ranges from {min_acc:.1f}% to {max_acc:.1f}% across "
        f"{len(acc)} model(s), indicating variation in compliance documentation quality."
    )


def _commentary_group_table(df: pd.DataFrame, group_col: str, metric_col: str) -> str:
    """Auto-generate commentary for Tables 3 and 4 (group tables)."""
    if df.empty:
        return "No data available."
    data_rows = df[df[group_col] != "All"].copy()
    if len(data_rows) <= 1:
        val = data_rows[metric_col].iloc[0] if not data_rows.empty else "N/A"
        group = data_rows[group_col].iloc[0] if not data_rows.empty else "unknown"
        return f"Only one {group_col.lower()} present in this batch: {group} ({val})."
    # Extract numeric part from strings like "72.5% (3.1%)" or "72.5%"
    def extract_num(s: str) -> float:
        try:
            return float(str(s).split("%")[0].strip("(").strip())
        except Exception:
            return float("nan")

    data_rows["_num"] = data_rows[metric_col].apply(extract_num)
    valid = data_rows.dropna(subset=["_num"])
    if valid.empty:
        return "Group-level statistics computed across all models."
    best = valid.loc[valid["_num"].idxmax()]
    worst = valid.loc[valid["_num"].idxmin()]
    return (
        f"{best[group_col]} has the highest avg accuracy ({best[metric_col]}); "
        f"{worst[group_col]} has the lowest ({worst[metric_col]})."
    )


def _commentary_table5(df: pd.DataFrame) -> str:
    """Auto-generate commentary for Table 5."""
    if df.empty:
        return "No section-level N/A data available."
    top_row = df.iloc[0]
    return (
        f"'{top_row['Section']}' has the highest average N/A rate ({top_row['Avg N/A %']}), "
        f"meaning compliance information in this section is most frequently unavailable in model cards."
    )


def _commentary_table6(df: pd.DataFrame) -> str:
    """Auto-generate commentary for Table 6."""
    if df.empty:
        return "No org-type breakdown available (all models have unknown org type)."
    # Count cells with "*" suffix
    n_highlighted = 0
    for col in df.columns[1:]:
        n_highlighted += df[col].astype(str).str.endswith("*").sum()
    if n_highlighted == 0:
        return (
            "No organization type shows N/A rates that deviate more than 15 percentage points "
            "from the section average."
        )
    return (
        f"{n_highlighted} cell(s) are highlighted (*) where an organization type's section N/A rate "
        f"differs from the overall section average by more than 15 percentage points."
    )


def _commentary_table7(df: pd.DataFrame, has_data: bool) -> str:
    """Auto-generate commentary for Table 7."""
    if not has_data:
        return "No hallucinations detected in this batch."
    top = df.iloc[0]
    return (
        f"'{top['Question ID']}' (section: {top['Section']}) is the most frequently hallucinated "
        f"question, occurring in {top['Hallucination Count']} model(s) at a rate of {top['Rate (%)']}."
    )


def _commentary_table8(df: pd.DataFrame, has_data: bool) -> str:
    """Auto-generate commentary for Table 8."""
    if not has_data:
        return "No incomplete answers detected in this batch."
    top = df.iloc[0]
    return (
        f"'{top['Question ID']}' (section: {top['Section']}) is the most frequently incomplete "
        f"question, occurring in {top['Incomplete Count']} model(s) at a rate of {top['Rate (%)']}."
    )


def assemble_report(
    tables: dict,
    batch_name: Optional[str],
    n_models: int,
    n_missing: int,
    auditor_model: str,
    table6_footnote: str,
    df_models: pd.DataFrame,
) -> str:
    """Build the complete Markdown batch report as a string.

    Args:
        tables: Dict with keys 1-8 mapping to formatted DataFrames.
                Keys 7 and 8 are (df, has_data) tuples.
        batch_name: Optional batch label string.
        n_models: Number of successfully audited models.
        n_missing: Number of models in manifest with no audit results.
        auditor_model: Model ID used for auditing (or "unknown").
        table6_footnote: Footnote string for Table 6's highlighting rule.
        df_models: Raw per-model numeric DataFrame (for commentary).

    Returns:
        Complete Markdown string for batch_report.md.
    """
    now_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # -- Header --
    lines: list[str] = [
        "# EU AI Act Compliance Batch Report",
        "",
        f"**Batch:** {batch_name or 'unnamed'}",
        f"**Generated:** {now_str}",
        f"**Models audited:** {n_models}",
    ]
    if n_missing > 0:
        lines.append(f"**Models in manifest but not audited:** {n_missing}")
    lines += [
        f"**Auditor model:** {auditor_model}",
        "",
        "---",
        "",
    ]

    # -- Table 1 --
    t1 = tables[1]
    lines += [
        "## Table 1: Aggregate Summary Statistics",
        "",
        render_md_table(t1),
        "",
        f"*Key finding: {_commentary_table1(t1)}*",
        "",
    ]

    # -- Table 2 --
    t2 = tables[2]
    lines += [
        "## Table 2: Per-Model Score Detail",
        "",
        render_md_table(t2),
        "",
        f"*Key finding: {_commentary_table2(df_models)}*",
        "",
    ]

    # -- Table 3 --
    t3 = tables[3]
    lines += [
        "## Table 3: Accuracy and Completeness by Organization Type",
        "",
        render_md_table(t3),
        "",
        f"*Key finding: {_commentary_group_table(t3, 'Org Type', 'Avg Accuracy%')}*",
        "",
    ]

    # -- Table 4 --
    t4 = tables[4]
    lines += [
        "## Table 4: Accuracy and Completeness by Domain",
        "",
        render_md_table(t4),
        "",
        f"*Key finding: {_commentary_group_table(t4, 'Domain', 'Avg Accuracy%')}*",
        "",
    ]

    # -- Table 5 --
    t5 = tables[5]
    lines += [
        "## Table 5: Section-Level Unavailability (N/A Rate)",
        "",
        render_md_table(t5),
        "",
        f"*Key finding: {_commentary_table5(t5)}*",
        "",
    ]

    # -- Table 6 --
    t6 = tables[6]
    lines += [
        "## Table 6: Section-Level Unavailability by Organization Type",
        "",
        render_md_table(t6) if not t6.empty else "> No organization type data available.",
        "",
        table6_footnote,
        "",
        f"*Key finding: {_commentary_table6(t6)}*",
        "",
    ]

    # -- Table 7 --
    t7_df, t7_has = tables[7]
    t7_md = render_md_table(t7_df) if t7_has else "> No hallucinated answers (score 2) were found across this batch."
    lines += [
        "## Table 7: Most Commonly Hallucinated Questions",
        "",
        t7_md,
        "",
        f"*Key finding: {_commentary_table7(t7_df, t7_has)}*",
        "",
    ]

    # -- Table 8 --
    t8_df, t8_has = tables[8]
    t8_md = render_md_table(t8_df) if t8_has else "> No incomplete answers (score 3) were found across this batch."
    lines += [
        "## Table 8: Most Commonly Incomplete Questions",
        "",
        t8_md,
        "",
        f"*Key finding: {_commentary_table8(t8_df, t8_has)}*",
        "",
        "---",
        "",
    ]

    # -- Methodology section --
    total_questions = sum(len(qids) for qids in SECTION_MAP.values())
    section_names = ", ".join(SECTION_MAP.keys())

    lines += [
        "## Methodology",
        "",
        "### Scoring Rubric",
        "",
        "| Score | Label | Description |",
        "| --- | --- | --- |",
        "| 1 | Accurate (Direct) | Answer directly stated in source materials |",
        "| 1i | Accurate (Inferred) | Answer correctly derived from indirect evidence |",
        "| 2 | Inaccurate/Hallucinated | Answer asserts info not in or contradicted by sources |",
        "| 3 | Incomplete | Answer misses information present in sources |",
        "| 4 | Appropriately Unavailable | Correctly indicates info not available in sources |",
        "",
        "### Derived Metrics",
        "",
        "- **Accuracy Rate** = (Score 1 + Score 1i + Score 4) / Total × 100 — measures correctness given available information",
        "- **Completeness Rate** = (Score 1 + Score 1i) / Total × 100 — measures how much information is ready to submit without human review",
        "- **Hallucination Rate** = Score 2 / Total × 100 — measures fabricated or contradicted information",
        "- **N/A Rate** = Score 4 / Total × 100 — measures fields where information is unavailable in source materials",
        "",
        "### Section Mapping",
        "",
        f"This report uses 8 compliance form sections covering {total_questions} questions as defined in `report_generator.py`.",
        f"Sections: {section_names}",
        "",
        "Table 6 highlights: cells marked with * differ from the overall section average by more than 15 percentage points.",
    ]

    return "\n".join(lines) + "\n"


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

    # ------------------------------------------------------------------
    # Stage 5 — Tables 5-8 and Markdown report assembly
    # ------------------------------------------------------------------
    console.print("[cyan]Stage 5 — Aggregating Tables 5-8 ...[/cyan]")

    # Table 5: Section-level N/A rates
    df_t5 = make_table5(df_combined)
    t5_path = out_dir / "table5_section_unavailability.csv"
    # Export raw numeric version (not formatted strings) — recompute from combined_df
    # The formatted df_t5 is used for Markdown; raw CSV uses the same data with numeric cols
    df_t5.to_csv(t5_path, index=False, encoding="utf-8")
    console.print(f"  Table 5 (section N/A):      {t5_path}")

    # Table 6: Section N/A by org type
    df_t6, table6_footnote = make_table6(df_combined)
    t6_path = out_dir / "table6_section_by_org.csv"
    # Export raw numeric version (strip "*" markers)
    df_t6_raw = df_t6.copy()
    for col in df_t6_raw.columns[1:]:
        df_t6_raw[col] = df_t6_raw[col].astype(str).str.rstrip("*")
    df_t6_raw.to_csv(t6_path, index=False, encoding="utf-8")
    console.print(f"  Table 6 (section by org):   {t6_path}")

    # Table 7: Hallucinated questions
    df_t7, t7_has_data = make_table7(df_combined)
    t7_path = out_dir / "table7_hallucinated_questions.csv"
    if t7_has_data:
        df_t7.to_csv(t7_path, index=False, encoding="utf-8")
    else:
        # Write header-only CSV when no data
        pd.DataFrame(
            columns=["Rank", "Question ID", "Section", "Hallucination Count", "Rate (%)", "Models Affected"]
        ).to_csv(t7_path, index=False, encoding="utf-8")
    console.print(f"  Table 7 (hallucinations):   {t7_path} {'(no data)' if not t7_has_data else ''}")

    # Table 8: Incomplete questions
    df_t8, t8_has_data = make_table8(df_combined)
    t8_path = out_dir / "table8_incomplete_questions.csv"
    if t8_has_data:
        df_t8.to_csv(t8_path, index=False, encoding="utf-8")
    else:
        pd.DataFrame(
            columns=["Rank", "Question ID", "Section", "Incomplete Count", "Rate (%)", "Models Affected"]
        ).to_csv(t8_path, index=False, encoding="utf-8")
    console.print(f"  Table 8 (incomplete):       {t8_path} {'(no data)' if not t8_has_data else ''}")

    # ------------------------------------------------------------------
    # Stage 6 — Assemble and write batch_report.md
    # ------------------------------------------------------------------
    console.print("[cyan]Stage 6 — Assembling batch_report.md ...[/cyan]")

    # Extract auditor_model from first loaded audit
    auditor_model_val = "unknown"
    if audits:
        auditor_model_val = audits[0].get("auditor_model", "unknown") or "unknown"

    # Count manifest models with no audit result (n_missing)
    n_missing_count = 0
    if not manifest.empty and "model_id" in manifest.columns:
        audited_ids = {a.get("model_id", "") for a in audits}
        n_missing_count = sum(1 for mid in manifest["model_id"] if mid not in audited_ids)

    tables = {
        1: df_t1,
        2: df_t2,
        3: df_t3,
        4: df_t4,
        5: df_t5,
        6: df_t6,
        7: (df_t7, t7_has_data),
        8: (df_t8, t8_has_data),
    }

    report_str = assemble_report(
        tables=tables,
        batch_name=batch_name,
        n_models=len(audits),
        n_missing=n_missing_count,
        auditor_model=auditor_model_val,
        table6_footnote=table6_footnote,
        df_models=df_models,
    )

    report_path = out_dir / "batch_report.md"
    report_path.write_text(report_str, encoding="utf-8")
    console.print(f"  batch_report.md:            {report_path}")

    # ------------------------------------------------------------------
    # Smoke validation
    # ------------------------------------------------------------------
    assert report_path.exists() and report_path.stat().st_size > 0, (
        "batch_report.md was not written or is empty!"
    )
    report_contents = report_path.read_text(encoding="utf-8")
    for i in range(1, 9):
        assert f"## Table {i}" in report_contents, f"Missing '## Table {i}' in batch_report.md"
    assert "## Methodology" in report_contents, "Missing '## Methodology' in batch_report.md"

    # ------------------------------------------------------------------
    # Success summary panel
    # ------------------------------------------------------------------
    all_output_paths = [
        combined_path, t1_path, t2_path, t3_path, t4_path,
        t5_path, t6_path, t7_path, t8_path, report_path,
    ]
    console.print("\n[bold green]Report generation complete![/bold green]")
    console.print(f"\nOutput files in [cyan]{out_dir}[/cyan]:")
    for p in all_output_paths:
        size_kb = p.stat().st_size / 1024
        console.print(f"  {p.name:<45} {size_kb:>7.1f} KB")


if __name__ == "__main__":
    app()
