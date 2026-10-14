"""Checkpoint 5 - Programacao Dinamica em Strings.

Execute este arquivo na mesma pasta de transcricoes_atividade.csv e catalogo.csv.
Ele gera todas as saidas exigidas pelo checkpoint, sem bibliotecas de similaridade.

Fluxo: ler corpus -> limpar -> frequencia -> catalogo -> triagem exata
       -> DP (melhor candidato) -> regra de aceitacao (L1 e L2) -> saidas.
"""

from collections import Counter
from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_TRANSCRICOES = BASE_DIR / "transcricoes_atividade.csv"
ARQUIVO_CATALOGO = BASE_DIR / "catalogo.csv"
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")
MINIMO_APROXIMACAO = 4
LIMITES = (1, 2)


# ---------------------------------------------------------------------------
# Etapa 2 - limpeza e comparacao exata
# ---------------------------------------------------------------------------

def limpar_texto(texto):
    """Normaliza texto para comparacao: minusculas, sem pontuacao e espacos unicos.

    Acentos sao preservados porque fazem parte da forma canonica correta
    (ex.: "solucao" e "solução" nao devem ser tratados como iguais).
    """
    texto = "" if pd.isna(texto) else str(texto)
    texto = texto.lower().strip()
    texto = re.sub(r"[^a-zà-öø-ÿ]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def comparar_exato(a, b):
    """Compara duas entradas depois da mesma limpeza controlada."""
    return limpar_texto(a) == limpar_texto(b)


def tokenizar(texto):
    """Extrai as palavras ja normalizadas de um texto."""
    return [limpar_texto(p) for p in TOKEN_RE.findall(str(texto))]


# ---------------------------------------------------------------------------
# Etapa 6 - distancia de edicao por Programacao Dinamica
# ---------------------------------------------------------------------------

def matriz_distancia(a, b):
    """Constroi a matriz bottom-up da distancia de edicao de Levenshtein.

    dp[i][j] = menor custo para transformar os i primeiros caracteres de a
    nos j primeiros caracteres de b.
    """
    a = limpar_texto(a)
    b = limpar_texto(b)
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]

    for i in range(len(a) + 1):
        dp[i][0] = i
    for j in range(len(b) + 1):
        dp[0][j] = j

    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                remover = dp[i - 1][j]
                inserir = dp[i][j - 1]
                substituir = dp[i - 1][j - 1]
                dp[i][j] = 1 + min(remover, inserir, substituir)
    return dp


def distancia_edicao(a, b):
    """Retorna a distancia final da matriz de programacao dinamica."""
    return matriz_distancia(a, b)[-1][-1]


# ---------------------------------------------------------------------------
# Etapas 1, 3 e 4 - corpus, frequencia e catalogo
# ---------------------------------------------------------------------------

def carregar_corpus():
    """Le e valida o corpus, preservando id + meeting_id + locutor + texto."""
    df = pd.read_csv(ARQUIVO_TRANSCRICOES)
    colunas_esperadas = ["id", "meeting_id", "locutor", "texto"]
    faltando = [c for c in colunas_esperadas if c not in df.columns]
    if faltando:
        raise ValueError(f"CSV de transcricoes sem as colunas: {faltando}")
    if len(df) != 420:
        raise ValueError(f"Esperados 420 registros; encontrados {len(df)}.")
    return df[colunas_esperadas].copy()


def carregar_catalogo():
    """Le e valida o catalogo canonico (80 a 150 termos, sem duplicatas)."""
    catalogo_df = pd.read_csv(ARQUIVO_CATALOGO)
    if "termo" not in catalogo_df.columns:
        raise ValueError("catalogo.csv precisa ter a coluna termo.")
    catalogo = [limpar_texto(t) for t in catalogo_df["termo"].dropna()]
    catalogo = [t for t in catalogo if t]
    if not 80 <= len(catalogo) <= 150:
        raise ValueError("O catalogo deve ter entre 80 e 150 termos.")
    if len(set(catalogo)) != len(catalogo):
        raise ValueError("O catalogo contem termos duplicados.")
    return catalogo


