from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def metrics_tmp_dir(tmp_path):
    """Write metrics to tmpdir instead of cwd during unittests"""
    with patch(
        "suppy.utils.metrics.get_default_filename",
        new=lambda: tmp_path,
    ):
        yield
