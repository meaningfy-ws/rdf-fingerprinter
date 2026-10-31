"""Split a namespace's classes into diagram modules of at most `size` classes (readable-representations DEC-7).

The spec's algorithm: seed with the class most linked to the unassigned ones, grow by the class most linked to the
cluster, repeat while linked classes remain, then chunk the rest by name. Ties go by name, so it is deterministic.
"""

from collections import Counter
from collections.abc import Iterable


def cluster(classes: Iterable[str], links: Iterable[tuple[str, str]], size: int) -> list[list[str]]:
    """Modules of the `classes` (short names); each link (a, b) adds 1 to the pair's weight, in either direction."""
    names = sorted(set(classes))
    if len(names) <= size:
        return [names] if names else []
    known = set(names)
    weight: Counter[frozenset[str]] = Counter(  # dict-ok: lookup index pair → link count
        frozenset((a, b)) for a, b in links if a != b and a in known and b in known
    )

    def w(a: str, b: str) -> int:
        return weight[frozenset((a, b))]

    unassigned = list(names)  # kept in name order
    modules: list[list[str]] = []
    while True:
        linked = [c for c in unassigned if any(w(c, o) for o in unassigned if o != c)]
        if not linked:
            break
        seed = max(linked, key=lambda c: (sum(w(c, o) for o in unassigned if o != c), _by_name(c)))
        module = [seed]
        unassigned.remove(seed)
        while len(module) < size:
            scores = [(sum(w(c, m) for m in module), c) for c in unassigned]
            best = max(scores, key=lambda s: (s[0], _by_name(s[1])), default=(0, ""))
            if best[0] <= 0:
                break
            module.append(best[1])
            unassigned.remove(best[1])
        modules.append(sorted(module))
    modules += [unassigned[i : i + size] for i in range(0, len(unassigned), size)]
    return modules


class _by_name:
    """Reverses name order inside max(): the smaller name wins a tie."""

    def __init__(self, name: str):
        self.name = name

    def __lt__(self, other: "_by_name") -> bool:
        return self.name > other.name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _by_name) and self.name == other.name