def gerar_frequencia(df):
    """Conta todas as palavras do corpus (inclusive as curtas) sem filtro.

    O filtro de tamanho minimo so e aplicado depois, na triagem da DP; a
    frequencia mostra o vocabulario completo usado para montar o catalogo.
    """
    contador = Counter()
    for texto in df["texto"]:
        contador.update(tokenizar(texto))
    frequencia = pd.DataFrame(contador.most_common(), columns=["palavra", "frequencia"])
    frequencia["tamanho"] = frequencia["palavra"].str.len()
    return frequencia


# ---------------------------------------------------------------------------
# Etapa 5 - triagem: EXATO x PENDENTE_DP
# ---------------------------------------------------------------------------

def classificar_termos(palavras, catalogo):
    """Separa EXATO de PENDENTE_DP antes de qualquer comparacao aproximada.

    Palavras com menos de MINIMO_APROXIMACAO letras recebem CURTO: nao vao
    para a DP (artigos e preposicoes gerariam falsos positivos) e depois
    ficam como MANTIDO.
    """
    catalogo_set = set(catalogo)
    triagem = {}
    for palavra in palavras:
        normalizada = limpar_texto(palavra)
        if normalizada in catalogo_set:
            triagem[normalizada] = "EXATO"
        elif len(normalizada) < MINIMO_APROXIMACAO:
            triagem[normalizada] = "CURTO"
        else:
            triagem[normalizada] = "PENDENTE_DP"
    return triagem


# ---------------------------------------------------------------------------
# Etapa 6 e 7 - melhor candidato e regra de aceitacao
# ---------------------------------------------------------------------------

def buscar_melhor_candidato(palavra, catalogo):
    """Calcula a DP contra todo o catalogo e devolve (menor distancia, empatados)."""
    distancias = [(termo, distancia_edicao(palavra, termo)) for termo in catalogo]
    menor = min(distancia for _, distancia in distancias)
    melhores = [termo for termo, distancia in distancias if distancia == menor]
    return menor, melhores


def aplicar_regra(original, status_triagem, busca, limite):
    """Aplica EXATO / CORRIGIDO / AMBIGUO / MANTIDO.

    Retorno: (texto_saida, distancia, status, candidatos).
    """
    normalizada = limpar_texto(original)
    if status_triagem == "EXATO":
        return normalizada, 0, "EXATO", [normalizada]
    if status_triagem == "CURTO":
        return original, None, "MANTIDO", []

    menor, melhores = busca
    if menor > limite:
        return original, menor, "MANTIDO", melhores
    if len(melhores) > 1:
        return original, menor, "AMBIGUO", melhores
    return melhores[0], menor, "CORRIGIDO", melhores


def classificar_termo(palavra, catalogo, limite):
    """Atalho para uma palavra isolada: triagem + DP + regra de aceitacao."""
    normalizada = limpar_texto(palavra)
    status = classificar_termos([normalizada], catalogo)[normalizada]
    busca = buscar_melhor_candidato(normalizada, catalogo) if status == "PENDENTE_DP" else None
    return aplicar_regra(palavra, status, busca, limite)


# ---------------------------------------------------------------------------
# Pipeline sobre o corpus
# ---------------------------------------------------------------------------

