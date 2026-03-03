"""
Verify HuggingFace Model Cards for Test Models CSV
====================================================
Reads a CSV containing a model_id column and checks whether each model's
HuggingFace model card is reachable. Useful for catching broken or
non-existent model IDs before running expensive compliance evaluations.

Output:
  [OK]   model_id              — model card is accessible
  [OK]   model_id (gated …)   — model is gated but card exists
  [FAIL] model_id — reason    — model card is missing or errored

Exits with code 1 if any model is inaccessible (CI-friendly).

Usage:
  python3 verify_model_cards.py
  python3 verify_model_cards.py --input test_models.csv
  python3 verify_model_cards.py --input test_models.csv --verbose
"""

import csv
import sys
import argparse
from huggingface_hub import model_info
from huggingface_hub.utils import RepositoryNotFoundError, GatedRepoError


def check_model_card(model_id: str) -> tuple[bool, str]:
    """
    Check whether a HuggingFace model card is reachable.

    Returns:
        (True, "OK")                    — model card accessible
        (True, "gated (card exists)")   — gated repo; card exists
        (False, "not found")            — repository does not exist
        (False, "error: <message>")     — unexpected error
    """
    try:
        model_info(model_id)
        return (True, "OK")
    except RepositoryNotFoundError:
        return (False, "not found")
    except GatedRepoError:
        return (True, "gated (card exists)")
    except Exception as e:
        return (False, f"error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Verify HuggingFace model cards for every model_id in a CSV"
    )
    parser.add_argument(
        "--input", "-i",
        default="test_models.csv",
        help="Path to input CSV with model_id column (default: test_models.csv)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print additional details for each model",
    )
    args = parser.parse_args()

    # Read CSV and collect model IDs
    try:
        with open(args.input, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            # DictReader uses the raw header as keys; strip surrounding whitespace
            # so "model_id" and " model_id" both resolve correctly.
            rows = []
            for row in reader:
                # Build a whitespace-stripped key lookup
                stripped_row = {k.strip(): v.strip() for k, v in row.items()}
                model_id = stripped_row.get("model_id", "")
                if model_id:
                    rows.append(model_id)
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("ERROR: No model IDs found in CSV.", file=sys.stderr)
        sys.exit(1)

    total = len(rows)
    print(f"Checking {total} model(s) from {args.input} ...\n")

    results = []
    for model_id in rows:
        ok, reason = check_model_card(model_id)
        results.append((model_id, ok, reason))
        if ok:
            if reason == "OK":
                print(f"[OK]   {model_id}")
            else:
                # Gated or other positive status
                print(f"[OK]   {model_id}  ({reason})")
        else:
            print(f"[FAIL] {model_id} — {reason}")

        if args.verbose:
            print(f"       status: {'accessible' if ok else 'inaccessible'}, reason: {reason}")

    # Summary
    accessible = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Total:       {total}")
    print(f"  Accessible:  {len(accessible)}")
    print(f"  Failed:      {len(failed)}")

    if failed:
        print(f"\nFailed model IDs:")
        for model_id, _, reason in failed:
            print(f"  - {model_id}  ({reason})")
        print(f"\n[FAIL] {len(failed)} model(s) not accessible. Exiting with code 1.")
        sys.exit(1)
    else:
        print(f"\n[OK] All {total} model(s) have accessible model cards.")


if __name__ == "__main__":
    main()
