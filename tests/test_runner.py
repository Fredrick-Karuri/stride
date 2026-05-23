import sys
import pytest
from unittest.mock import patch, MagicMock
from ordo.config import parse
from ordo.runner import Runner
from ordo.errors import UnknownCommandError


def test_run_unknown_group_raises(tmp_config):
    config = parse(tmp_config())
    with pytest.raises(UnknownCommandError, match="ghost:cmd"):
        Runner.execute(config, "ghost:cmd")

def test_run_unknown_command_raises(tmp_config):
    config = parse(tmp_config())
    with pytest.raises(UnknownCommandError, match="dev:ghost"):
        Runner.execute(config, "dev:ghost")

def test_run_no_colon_raises(tmp_config):
    config = parse(tmp_config())
    with pytest.raises(UnknownCommandError):
        Runner.execute(config, "devstart")

def test_run_fuzzy_suggestion(tmp_config):
    config = parse(tmp_config())
    with pytest.raises(UnknownCommandError) as exc:
        Runner.execute(config, "dev:strat")
    assert exc.value.suggestion == "dev:start"

def test_run_no_suggestion_for_gibberish(tmp_config):
    config = parse(tmp_config())
    with pytest.raises(UnknownCommandError) as exc:
        Runner.execute(config, "zzz:qqq")
    assert exc.value.suggestion is None

def test_run_executes_command_and_returns_exit_code(tmp_config):
    config = parse(tmp_config())
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.wait = MagicMock()
    with patch("ordo.runner.subprocess.Popen", return_value=mock_proc) as mock_popen:
        code = Runner.execute(config, "dev:start")
    mock_popen.assert_called_once()
    call_kwargs = mock_popen.call_args
    assert call_kwargs[0][0] == ["sh", "-c", "uvicorn app.main:app --reload"]
    assert code == 0

def test_run_sets_cwd_to_config_dir(tmp_config, tmp_path):
    config = parse(tmp_config())
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.wait = MagicMock()
    with patch("ordo.runner.subprocess.Popen", return_value=mock_proc) as mock_popen:
        Runner.execute(config, "dev:start")
    assert mock_popen.call_args[1]["cwd"] == tmp_path

def test_run_forwards_nonzero_exit_code(tmp_config, capsys):
    config = parse(tmp_config())
    mock_proc = MagicMock()
    mock_proc.returncode = 2
    mock_proc.wait = MagicMock()
    with patch("ordo.runner.subprocess.Popen", return_value=mock_proc):
        code = Runner.execute(config, "dev:start")
    assert code == 2
    err = capsys.readouterr().err
    assert "exited with code 2" in err