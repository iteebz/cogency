from types import SimpleNamespace

from typer.testing import CliRunner

from cogency.cli.__init__ import app


def _stub_agent_stream(response: str):
    async def _gen(*args, **kwargs):
        yield {"type": "respond", "content": response, "payload": {}, "timestamp": 0}
        yield {"type": "end", "content": "", "payload": {}, "timestamp": 0}

    return _gen()


def test_cli_one_shot_runs_without_greeting(monkeypatch):
    runner = CliRunner()

    async def stub_assemble(*args, **kwargs):
        return [{"role": "system", "content": "IDENTITY"}]

    class StubAgent:
        def __init__(self, llm: str, mode: str, debug: bool):
            self.config = SimpleNamespace(
                tools=(),
                storage=SimpleNamespace(),
                history_window=None,
                profile=False,
                identity="IDENTITY",
                instructions="INSTRUCTIONS",
                llm=SimpleNamespace(websocket_model=None, http_model=llm),
            )
            self._last_question = None

        def __call__(self, question: str, user_id: str, conversation_id, chunks: bool):
            self._last_question = question
            return _stub_agent_stream("4")

    monkeypatch.setattr("cogency.cli.ask.Agent", StubAgent)
    monkeypatch.setattr("cogency.context.assemble", stub_assemble)

    result = runner.invoke(app, ["what is 2+2"])  # defaults to --llm openai

    assert result.exit_code == 0
    assert "> 4" in result.stdout
    assert "Hello" not in result.stdout
