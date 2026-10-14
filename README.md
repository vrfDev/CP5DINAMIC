# Checkpoint 5 Dynamic Programming em Strings

**Aluno:** Vitor Ramos de Farias - **RM:** 561958
**Disciplina:** Dynamic Programming - TOTVS

## Como executar

Mantenha `transcricoes_atividade.csv` e `catalogo.csv` na mesma pasta do script e execute:

```bash
pip install pandas
python CP5_Dynamic_Programming_Vitor_Ramos.py
```

No Colab, envie os dois CSVs e abra `CP5_Dynamic_Programming_Vitor_Ramos.ipynb`. O notebook é dividido por etapa: uma célula para cada bloco de funções e uma célula para cada etapa do pipeline (testes mínimos, 1 a 8), cada uma com seu título e sua saída. Ele é gerado a partir do script por `python gerar_notebook.py`, então os dois têm sempre o mesmo código. Todos os CSVs de saída são produzidos pelo código, sem edição manual.

## Pipeline

| # | Etapa | Função | Resultado nesta base |
|---|---|---|---|
| 1 | Ler o corpus | `carregar_corpus` | 420 registros, 30 reuniões, 8 locutores |
| 2 | Limpar texto | `limpar_texto` | 47 registros alterados (maiúsculas iniciais, espaços duplos); erros de grafia são corrigidos na etapa 7 |
| 3 | Gerar frequência | `gerar_frequencia` | 507 palavras distintas (4199 ocorrências), todas as palavras, sem filtro |
| 4 | Carregar catálogo | `carregar_catalogo` | 133 termos |
| 5 | Triagem exata | `classificar_termos` | 1320 EXATO, 1307 PENDENTE_DP (31,13%), 1572 curtas (sem DP) |
| 6 | Executar DP | `buscar_melhor_candidato` | 358 palavras distintas × 133 termos = 47.614 comparações |
| 7 | Aplicar regra | `aplicar_regra` | EXATO / CORRIGIDO / AMBIGUO / MANTIDO, com os pares antes → depois |
| 8 | Gerar saídas | `main` | CSVs listados no final |

A limpeza usa `lower()` e `strip()`, troca pontuação por espaço e colapsa espaços repetidos. Os acentos são mantidos de propósito: eles fazem parte da forma canônica, e removê-los tornaria `solucao` e `solução` "iguais" antes da DP, escondendo um erro real.

### Antes → depois

A limpeza (etapa 2) só mexe em maiúsculas, pontuação e espaços:

- `'A validação do classe depende da configuração do processamebnto'` → `'a validação do classe depende da configuração do processamebnto'`
- `'...treinamento sobre  a clusterização'` (dois espaços) → `'...treinamento sobre a clusterização'`

As palavras escritas errado são corrigidas pela DP (etapa 7). Pares reais com `LIMITE_DISTANCIA = 1`:

| Antes | Depois | Distância | Operação |
|---|---|---:|---|
| `serkviço` | `serviço` | 1 | remover `k` |
| `serviçoi` | `serviço` | 1 | remover `i` |
| `ckassificação` | `classificação` | 1 | trocar `k → l` |
| `commiot` | `commit` | 1 | remover `o` |
| `peddo` | `pedido` | 1 | inserir `i` |
| `lmpeza` | `limpeza` | 1 | inserir `i` |
| `contrao` | `contrato` | 1 | inserir `t` |
| `variavel` | `variável` | 1 | trocar `a → á` |

E no registro inteiro (`texto_original` → `texto_tratado` em `transcricoes_processadas_L1.csv`):

| id | Antes | Depois |
|---|---|---|
| 10 | a validação do análise depende da configuração do **serkviço** | a validação do análise depende da configuração do **serviço** |
| 7 | o time abriu um **ckassificação** porque o firewall deixou de responder | o time abriu um **classificação** porque o firewall deixou de responder |
| 9 | a análise indicou necessidade de revisar **commiot** e recuperação | a análise indicou necessidade de revisar **commit** e recuperação |

O script imprime esses pares na etapa 7, e todos ficam em `correcoes_realizadas.csv`.

### Frequência sem filtro

`frequencia_palavras.csv` conta **todas** as palavras do corpus, inclusive as curtas: 507 palavras distintas e 4199 ocorrências, o mesmo total que a triagem analisa. A coluna `tamanho` mostra o número de letras, então dá para ver que as 16 palavras com menos de 4 letras (`o`, `a`, `de`, `e`, `do`…) somam 1572 ocorrências, 37% do corpus. O filtro de tamanho só entra depois, na triagem da DP, e não na contagem.

### Palavras curtas (status CURTO)

