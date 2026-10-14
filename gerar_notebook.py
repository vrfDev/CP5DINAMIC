"""Gera a versao .ipynb a partir do script principal do checkpoint.

O notebook e dividido por etapa: uma celula por bloco de funcoes do script
(secoes "# ---- Etapa ...") e uma celula por etapa do main (marcadores
"# == ... =="). Assim o codigo continua com uma unica fonte (o .py).
"""

import json
import re
import textwrap
from pathlib import Path


PASTA = Path(__file__).resolve().parent
SCRIPT = "CP5_Dynamic_Programming_Vitor_Ramos.py"
NOTEBOOK = "CP5_Dynamic_Programming_Vitor_Ramos.ipynb"

SECAO_RE = re.compile(r"^# -{20,}\n# (.+)\n# -{20,}\n", re.M)
ETAPA_RE = re.compile(r"^    # == (.+) ==\n", re.M)

DESCRICOES = {
    "Testes minimos": "Executados antes do corpus (secao 9 do enunciado).",
    "Etapa 1": "Leitura e validacao das 420 transcricoes.",
    "Etapa 2": "Limpeza controlada: minusculas, pontuacao e espacos. "
               "As palavras com erro so sao corrigidas pela DP (etapa 7).",
    "Etapa 3": "Frequencia de todas as palavras do corpus, sem filtro de tamanho.",
    "Etapa 4": "Catalogo canonico (80 a 150 termos).",
    "Etapa 5": "Triagem: EXATO, PENDENTE_DP ou CURTO (menos de 4 letras, sem DP).",
    "Etapa 6": "Distancia de edicao por DP, uma vez por palavra distinta pendente.",
    "Etapa 7": "Regra de aceitacao com LIMITE_DISTANCIA 1 e 2, com os pares "
               "antes -> depois das palavras corrigidas.",
    "Etapa 8": "CSVs de saida e estatisticas comparativas.",
}


def linhas(texto):
    return texto.strip("\n").splitlines(keepends=True)


def markdown(texto):
    return {"cell_type": "markdown", "metadata": {}, "source": linhas(texto)}


def codigo(texto):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": linhas(texto)}


def descricao(titulo):
    for chave, texto in DESCRICOES.items():
        if titulo.startswith(chave):
            return texto
    return ""


fonte = (PASTA / SCRIPT).read_text(encoding="utf-8")
fonte = fonte.replace(
    "BASE_DIR = Path(__file__).resolve().parent", "BASE_DIR = Path.cwd()"
)
definicoes, corpo_main = fonte.split("def main():\n", 1)
corpo_main = corpo_main.split('\nif __name__ == "__main__":', 1)[0]

celulas = [
    markdown(
        "# Checkpoint 5 Programacao Dinamica em Strings\n\n"
        "**Vitor Ramos de Farias - RM 561958**\n\n"
        "Este notebook processa o corpus de 420 transcricoes, gera frequencia, "
        "aplica a distancia de edicao implementada com Programacao Dinamica e "
        "compara os limites 1 e 2.\n\n"
        "Deixe `transcricoes_atividade.csv` e `catalogo.csv` na mesma pasta do "
        "notebook e execute as celulas em ordem. Este arquivo e gerado a partir de "
        f"`{SCRIPT}` por `python gerar_notebook.py`."
    )
]

# Funcoes: cabecalho (imports e constantes) + uma celula por secao do script
partes = SECAO_RE.split(definicoes)
celulas += [markdown("## Imports e constantes"), codigo(partes[0])]
for titulo, bloco in zip(partes[1::2], partes[2::2]):
    if bloco.strip():
        celulas += [markdown(f"## Funcoes - {titulo}"), codigo(bloco)]

# Execucao: uma celula por etapa do main
partes = ETAPA_RE.split(corpo_main)
for titulo, bloco in zip(partes[1::2], partes[2::2]):
    texto = f"## {titulo[0].upper()}{titulo[1:]}"
    if descricao(titulo):
        texto += f"\n\n{descricao(titulo)}"
    celulas += [markdown(texto), codigo(textwrap.dedent(bloco))]

notebook = {
    "cells": celulas,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

(PASTA / NOTEBOOK).write_text(
    json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"{NOTEBOOK} gerado a partir de {SCRIPT} ({len(celulas)} celulas).")
