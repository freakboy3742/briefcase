from unittest import mock

import pytest

from briefcase.commands.run import LogFilter
from briefcase.exceptions import BriefcaseCommandError, BriefcaseTestSuiteFailure


def test_run_app(run_command, first_app):
    """An app can have its logs streamed."""
    popen = mock.MagicMock()
    popen.poll = mock.MagicMock(return_value=0)
    clean_filter = mock.MagicMock()

    # Invoke the stop func as part of streaming. This is to satisfy coverage.
    def mock_stream(label, popen_process, stop_func, filter_func):
        stop_func()

    run_command.tools.subprocess.stream_output = mock.MagicMock(side_effect=mock_stream)

    # Stream the app logs
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        clean_filter=clean_filter,
        clean_output=False,
    )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=mock.ANY,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.exit_filter.regex.pattern == LogFilter.DEFAULT_EXIT_REGEX


def test_run_app_custom_stop_func(run_command, first_app):
    """An app with a custom stop function can have its logs streamed."""
    popen = mock.MagicMock()
    popen.poll = mock.MagicMock(return_value=0)
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Stream the app logs
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        clean_filter=clean_filter,
        clean_output=False,
        stop_func=stop_func,
    )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.exit_filter.regex.pattern == LogFilter.DEFAULT_EXIT_REGEX


def test_test_mode_success(run_command, first_app):
    """An app can be streamed in test mode."""
    first_app.test_mode = True

    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Mock effect of streaming the app resulting in a test suite success
    def mock_stream_output(label, popen_process, filter_func, **kwargs):
        filter_func.returncode = 0

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    # Stream the app logs
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        clean_filter=clean_filter,
        clean_output=False,
        stop_func=stop_func,
    )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.exit_filter.regex.pattern == LogFilter.DEFAULT_EXIT_REGEX


def test_test_mode_failure(run_command, first_app, capsys):
    """An app can be streamed in test mode, resulting in test failure."""
    first_app.test_mode = True

    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Mock effect of streaming the app resulting in a test suite success
    def mock_stream_output(label, popen_process, filter_func, **kwargs):
        filter_func.returncode = 42

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    # Streaming the app logs causes a test suite failure
    with pytest.raises(BriefcaseTestSuiteFailure):
        run_command._stream_app_logs(
            first_app,
            popen=popen,
            clean_filter=clean_filter,
            clean_output=False,
            stop_func=stop_func,
        )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.exit_filter.regex.pattern == LogFilter.DEFAULT_EXIT_REGEX

    # An error was written with the test suite failure code
    assert "Test suite failed! (return code 42)" in capsys.readouterr().out


def test_test_mode_no_result(run_command, first_app):
    """An app can be streamed in test mode, but with no test result being found."""
    first_app.test_mode = True

    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Mock effect of streaming the app but not finding a test result.
    def mock_stream_output(label, popen_process, filter_func, **kwargs):
        filter_func.success = None

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    # Stream the app logs raises an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Test suite didn't report a result.",
    ):
        run_command._stream_app_logs(
            first_app,
            popen=popen,
            clean_filter=clean_filter,
            clean_output=False,
            stop_func=stop_func,
        )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.exit_filter.regex.pattern == LogFilter.DEFAULT_EXIT_REGEX


def test_test_mode_custom_filters(run_command, first_app):
    """An app can define custom success/failure regexes."""
    first_app.test_mode = True

    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Mock effect of streaming the app resulting in a test suite success
    def mock_stream_output(label, popen_process, filter_func, **kwargs):
        filter_func.returncode = 0

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    first_app.exit_regex = "THIS IS WHAT SUCCESS LOOKS LIKE"

    # Stream the app logs
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        clean_filter=clean_filter,
        clean_output=False,
        stop_func=stop_func,
    )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.exit_filter.regex.pattern == "THIS IS WHAT SUCCESS LOOKS LIKE"


def test_run_app_failure(run_command, first_app):
    """If an app exits with a bad exit code, that is raised as an error."""
    popen = mock.MagicMock()
    popen.poll = mock.MagicMock(return_value=42)
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Streaming the app logs raises an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Problem running app first \(return code 42\)\.",
    ):
        run_command._stream_app_logs(
            first_app,
            popen=popen,
            clean_filter=clean_filter,
            clean_output=False,
            stop_func=stop_func,
        )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.exit_filter.regex.pattern == LogFilter.DEFAULT_EXIT_REGEX


