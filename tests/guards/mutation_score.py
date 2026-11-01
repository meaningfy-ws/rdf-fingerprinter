"""The mutation-score ratchet (lean-test-suite P-7).

    python tests/guards/mutation_score.py mutants/mutmut-cicd-stats.json tests/guards/mutation_score.txt

Exit 0: score equal or higher (a higher score is written back). Exit 1: score below the stored one.
Exit 2: no usable score (interrupted run, no mutants, unreadable stored score).
"""

import json
import sys
from pathlib import Path
from typing import NamedTuple

EXIT_OK, EXIT_DROPPED, EXIT_ERROR = 0, 1, 2


class Stats(NamedTuple):
    killed: int = 0
    timeout: int = 0
    survived: int = 0
    no_tests: int = 0
    check_was_interrupted_by_user: int = 0


def score(stats: Stats) -> float:
    """Caught mutants over all that count; a mutant no test covers is not caught."""
    caught = stats.killed + stats.timeout
    total = caught + stats.survived + stats.no_tests
    return round(caught / total, 3)


def main(stats_path: Path, stored_path: Path) -> int:
    raw = json.loads(stats_path.read_text())  # dict-ok: the JSON mutmut writes
    stats = Stats(**{name: raw.get(name, 0) for name in Stats._fields})  # dict-ok: kwargs into the model
    if stats.check_was_interrupted_by_user:
        return _error("the mutmut run was interrupted; no score")
    if not (stats.killed + stats.timeout + stats.survived + stats.no_tests):
        return _error("no mutants were generated; no score")
    try:
        stored = float(stored_path.read_text())
        if not 0 <= stored <= 1:
            raise ValueError(stored)
    except FileNotFoundError:
        return _error(f"stored score file {stored_path} is missing; write the baseline first")
    except ValueError:
        return _error(f"stored score file {stored_path} does not hold a number from 0 to 1")
    current = score(stats)
    print(f"mutation score {current:.3f} (stored {stored:.3f})")
    if current < stored:
        print("The score dropped: run `mutmut results` to list the surviving mutants.")
        return EXIT_DROPPED
    if current > stored:
        stored_path.write_text(f"{current:.3f}\n")
        print(f"Raised the stored score in {stored_path}; commit it.")
    return EXIT_OK


def _error(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
