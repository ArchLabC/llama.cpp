# Huge Pages Test Harness

This Python script tests llama.cpp with and without huge pages to compare their performance.

## Requirements

- Python 3
- Linux
- Built llama.cpp with huge pages support
- A GGUF model

## How to Run

First, build llama.cpp and make sure `llama-cli` is available in `build/bin/`.

Put a GGUF model in the `test-models/` folder. The default model path is:

`test-models/smollm2.gguf`

Run the script from the llama.cpp root directory:

```bash
python3 tests/hugepages/benchmark.py
```

If you use a different model, change the `MODEL` path in `benchmark.py`.

## What It Does

The script runs two modes:

- **Normal:** Runs llama.cpp without huge pages.
- **Huge Pages:** Runs llama.cpp with the `--hugepages` option.

Each mode runs 5 times by default.

For each run, the script records:

- **Execution time:** Total time taken to run the program.
- **Prompt tokens/s:** Speed of processing the input.
- **Generation tokens/s:** Speed of generating the response.
- **Status:** PASS, FAIL, or TIMEOUT.

It also calculates the mean and standard deviation for each performance metric.

## Results

All results are saved in `tests/hugepages/results/`.

- `results.csv` - Results from each individual run.
- `summary.csv` - Mean and standard deviation for both modes.
- `.log` files - Output from each run.

The script also prints a summary in the terminal after all tests finish.

## Note

PASS means the program exited successfully. It does not confirm that huge pages were actually allocated.