def test_run_app_reported_success_overrides_process_exit_status(
    run_command,
    first_app,
):
    """If the app reports a successful exit, that overrides a non-zero process exit
    status.

    This is the scenario in beeware/briefcase#2969: the app reports success via the exit
    sentinel, but is forcibly terminated by Briefcase before it manages to exit on its
    own (e.g. because GUI toolkit teardown is slow). On Windows, that forced termination
    itself produces an exit status of 1, which must not be mistaken for the app failing.
    """
    popen = mock.MagicMock()
    # The process' own exit status disagrees with what the app reported; this
    # simulates Briefcase's own forced termination producing a status of 1.
    popen.poll = mock.MagicMock(return_value=1)
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # The app reported a successful exit via the sentinel.
    def mock_stream_output(label, popen_process, filter_func, **kwargs):
        filter_func.returncode = 0

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    # No error is raised; the app's own report of success takes priority.
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        clean_filter=clean_filter,
        clean_output=False,
        stop_func=stop_func,
    )


def test_run_app_reported_failure_overrides_process_exit_status(
    run_command,
    first_app,
):
    """If the app reports a failure exit code, that is used even if the process exit
    status disagrees."""
    popen = mock.MagicMock()
    # The process happened to exit cleanly, but the app reported failure.
    popen.poll = mock.MagicMock(return_value=0)
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    def mock_stream_output(label, popen_process, filter_func, **kwargs):
        filter_func.returncode = 42

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Problem running app first \(return code 42\)\.",
    ):
        run_command._stream_app_logs(
            first_app,
            popen=popen,
            clean_filter=clean_filter,
            clean_output=False,
            stop_func=stop_func,
        )


def test_run_app_no_sentinel_falls_back_to_process_exit_status(
    run_command,
    first_app,
):
    """If the app never reports an exit code, the process' exit status is used, as
    before."""
    popen = mock.MagicMock()
    popen.poll = mock.MagicMock(return_value=7)
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # The app never printed the exit sentinel; filter_func.returncode stays at its
    # default value of None.

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Problem running app first \(return code 7\)\.",
    ):
        run_command._stream_app_logs(
            first_app,
            popen=popen,
            clean_filter=clean_filter,
            clean_output=False,
            stop_func=stop_func,
        )


def test_run_app_log_stream_stream_failure(run_command, first_app):
    """If a log stream returns an error code, the log filter requires it is ignored."""
    popen = mock.MagicMock()
    popen.returncode = 1
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # The log stream raises an error code, but that doesn't raise an error
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        clean_filter=clean_filter,
        clean_output=False,
        stop_func=stop_func,
        log_stream=True,
    )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="log stream",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.exit_filter.regex.pattern == LogFilter.DEFAULT_EXIT_REGEX


def test_run_app_log_stream_success(run_command, first_app):
    """If a log streamed app returns successfully, no problem is surfaced."""
    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Mock effect of streaming the app and returning successfully
    def mock_stream_output(label, popen_process, filter_func, **kwargs):
        filter_func.returncode = 0

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    # Stream the app logs returns success
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        clean_filter=clean_filter,
        clean_output=False,
        stop_func=stop_func,
        log_stream=True,
    )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="log stream",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.exit_filter.regex.pattern == LogFilter.DEFAULT_EXIT_REGEX


def test_run_app_log_stream_failure(run_command, first_app):
    """If a log streamed app exits with a failure code, the error is surfaced."""
    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Mock effect of streaming the app resulting in a test suite success
    def mock_stream_output(label, popen_process, filter_func, **kwargs):
        filter_func.returncode = 42

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    # Streaming the app logs causes a test suite failure
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Problem running app first \(log stream return code 42\)\.",
    ):
        run_command._stream_app_logs(
            first_app,
            popen=popen,
            clean_filter=clean_filter,
            clean_output=False,
            stop_func=stop_func,
            log_stream=True,
        )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="log stream",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.exit_filter.regex.pattern == LogFilter.DEFAULT_EXIT_REGEX


def test_run_app_log_stream_no_result(run_command, first_app):
    """If a log streamed app returns no result, no problem is surfaced."""
    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Mock effect of streaming the app but not finding a test result.
    def mock_stream_output(label, popen_process, filter_func, **kwargs):
        filter_func.returncode = None

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    # Streaming the app logs doesn't raise an error
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        clean_filter=clean_filter,
        clean_output=False,
        stop_func=stop_func,
        log_stream=True,
    )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="log stream",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.exit_filter.regex.pattern == LogFilter.DEFAULT_EXIT_REGEX


def test_run_app_ctrl_c(run_command, first_app):
    """An app can have its logs streamed, but be interrupted."""
    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Mock a CTRL-C
    run_command.tools.subprocess.stream_output.side_effect = KeyboardInterrupt

    # Stream the app logs
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        clean_filter=clean_filter,
        clean_output=False,
        stop_func=stop_func,
    )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.exit_filter.regex.pattern == LogFilter.DEFAULT_EXIT_REGEX
