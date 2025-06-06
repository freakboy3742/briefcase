import subprocess
from datetime import datetime
from unittest.mock import MagicMock, PropertyMock

import pytest

from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize("is_color_enabled", [True, False])
def test_logcat_tail(mock_tools, adb, is_color_enabled, monkeypatch):
    """Invoking `logcat_tail()` calls `run()` with the appropriate parameters."""
    # Mock whether color is enabled for the console
    monkeypatch.setattr(
        type(mock_tools.console),
        "is_color_enabled",
        PropertyMock(return_value=is_color_enabled),
    )

    # Invoke logcat_tail with a specific timestamp
    adb.logcat_tail(since=datetime(2022, 11, 10, 9, 8, 7))

    # Validate call parameters.
    mock_tools.subprocess.run.assert_called_once_with(
        [
            mock_tools.android_sdk.adb_path,
            "-s",
            "exampleDevice",
            "logcat",
            "--format=tag",
            "-t",
            "11-10 09:08:07.000000",
            "-s",
            "MainActivity:*",
            "stdio:*",
            "python.stdout:*",
            "AndroidRuntime:*",
        ]
        + (["--format=color"] if is_color_enabled else []),
        env=mock_tools.android_sdk.env,
        check=True,
        encoding="UTF-8",
    )


def test_adb_failure(mock_tools, adb):
    """If adb logcat fails, the error is caught."""
    # Mock out the run command on an adb instance
    mock_tools.subprocess.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="adb logcat")
    )

    with pytest.raises(BriefcaseCommandError):
        adb.logcat_tail(since=datetime(2022, 11, 10, 9, 8, 7))
