import pytest

from pipeline_livros.pipeline import bloquear_destino


def test_mesmo_destino_exclusivo_e_outro_independente(tmp_path):
    primeiro = tmp_path / "primeiro"
    segundo = tmp_path / "segundo"
    with bloquear_destino(primeiro):
        assert (primeiro / ".pipeline.lock").is_file()
        with pytest.raises(BlockingIOError), bloquear_destino(primeiro):
            pytest.fail("a segunda execução entrou na seção protegida")
        with bloquear_destino(segundo):
            assert (segundo / ".pipeline.lock").is_file()
    with bloquear_destino(primeiro):
        assert (primeiro / ".pipeline.lock").is_file()


def test_libera_bloqueio_em_erro(tmp_path):
    with pytest.raises(RuntimeError), bloquear_destino(tmp_path):
        raise RuntimeError("falha simulada")
    with bloquear_destino(tmp_path):
        assert (tmp_path / ".pipeline.lock").is_file()
