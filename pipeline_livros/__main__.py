"""Entrada da linha de comando do pipeline."""

import argparse
import logging
from pathlib import Path

from .pipeline import executar


def _mostrar_resumo(resultado):
    if resultado.etapa_falha:
        estado = f"falha de {resultado.etapa_falha}"
    elif resultado.rejeitados:
        estado = "conclusão com erros de itens"
    else:
        estado = "sucesso"
    print(f"Resultado: {estado}")
    print(f"SQLite: {resultado.banco} ({resultado.estado_banco})")
    print(f"CSV: {resultado.csv} ({resultado.estado_csv})")
    print(f"Páginas percorridas: {resultado.paginas}")
    print(f"Ocorrências detectadas: {resultado.detectados}")
    print(f"Itens rejeitados: {resultado.rejeitados}")
    print(f"Duplicatas na coleta: {resultado.duplicatas}")
    print(f"Registros inseridos: {resultado.carga.inseridos}")
    print(f"Registros atualizados: {resultado.carga.atualizados}")
    print(f"Registros mantidos sem mudança: {resultado.carga.mantidos}")
    print(f"Linhas exportadas: {resultado.linhas_exportadas}")
    print(f"Total de erros: {resultado.total_erros}")
    print(f"Tentativas de conexão malsucedidas: {resultado.tentativas_malsucedidas}")
    print(f"Falhas recuperadas: {resultado.falhas_recuperadas}")
    print(f"Erros definitivos: {resultado.erros_definitivos}")


def main(argumentos=None):
    parser = argparse.ArgumentParser(
        prog="python -m pipeline_livros",
        description="Coleta e trata o catálogo Books to Scrape.",
        add_help=False,
    )
    opcoes_cli = parser.add_argument_group("opções")
    opcoes_cli.add_argument("-h", "--help", action="help", help="mostra esta ajuda e encerra")
    opcoes_cli.add_argument(
        "--diretorio-saida", type=Path, default=Path("saida"), metavar="DIRETÓRIO",
        help="diretório de saída (padrão: saida/)",
    )
    opcoes = parser.parse_args(argumentos)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    resultado = executar(opcoes.diretorio_saida)
    _mostrar_resumo(resultado)
    return resultado.codigo


if __name__ == "__main__":
    raise SystemExit(main())