Palavras com menos de 4 letras não vão para a DP: recebem `CURTO` na triagem e saem como `MANTIDO`. Com distância 1 ou 2, quase toda palavra curta fica perto de algum termo do catálogo (com limite 2, por exemplo, `de` viraria `rede`, a 2 inserções), o que geraria falsos positivos em artigos e preposições.

**Limitação:** um erro de grafia em palavra curta nunca é corrigido, mesmo quando a correção seria óbvia. Isso acontece nesta base: no registro id 280 ("revisar token e **ede**"), `ede` é `rede` sem o `r` (distância 1), mas como tem 3 letras foi marcado como CURTO e mantido. O mesmo valeria para erros que encurtam termos de 4 letras do catálogo (`erro`, `fila`, `rede`). Outro efeito é que a contagem de `MANTIDO` mistura dois casos diferentes: palavras que a DP avaliou e rejeitou e palavras curtas que nem foram avaliadas. Por isso o `estatisticas_resumo.csv` separa `ocorrencias_curtas_sem_dp` (1572) de `MANTIDO_apos_dp` (989 no L1). Uma alternativa seria usar limite 0 ou 1 para palavras curtas em vez de excluí-las, ou aceitar a correção só quando a palavra curta não for uma palavra funcional conhecida.

A DP roda **uma vez por palavra distinta**, e o resultado (menor distância e candidatos) é reaproveitado nos dois limites. Só a regra de aceitação muda entre L1 e L2.

## 1. Catálogo: quantos termos e qual critério

São **133 termos** canônicos. O critério foi:

1. Partir de `frequencia_palavras.csv` (corpus completo).
2. Manter apenas substantivos do domínio (tecnologia, dados, qualidade, infraestrutura, segurança e negócio) escritos corretamente, com acentuação.
3. Excluir palavras funcionais e verbos genéricos (`precisa`, `discutiu`, `revisar`), que não são termos do domínio.
4. Não incluir nenhuma forma com erro.

O script confere o resultado: os **133 termos aparecem literalmente no corpus**, não há duplicatas e o tamanho está entre 80 e 150.

## 2. O que mudou entre LIMITE_DISTANCIA = 1 e = 2

| Métrica | Limite 1 | Limite 2 | Diferença |
|---|---:|---:|---:|
| Termos analisados | 4199 | 4199 | 0 |
| Ocorrências PENDENTE_DP | 1307 | 1307 | 0 |
| % PENDENTE_DP sobre termos analisados | 31,13% | 31,13% | 0 |
| EXATO | 1320 | 1320 | 0 |
| CORRIGIDO | 318 | 389 | +71 |
| AMBIGUO | 0 | 2 | +2 |
| MANTIDO | 2561 | 2488 | −73 |
| MANTIDO após a DP (sem contar CURTO) | 989 | 916 | −73 |
| % correções automáticas (sobre termos analisados) | 7,57% | 9,26% | +1,69 p.p. |
| % CORRIGIDO sobre PENDENTE_DP | 24,33% | 29,76% | +5,43 p.p. |
| % AMBIGUO sobre PENDENTE_DP | 0% | 0,15% | +0,15 p.p. |
| % MANTIDO sobre PENDENTE_DP | 75,67% | 70,08% | −5,59 p.p. |
| Registros alterados | 248 | 283 | +35 |

Os percentuais sobre PENDENTE_DP mostram o efeito real do limite: das palavras que a DP avaliou, o L1 corrige 24,33% e o L2 corrige 29,76%.

Das 71 correções a mais no L2:

- **61 são falsos positivos**: `revisar → revisão` (40) e `revisou → revisão` (21). São verbos corretos trocados por um substantivo.
- **10 são acertos**: palavras sem acento ou cedilha, como `solucao → solução`, `funcao → função`, `clusterizacao → clusterização` (2), `autenticacao → autenticação`.

## 3. Qual limite é mais seguro

**Limite 1.** No L2, 61 das 71 correções novas (86%) estão erradas. No L1, as correções são quase todas de um único caractere trocado, inserido ou removido, exemplos reais do corpus:

- `fatutramento → faturamento` (letra extra), `fatukamento → faturamento` (letra trocada)
- `bnco → banco`, `qualudade → qualidade`, `tabla → tabela`
- `serkviço → serviço`, `algxritmo → algoritmo`, `ckassificação → classificação`

O custo do L1 é deixar como MANTIDO as palavras sem acento (`solucao`, `funcao`). Esse erro é inofensivo para leitura, ao contrário de transformar todo `revisar` em `revisão`.

## 4. Casos em que a distância não bastou

