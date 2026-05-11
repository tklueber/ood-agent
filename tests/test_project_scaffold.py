from __future__ import annotations

import ood


def test_package_imports_from_src_layout() -> None:
    assert ood.__file__ is not None
    assert "/src/ood/" in ood.__file__.replace("\\", "/")


def test_package_exposes_non_empty_version() -> None:
    assert isinstance(ood.__version__, str)
    assert ood.__version__.strip()
