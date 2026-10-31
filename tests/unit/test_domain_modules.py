"""Diagram modules: deterministic clusters of linked classes (profile-representations › PlantUML class diagram)."""

import random

from fingerprint.domain.modules import cluster


def test_the_spec_example():
    links = [("A", "B"), ("A", "B"), ("B", "C"), ("C", "D"), ("E", "F")]
    assert cluster(list("ABCDEFG"), links, 3) == [["A", "B", "C"], ["E", "F"], ["D", "G"]]


def test_small_namespaces_are_one_module():
    assert cluster(["B", "A"], [], 15) == [["A", "B"]]


def test_big_namespaces_split_deterministically_with_every_class_once():
    names = [f"C{n:02}" for n in range(40)]
    rng = random.Random(7)
    links = [(rng.choice(names), rng.choice(names)) for _ in range(80)]
    modules = cluster(names, links, 15)
    assert len(modules) >= 3 and all(len(m) <= 15 for m in modules)
    assert sorted(c for m in modules for c in m) == sorted(names)
    assert cluster(list(reversed(names)), list(reversed(links)), 15) == modules


def test_self_links_and_unknown_classes_are_ignored():
    assert cluster(["A", "B"], [("A", "A"), ("A", "Z")], 1) == [["A"], ["B"]]
