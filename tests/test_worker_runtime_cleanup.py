import logging

from tests.helpers.worker_runtime import isolated_runtime


def test_runtime_cleanup_closes_owned_logs_without_closing_other_logs(tmp_path):
    logger = logging.getLogger('qa-runtime-cleanup')
    unrelated = logging.FileHandler(tmp_path / 'unrelated.log', encoding='utf-8')
    logger.addHandler(unrelated)
    try:
        with isolated_runtime('cleanup-check') as root:
            owned = logging.FileHandler(root / 'data' / 'owned.log', encoding='utf-8')
            logger.addHandler(owned)
            owned_stream = owned.stream
            owned_stream.write('QA log\n')
        assert owned_stream.closed
        assert owned not in logger.handlers
        assert not root.exists(), 'temporary runtime still locked after cleanup'
        assert unrelated.stream is not None and not unrelated.stream.closed
    finally:
        logger.removeHandler(unrelated)
        unrelated.close()