def processar_corpus(df, triagem, buscas, limite):
    """Aplica a regra a cada palavra dos 420 registros mantendo rastreabilidade.

    Recebe a triagem e as buscas da DP ja calculadas (uma vez por palavra
    distinta), de modo que cada limite apenas reaplica a regra de aceitacao.
    """
    textos_tratados, decisoes_registro, logs = [], [], []
    contagens = {s: [] for s in ("EXATO", "CORRIGIDO", "AMBIGUO", "MANTIDO")}
    totais = Counter()

    for linha in df.itertuples(index=False):
        contagem = Counter()
        decisoes = []

        def substituir(match):
            original = match.group(0)
            normalizada = limpar_texto(original)
            saida, distancia, status, candidatos = aplicar_regra(
                original, triagem[normalizada], buscas.get(normalizada), limite
            )
            contagem[status] += 1
            totais[f"triagem_{triagem[normalizada]}"] += 1
            if status in ("CORRIGIDO", "AMBIGUO"):
                decisoes.append(f"{original}->{saida}:{status}" if status == "CORRIGIDO"
                                else f"{original}:{status}")
                logs.append({
                    "id": linha.id,
                    "meeting_id": linha.meeting_id,
                    "locutor": linha.locutor,
                    "original": original,
                    "candidato": saida if status == "CORRIGIDO" else "",
                    "candidatos_empatados": "|".join(candidatos) if status == "AMBIGUO" else "",
                    "distancia": distancia,
                    "limite": limite,
                    "status": status,
                })
            return saida

        textos_tratados.append(TOKEN_RE.sub(substituir, str(linha.texto)))
        decisoes_registro.append("; ".join(decisoes))
        totais.update(contagem)
        for status in contagens:
            contagens[status].append(contagem[status])

    resultado = df.rename(columns={"texto": "texto_original"})
    resultado["texto_limpo"] = resultado["texto_original"].map(limpar_texto)
    resultado["texto_tratado"] = textos_tratados
    resultado["status_registro"] = [
        "AMBIGUO" if a else "CORRIGIDO" if c else "SEM_ALTERACAO"
        for a, c in zip(contagens["AMBIGUO"], contagens["CORRIGIDO"])
    ]
    resultado["decisoes"] = decisoes_registro
    for status, valores in contagens.items():
        resultado[f"qtd_{status.lower()}"] = valores
    totais["termos_analisados"] = sum(totais[s] for s in contagens)
    totais["registros_alterados"] = sum(1 for c in contagens["CORRIGIDO"] if c)
    return resultado, pd.DataFrame(logs), totais


def percentual(parte, todo):
    """Percentual arredondado em 2 casas (0 quando o total e zero)."""
    return round(100 * parte / todo, 2) if todo else 0.0


def resumo_estatistico(totais, limite, tamanho_catalogo, pendentes_dp):
    """Metricas de um limite. Contagens sao int; percentuais, float com 2 casas."""
    analisados = totais["termos_analisados"]
    pendentes = totais["triagem_PENDENTE_DP"]
    return {
        "limite_distancia": limite,
        "termos_no_catalogo": tamanho_catalogo,
        "palavras_distintas_pendentes_dp": pendentes_dp,
        "termos_analisados": analisados,
        "ocorrencias_pendentes_dp": pendentes,
        "ocorrencias_curtas_sem_dp": totais["triagem_CURTO"],
        "EXATO": totais["EXATO"],
        "CORRIGIDO": totais["CORRIGIDO"],
        "AMBIGUO": totais["AMBIGUO"],
        "MANTIDO": totais["MANTIDO"],
        "MANTIDO_apos_dp": pendentes - totais["CORRIGIDO"] - totais["AMBIGUO"],
        "percentual_pendentes_dp": percentual(pendentes, analisados),
        "percentual_correcoes_automaticas": percentual(totais["CORRIGIDO"], analisados),
        "percentual_corrigido_sobre_pendentes_dp": percentual(totais["CORRIGIDO"], pendentes),
        "percentual_ambiguo_sobre_pendentes_dp": percentual(totais["AMBIGUO"], pendentes),
        "percentual_mantido_sobre_pendentes_dp": percentual(
            pendentes - totais["CORRIGIDO"] - totais["AMBIGUO"], pendentes
        ),
        "registros_alterados": totais["registros_alterados"],
    }


def tabela_comparativa(resumos):
    """Monta metrica x limite sem converter inteiros em float (evita 133.0)."""
    l1, l2 = resumos
    linhas = []
    for metrica in l1:
        if metrica == "limite_distancia":
            continue
        diferenca = l2[metrica] - l1[metrica]
        if isinstance(diferenca, float):
            diferenca = round(diferenca, 2)
        linhas.append({
            "metrica": metrica,
            f"limite_{l1['limite_distancia']}": l1[metrica],
            f"limite_{l2['limite_distancia']}": l2[metrica],
            "diferenca_L2_menos_L1": diferenca,
        })
    return pd.DataFrame(linhas, dtype=object)


