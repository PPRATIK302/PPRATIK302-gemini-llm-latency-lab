import os

import pytest


@pytest.mark.live
def test_live_tests_are_opt_in() -> None:
    if os.getenv("RUN_LIVE_TESTS") != "true" or not os.getenv("GEMINI_API_KEY"):
        pytest.skip("Set RUN_LIVE_TESTS=true and GEMINI_API_KEY to enable live tests.")
    assert os.getenv("GEMINI_API_KEY")

