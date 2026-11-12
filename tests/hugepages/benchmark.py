
import subprocess
import time
import csv
from pathlib import Path

# Configuration
MODEL = "test-models/smollm2.gguf"
BINARY = "./build/bin/llama-cli"
REPEATS = 5
TIMEOUT = 120

RESULTS_DIR = Path("tests/hugepages/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

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
                stdin=subprocess.DEVNULL,
            )

            elapsed = time.perf_counter() - start
            status = "PASS" if result.returncode == 0 else "FAIL"

            log_path = RESULTS_DIR / f"{mode}_{run}.log"
            log_path.write_text(
                result.stdout + "\n" + result.stderr,
                encoding="utf-8",
            )

            results.append({
                "mode": mode,
                "run": run,
                "elapsed_seconds": round(elapsed, 3),
                "exit_code": result.returncode,
                "status": status,
            })

        except subprocess.TimeoutExpired:
            results.append({
                "mode": mode,
                "run": run,
                "elapsed_seconds": TIMEOUT,
                "exit_code": "",
                "status": "TIMEOUT",
            })

# Save results
csv_path = RESULTS_DIR / "results.csv"

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "mode",
            "run",
            "elapsed_seconds",
            "exit_code",
            "status",
        ],
    )
    writer.writeheader()
    writer.writerows(results)

print(f"\nResults saved to {csv_path}")