# ---------------------------------------------------------------------------
# Testes minimos (secao 9 do enunciado)
# ---------------------------------------------------------------------------

def executar_testes_minimos():
    """Testes exigidos no enunciado antes do processamento integral."""
    assert limpar_texto(" TOTOS ") == "totos"
    assert comparar_exato("TOTVS", " totvs ") is True
    assert comparar_exato("Totos", "totvs") is False
    assert distancia_edicao("protheu", "protheus") == 1
    assert distancia_edicao("totvss", "totvs") == 1

    matriz = matriz_distancia("totos", "totvs")
    assert len(matriz) == 6 and all(len(linha) == 6 for linha in matriz)
    assert matriz[0] == [0, 1, 2, 3, 4, 5]
    assert [linha[0] for linha in matriz] == [0, 1, 2, 3, 4, 5]
    assert matriz[-1][-1] == 1

    # Lista curta da atividade anterior, usada apenas como teste de comportamento.
    catalogo_teste = ["totvs", "protheus", "fluig", "casa", "cama"]
    triagem = classificar_termos(["TOTVS", "Totos", "de"], catalogo_teste)
    assert triagem == {"totvs": "EXATO", "totos": "PENDENTE_DP", "de": "CURTO"}
    assert classificar_termo("Totos", catalogo_teste, 1)[:3] == ("totvs", 1, "CORRIGIDO")
    assert classificar_termo("protheu", catalogo_teste, 1)[2] == "CORRIGIDO"
    assert classificar_termo("xyzwk", catalogo_teste, 1)[2] == "MANTIDO"

    saida, distancia, status, candidatos = classificar_termo("cana", catalogo_teste, 1)
    assert status == "AMBIGUO" and saida == "cana" and distancia == 1
    assert sorted(candidatos) == ["cama", "casa"]
    print("Todos os testes minimos passaram.")


# ---------------------------------------------------------------------------
# Execucao completa
# ---------------------------------------------------------------------------