- **`producao` (registros id 8 e id 17, L2):** empata em distância 2 com `produção` (trocar `c→ç`, `a→ã`) e `produto`. O pipeline marcou `AMBIGUO` e manteve o original. Pelo contexto ("melhorar a producao do fluxo") a resposta é `produção`, mas a DP olha só a forma da palavra, não o contexto.
- **`revisar` / `revisou`:** a menor distância é única (2, para `revisão`), então a regra aceita. A distância "decidiu", mas decidiu errado: o verbo não está no catálogo e o substantivo mais próximo venceu.

## 5. Correção automática inadequada ou arriscada

- **`tributo → atributo` (L1, registro id 160, "falha no firewal durante o tributo"):** `tributo` é uma palavra válida em português, a uma inserção de `atributo`. Aqui a correção provavelmente acerta a intenção, mas o pipeline corrigiria do mesmo jeito uma frase sobre imposto. Isso ocorre porque a regra só consulta o catálogo: qualquer palavra correta fora dele, a 1 edição de um termo, será "corrigida".
- **`revisar → revisão` (L2, 40 vezes):** explicado acima. O limite 2 permite duas edições, e isso basta para converter terminações verbais em nominais (`-ar`/`-ou` → `-ão`).

## 6. Como funciona a DP

- **Estado:** `dp[i][j]` = menor número de operações para transformar os `i` primeiros caracteres de `a` nos `j` primeiros caracteres de `b`.
- **Casos-base:** `dp[i][0] = i` (remover `i` caracteres) e `dp[0][j] = j` (inserir `j` caracteres).
- **Transição:** se `a[i-1] == b[j-1]`, `dp[i][j] = dp[i-1][j-1]`. Senão, `dp[i][j] = 1 + min(dp[i-1][j] (remover), dp[i][j-1] (inserir), dp[i-1][j-1] (substituir))`.
- **Ordem:** bottom-up, linha a linha, da esquerda para a direita, a partir das bordas inicializadas. A resposta fica em `dp[m][n]`.

## 7. Complexidade

Uma comparação entre palavras de tamanho `m` e `n` custa **O(m·n)** em tempo e memória. Para `P` palavras pendentes e um catálogo de `C` termos, o custo total é **O(P·C·m·n)**: ele cresce linearmente com o catálogo. Nesta base foram 358 × 133 = 47.614 matrizes. Dobrar o catálogo dobra esse número.

## 8. Otimização e trade-off

- **Memória:** guardar só duas linhas da matriz reduz a memória para O(n). O trade-off é perder a matriz completa, que é útil para depurar e para os testes (a verificação 6×6 do enunciado deixaria de ser possível com essa função).
- **Busca:** filtrar candidatos por diferença de tamanho (`|len(a) − len(b)| > limite` já implica distância > limite) ou parar a DP quando o mínimo de uma linha passar do limite evita a maioria das matrizes. O trade-off é que o código fica mais difícil de ler e de manter, e a distância deixa de ser exata acima do limite, o que afeta os registros de rastreabilidade.
- **Cache (já implementado):** a DP roda uma vez por palavra distinta, não por ocorrência. Isso troca um pouco de memória (um dicionário) por menos recomputação.

## Testes mínimos

Executados automaticamente antes do corpus (`executar_testes_minimos`). A lista curta da atividade anterior (`totvs`, `protheus`, `fluig`…) é usada só aqui:

- `limpar_texto(" TOTOS ") == "totos"`
- `comparar_exato("TOTVS", " totvs ")` é `True`; `comparar_exato("Totos", "totvs")` é `False`
- `distancia_edicao("protheu", "protheus") == 1` e `distancia_edicao("totvss", "totvs") == 1`
- matriz `"totos" × "totvs"` com dimensão 6×6, primeira linha e primeira coluna `[0..5]` e resultado 1
- triagem separa `EXATO`, `PENDENTE_DP` e palavra curta
- empate `cana` → {`casa`, `cama`} marca `AMBIGUO` e preserva `cana`

## Arquivos gerados

| Arquivo | Conteúdo |
|---|---|
| `frequencia_palavras.csv` | palavra, frequência e tamanho, para todas as palavras do corpus |
| `transcricoes_processadas_L1.csv` / `_L2.csv` | id, meeting_id, locutor, texto original, limpo e tratado, status do registro, decisões e contagens por status |
| `correcoes_realizadas.csv` | id, meeting_id, locutor, original, candidato (ou candidatos empatados), distância, limite e status, para L1 e L2 |
| `estatisticas_resumo.csv` | métricas dos dois limites e a diferença; contagens inteiras e percentuais com 2 casas |
