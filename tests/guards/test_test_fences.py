"""The import contracts fence the test tiers (lean-test-suite P-4, TC-5)."""

import pytest

DOMAIN_CONTRACT = "domain tests import no higher layer or test double"


def test_the_real_tree_keeps_every_contract(tree, lint):
    assert lint(tree).returncode == 0


@pytest.mark.parametrize("imported", ["fingerprint.service_layer.handlers", "fingerprint.adapters.sparql", "tests.fakes"])
def test_a_domain_test_importing_a_higher_layer_or_a_double_fails(tree, lint, imported):
    (tree / "tests" / "unit" / "domain" / "test_violation.py").write_text(f"import {imported}\n")
    result = lint(tree)
    assert result.returncode != 0
    assert DOMAIN_CONTRACT in result.stdout