def main():
    # == Testes minimos ==
    executar_testes_minimos()

    # == Etapa 1: ler o corpus ==
    df = carregar_corpus()
    print(f"[1] Registros: {len(df)} | Reunioes: {df['meeting_id'].nunique()}"
          f" | Locutores: {df['locutor'].nunique()}")

    # == Etapa 2: limpar o texto ==
    alterados = df[df["texto"] != df["texto"].map(limpar_texto)]
    print(f"[2] Limpeza alterou {len(alterados)} registros. Exemplos (antes -> depois):")
    for texto in alterados["texto"].head(5):
        print(f"    {texto!r} -> {limpar_texto(texto)!r}")
    print("    A limpeza so normaliza maiusculas, pontuacao e espacos; as palavras"
          " com erro sao corrigidas pela DP (pares palavra a palavra na etapa 7).")

    # == Etapa 3: gerar a frequencia ==
    frequencia_df = gerar_frequencia(df)
    frequencia_df.to_csv(BASE_DIR / "frequencia_palavras.csv", index=False, encoding="utf-8-sig")
    curtas = frequencia_df[frequencia_df["tamanho"] < MINIMO_APROXIMACAO]
    print(f"[3] frequencia_palavras.csv: {len(frequencia_df)} palavras distintas"
          f" ({frequencia_df['frequencia'].sum()} ocorrencias), das quais"
          f" {len(curtas)} tem menos de {MINIMO_APROXIMACAO} letras"
          f" ({curtas['frequencia'].sum()} ocorrencias)")
    print(frequencia_df.head(10).to_string(index=False))

    # == Etapa 4: carregar o catalogo ==
    catalogo = carregar_catalogo()
    no_corpus = set(frequencia_df["palavra"])
    presentes = sum(1 for t in catalogo if t in no_corpus)
    print(f"[4] Catalogo: {len(catalogo)} termos ({presentes} aparecem literalmente no corpus)")

    # == Etapa 5: triagem exata (EXATO x PENDENTE_DP) ==
    palavras = [p for texto in df["texto"] for p in tokenizar(texto)]
    triagem = classificar_termos(set(palavras), catalogo)
    ocorrencias = Counter(triagem[p] for p in palavras)
    pendentes = sorted(p for p, s in triagem.items() if s == "PENDENTE_DP")
    print(f"[5] Triagem sobre {len(palavras)} ocorrencias:"
          f" EXATO={ocorrencias['EXATO']} | PENDENTE_DP={ocorrencias['PENDENTE_DP']}"
          f" ({percentual(ocorrencias['PENDENTE_DP'], len(palavras))}%)"
          f" | CURTO (sem DP)={ocorrencias['CURTO']}")
    print(f"    Palavras distintas enviadas para a DP: {len(pendentes)}")

    # == Etapa 6: executar a DP ==
    # Uma vez por palavra distinta; o resultado e reutilizado nos dois limites.
    buscas = {p: buscar_melhor_candidato(p, catalogo) for p in pendentes}
    print(f"[6] DP executada: {len(pendentes)} x {len(catalogo)}"
          f" = {len(pendentes) * len(catalogo)} comparacoes")

    # == Etapa 7: aplicar a regra de aceitacao (L1 e L2) ==
    resultados, resumos, logs = {}, [], []
    for limite in LIMITES:
        resultado, log, totais = processar_corpus(df, triagem, buscas, limite)
        resultados[limite] = resultado
        resumos.append(resumo_estatistico(totais, limite, len(catalogo), len(pendentes)))
        logs.append(log)

        print(f"[7] LIMITE_DISTANCIA = {limite}: " + " | ".join(
            f"{s}={totais[s]}" for s in ("EXATO", "CORRIGIDO", "AMBIGUO", "MANTIDO")))
        pares = (log[log["status"] == "CORRIGIDO"]
                 .groupby(["original", "candidato", "distancia"]).size()
                 .sort_values(ascending=False).head(8))
        print("    Palavras corrigidas (antes -> depois, ocorrencias):")
        for (original, candidato, distancia), qtd in pares.items():
            print(f"    {original} -> {candidato} (distancia {distancia}, {qtd}x)")

    print("\nRegistros antes -> depois (L1, texto original -> texto tratado):")
    exemplos = resultados[1][resultados[1]["status_registro"] == "CORRIGIDO"].head(5)
    for linha in exemplos.itertuples():
        print(f"    id {linha.id}: {linha.decisoes}")
        print(f"      antes : {linha.texto_original}")
        print(f"      depois: {linha.texto_tratado}")

    # == Etapa 8: gerar as saidas ==
    for limite, resultado in resultados.items():
        resultado.to_csv(BASE_DIR / f"transcricoes_processadas_L{limite}.csv",
                         index=False, encoding="utf-8-sig")
    pd.concat(logs, ignore_index=True).to_csv(
        BASE_DIR / "correcoes_realizadas.csv", index=False, encoding="utf-8-sig"
    )
    estatisticas = tabela_comparativa(resumos)
    estatisticas.to_csv(BASE_DIR / "estatisticas_resumo.csv", index=False, encoding="utf-8-sig")
    print("[8] Estatisticas comparativas:")
    print(estatisticas.to_string(index=False))

    # Correcoes que so aparecem no limite 2 (candidatas a falso positivo)
    l1, l2 = logs
    chave = ["id", "original", "status"]
    novas = l2.merge(l1[chave], on=chave, how="left", indicator=True)
    novas = novas[novas["_merge"] == "left_only"]
    print("\nDecisoes que so ocorrem no limite 2:")
    print(novas.groupby(["original", "candidato", "candidatos_empatados", "status"])
          .size().sort_values(ascending=False).to_string())


if __name__ == "__main__":
    main()
