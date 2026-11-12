# Huge Pages Test Harness

This Python script tests llama.cpp with and without huge pages and compares their performance.

## How to Run

Build llama.cpp first and put a GGUF model at `test-models/smollm2.gguf`.

Run from the project root:

```bash
python3 tests/hugepages/benchmark.py
```

## What It Does

- Runs normal and huge pages modes 5 times each.
- Records execution time and tokens/s.
- Calculates the average and standard deviation.
- Saves results to CSV files and logs.

## Output

Results are saved in `tests/hugepages/results/`.

- `results.csv` - Results for each run.
- `summary.csv` - Average and standard deviation.
- `.log` files - Program output for each run.

Note: This script compares performance but does not verify that huge pages were actually allocated.
