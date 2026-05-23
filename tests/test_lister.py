from ordo.config import parse
from ordo.lister import Lister
import io, sys

def test_list_basic(tmp_config, capsys):
    config = parse(tmp_config())
    Lister.list(config, verbose=False)
    out = capsys.readouterr().out
    assert "[dev]" in out
    assert "start" in out
    assert "reset" in out
    assert "[test]" in out

def test_list_shows_descriptions(tmp_config, capsys):
    config = parse(tmp_config())
    Lister.list(config, verbose=False)
    out = capsys.readouterr().out
    assert "Start the server" in out

def test_list_verbose_shows_run_string(tmp_config, capsys):
    config = parse(tmp_config())
    Lister.list(config, verbose=True)
    out = capsys.readouterr().out
    assert "uvicorn app.main:app --reload" in out

def test_list_no_verbose_hides_run_string(tmp_config, capsys):
    config = parse(tmp_config())
    Lister.list(config, verbose=False)
    out = capsys.readouterr().out
    assert "uvicorn" not in out