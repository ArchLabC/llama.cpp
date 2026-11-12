
import subprocess
import time
import csv
import re
import statistics
from pathlib import Path
import argparse

# Configuration
parser = argparse.ArgumentParser(description="Huge Pages Benchmark")

parser.add_argument(
    "--model",
    default="test-models/smollm2.gguf",
    help="Path to the GGUF model",
)

parser.add_argument(
    "--repeats",
    type=int,
    default=5,
    help="Number of runs per mode",
)

args = parser.parse_args()

MODEL = args.model
REPEATS = args.repeats
BINARY = "./build/bin/llama-cli"
TIMEOUT = 120

if REPEATS < 1:
    parser.error("--repeats must be at least 1")

if not Path(MODEL).is_file():
    parser.error(f"Model not found: {MODEL}")


    

RESULTS_DIR = Path("tests/hugepages/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Matches: [ Prompt: 205.8 t/s | Generation: 30.5 t/s ]
PERF_PATTERN = re.compile(
    r"Prompt:\s*([\d.]+)\s*t/s\s*\|\s*Generation:\s*([\d.]+)\s*t/s",
    re.IGNORECASE,
)

results = []

for mode in ["normal", "hugepages"]:
    for run in range(1, REPEATS + 1):
        command = [
            BINARY,
            "-m", MODEL,
            "--load-mode", "none",
            "-ngl", "0",
            "-t", "4",
            "-p", "What is 2+2?",
            "-n", "32",
            "--single-turn",
            "--simple-io",
            "--show-timings",
            "--no-display-prompt",
        ]

        if mode == "hugepages":
            command.append("--hugepages")

        print(f"Running {mode}, trial {run}/{REPEATS}")

        start = time.perf_counter()

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
                input="",
            )

            elapsed = time.perf_counter() - start
            output = result.stdout + "\n" + result.stderr

            log_path = RESULTS_DIR / f"{mode}_{run}.log"
            log_path.write_text(output, encoding="utf-8")

            matches = PERF_PATTERN.findall(output)
            prompt_tps = ""
            generation_tps = ""

            if matches:
                prompt_tps = float(matches[-1][0])
                generation_tps = float(matches[-1][1])

            status = "PASS" if result.returncode == 0 else "FAIL"

            results.append({
                "mode": mode,
                "run": run,
                "elapsed_seconds": round(elapsed, 3),
                "prompt_tps": prompt_tps,
                "generation_tps": generation_tps,
                "exit_code": result.returncode,
                "status": status,
            })

        except subprocess.TimeoutExpired as exc:
            elapsed = time.perf_counter() - start
            partial = exc.stdout or b""
            if isinstance(partial, bytes):
                partial = partial.decode("utf-8", errors="replace")
            RESULTS_DIR.joinpath(f"{mode}_{run}.log").write_text(
                partial + "\nTIMEOUT\n", encoding="utf-8"
            )

            results.append({
                "mode": mode,
                "run": run,
                "elapsed_seconds": round(elapsed, 3),
                "prompt_tps": "",
                "generation_tps": "",
                "exit_code": "",
                "status": "TIMEOUT",
            })

# Save detailed results
csv_path = RESULTS_DIR / "results.csv"

fields = [
    "mode", "run", "elapsed_seconds",
    "prompt_tps", "generation_tps",
    "exit_code", "status",
]

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(results)

print(f"\nResults saved to {csv_path}")

# Calculate summary statistics
summary = []

for mode in ["normal", "hugepages"]:
    successful = [
        row for row in results
        if row["mode"] == mode and row["status"] == "PASS"
    ]

    row = {"mode": mode, "successful_runs": len(successful)}

    for metric in ["elapsed_seconds", "prompt_tps", "generation_tps"]:
        values = [
            float(r[metric]) for r in successful
            if r[metric] != ""
        ]

        row[f"{metric}_mean"] = (
            round(statistics.mean(values), 3) if values else ""
        )
        row[f"{metric}_std"] = (
            round(statistics.stdev(values), 3)
            if len(values) > 1 else (0 if values else "")
        )

    summary.append(row)

# Save summary CSV
summary_path = RESULTS_DIR / "summary.csv"
summary_fields = [
    "mode", "successful_runs",
    "elapsed_seconds_mean", "elapsed_seconds_std",
    "prompt_tps_mean", "prompt_tps_std",
    "generation_tps_mean", "generation_tps_std",
]

with summary_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=summary_fields)
    writer.writeheader()
    writer.writerows(summary)

# Print summary
print("\n===== Benchmark Summary =====")

for row in summary:
    print(f"\n{row['mode']} ({row['successful_runs']}/{REPEATS} passed)")

    for metric, label in [
        ("elapsed_seconds", "Total time (s)"),
        ("prompt_tps", "Prompt (tokens/s)"),
        ("generation_tps", "Generation (tokens/s)"),
    ]:
        avg = row[f"{metric}_mean"]
        std = row[f"{metric}_std"]
        if avg != "":
            print(f"  {label}: {avg:.3f} +/- {std:.3f}")
        else:
            print(f"  {label}: N/A")

print(f"\nSummary saved to {summary_path}")
