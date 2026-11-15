# AGENTS.md

Staged learning project: an async web crawler built day by day (Python 3.14, asyncio + aiohttp). `README.md` and `docs/dayN.md` (in Russian) are the actual specs/acceptance criteria for each stage; done through day 2.

## Commands

- Run tests (from repo root): `.venv/bin/python -m pytest -q`
  - Bare `pytest` FAILS with `ModuleNotFoundError: No module named 'src'` — there is no packaging config (`pyproject.toml` absent, no `__init__.py` anywhere), so only `python -m pytest` puts the repo root on `sys.path`. Never add `__init__.py` or packaging files to "fix" this.
- Run a single test: `.venv/bin/python -m pytest test/test_AsyncCrawler.py -k name -q`
- Demo script (hits the live network — example.com, httpbin.org; slow and flaky, not for verification): `.venv/bin/python src/main.py`
- No linter, formatter, typechecker, or CI is configured.
- Deps live only in `requirements.txt`; the venv is `.venv/`.

## Testing quirks

- pytest-asyncio runs in **strict mode** (`pytest.ini`): every async test/fixture needs `@pytest.mark.asyncio`, otherwise it is skipped.
- Tests are hermetic: each spins up its own local `aiohttp.test_utils.TestServer` (routes `/ok`, `/404`, `/delay`) and must close it in `finally`. Follow that pattern; don't add tests that hit the network.
- `test_parallel_vs_sequential` asserts on wall-clock timing (`parallel_duration < sequential_duration`) — it can flake on a loaded machine.

## Code conventions

- New modules go in `src/` as loose files (not a package). Note the two import styles: tests use `from src.AsyncCrawler import ...`, but `src/main.py` uses flat `from AsyncCrawler import ...` (works only because `python src/main.py` puts `src/` first on `sys.path`). New entrypoint scripts should follow the `main.py` pattern; test imports follow the `src.` pattern. Module-to-module imports inside `src/` must use the `try: from src.X import ... / except ImportError: from X import ...` fallback (see `AsyncCrawler.py`) so both entry styles keep working.
- Fetch methods never raise on network/HTTP errors — they return a `FetchResult` with `error` set; callers check `result.is_success`. Keep that contract.
- The crawler must be used as an async context manager (`async with AsyncCrawler() as crawler:`) so the `aiohttp.ClientSession` is closed; the session is created lazily under a lock.
- All network operations must be async; concurrency via `asyncio.Semaphore(max_concurrent)`, pooling via `TCPConnector(limit=max_connections)`.
- Docs/specs (`README.md`, `docs/dayN.md`) are in Russian; code comments and log messages are mixed (e.g. `AsyncCrawler.py` logs in English, `HTMLParser.py` uses Russian docstrings) — match the style of the file you are editing.
