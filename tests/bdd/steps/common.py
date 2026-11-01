"""Plain helpers shared by the step modules (the fixtures and the steps themselves are in `tests/bdd/conftest.py`)."""

from click.testing import CliRunner

from fingerprint.entrypoints.cli import main as cli
from tests.builders import failure, klass, profile_run, prop
from tests.fakes import EX
from tests.sample_data import TEST_DATA

ENDPOINT = "http://fake/sparql"
READABILITY = TEST_DATA / "profiles" / "readability-profile.json"


def person_run(instances=3, observed=None, failures=()):
    """A one-class run: `ex:Person` with one `ex:name` value per observed instance."""
    observed = instances if observed is None else observed
    return profile_run(klass(EX + "Person", instances, prop(EX + "name", {1: observed}), observed=observed), failures=failures)


def big_failure():
    return failure(EX + "Big", "class Big: not profiled after 2 attempts")


def run_fingerprint(ctx, *args):
    """The `fingerprint` command against the scenario's endpoint, output folder and extra arguments."""
    command = ["-e", ctx.get("url", ENDPOINT), "-o", str(ctx["output"]), *ctx.get("args", []), *args]
    ctx["result"] = CliRunner().invoke(cli.fingerprint_endpoint, command)
