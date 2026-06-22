from __future__ import annotations

import pytest

from suisave.core import SuisaveRunError, acquire_run_lock


def test_acquire_run_lock_rejects_second_holder(tmp_path, monkeypatch) -> None:
    lock_path = tmp_path / "suisave-local.lock"
    monkeypatch.setattr("suisave.core.get_run_lock_path", lambda kind: lock_path)

    with acquire_run_lock("local"):
        with pytest.raises(SuisaveRunError, match="already active"):
            with acquire_run_lock("local"):
                pass
