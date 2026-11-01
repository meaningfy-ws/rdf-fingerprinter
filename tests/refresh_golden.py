"""Regenerates the golden outputs from the sample profile: `make refresh-golden` (P-5).

Writes only the files whose text changed; review the diff afterwards.
"""

from fingerprint.adapters.profile_file import load_profile
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.profile import ProfileRun
from fingerprint.service_layer.generators import GENERATORS
from fingerprint.service_layer.representations import make_generator
from tests.sample_data import GOLDEN, SAMPLE_PROFILE


def render(run: ProfileRun, name: str) -> dict[str, str]:
    """The files generator `name` writes for `run`, as file name → text."""
    documents = make_generator(name, analyse(run), JinjaTemplateRenderer()).serialize()
    return {d.file_name: d.text for d in documents}


def main() -> None:
    run = load_profile(SAMPLE_PROFILE)
    GOLDEN.mkdir(exist_ok=True)
    changed = []
    for name in sorted(GENERATORS):
        for file_name, text in render(run, name).items():
            path = GOLDEN / file_name
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                path.write_text(text, encoding="utf-8")
                changed.append(file_name)
    print("\n".join(f"rewrote {n}" for n in changed) or "golden outputs are up to date")


if __name__ == "__main__":
    main()
