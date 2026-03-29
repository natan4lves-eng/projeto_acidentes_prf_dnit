# 🚦 Pipeline de Dados — Acidentes de Trânsito PRF (AWS Glue + Athena + S3)

> Pipeline de dados em **três camadas (Medallion Architecture)** para ingestão, tratamento e modelagem analítica dos dados de ocorrências de acidentes de trânsito registrados pela Polícia Rodoviária Federal (PRF) do Brasil.

---

## 📐 Visão Geral da Arquitetura

O projeto implementa a **Arquitetura Medallion** (Bronze → Silver → Gold), onde cada camada tem um nível crescente de qualidade e estrutura dos dados. Todo o processamento ocorre em **AWS Glue Jobs**, os dados são armazenados em **Amazon S3** em formato **Parquet/Iceberg**, e catalogados no **AWS Glue Data Catalog** para consulta via **Amazon Athena**.

```
Fontes CSV (S3)
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  CAMADA BRONZE  (01_glue_processa_bronze.py)            │
│  • Leitura dos CSVs brutos do S3                        │
│  • Normalização de colunas                              │
│  • Conversão de todos os campos para STRING             │
│  • Saída: Parquet no S3 + tabela no Glue Catalog        │
└─────────────────────────────────────────────────────────┘
      │  dispara automaticamente
      ▼
┌─────────────────────────────────────────────────────────┐
│  CAMADA SILVER  (02_glue_processa_silver.py)            │
│  • Leitura da tabela Bronze via Athena                  │
│  • Limpeza: remove duplicatas e linhas vazias           │
│  • Renomeação de colunas (padrão DW semântico)          │
│  • Conversão e validação de tipos de dados              │
│  • Enriquecimento: faixa etária, padronização textual   │
│  • Saída: Parquet no S3 + tabela no Glue Catalog        │
└─────────────────────────────────────────────────────────┘
      │  dispara automaticamente
      ▼
┌─────────────────────────────────────────────────────────┐
│  CAMADA GOLD  (03_glue_processa_gold.py)                │
│  • Leitura da tabela Silver via Athena                  │
│  • Criação de 6 Dimensões (Star Schema)                 │
│  • Criação de 2 Tabelas Fato                            │
│  • Geração de Surrogate Keys únicas                     │
│  • Cálculo de métricas analíticas e scores              │
│  • Saída: Apache Iceberg no S3 + tabelas no Glue Catalog│
└─────────────────────────────────────────────────────────┘
      │
      ▼
  Athena / BI Tools (Power BI, QuickSight, etc.)
```

---

## 📁 Estrutura de Arquivos

```
.
├── scripts/
│   ├── 01_glue_processa_bronze.py   # Glue Job: Ingestão bruta (Landing → Bronze)
│   ├── 02_glue_processa_silver.py   # Glue Job: Limpeza e padronização (Bronze → Silver)
│   ├── 03_glue_processa_gold.py     # Glue Job: Modelagem dimensional (Silver → Gold)
│   └── utils.py                     # Biblioteca de funções reutilizáveis
└── terraform/
    ├── main.tf                      # Recursos principais: S3, Glue Jobs, Glue Catalog
    ├── iam_role.tf                  # IAM Role e todas as políticas de permissão
    └── variables.tf                 # Variáveis de configuração do projeto
```

---

## ⚙️ Tecnologias Utilizadas

| Tecnologia | Uso |
|---|---|
| **AWS Glue** | Orquestração e execução dos jobs de ETL |
| **Amazon S3** | Armazenamento dos dados em todas as camadas |
| **Amazon Athena** | Consulta SQL sobre os dados no S3 |
| **AWS Glue Data Catalog** | Catálogo de metadados das tabelas |
| **Apache Iceberg** | Formato de tabela transacional na camada Gold (suporte a UPSERT/MERGE) |
| **Apache Parquet + Snappy** | Formato de arquivo nas camadas Bronze e Silver |
| **AWS Wrangler (awswrangler)** | SDK Python para integração entre Pandas e os serviços AWS |
| **Pandas / NumPy** | Processamento e transformação dos dados |
| **Boto3** | Interação com a API da AWS (S3, Glue) |
| **Terraform** | Provisionamento e gerenciamento da infraestrutura como código (IaC) |

---

## 🔄 Fluxo Detalhado por Camada

---

### 🥉 CAMADA BRONZE — `01_glue_processa_bronze.py`

**Objetivo:** Ingerir os dados brutos dos arquivos CSV sem qualquer transformação analítica, garantindo apenas a chegada íntegra dos dados ao data lake.

#### Parâmetros de entrada (Glue Job Arguments)

| Parâmetro | Descrição |
|---|---|
| `db_destino` | Database no Glue Catalog onde a tabela Bronze será criada |
| `tb_destino` | Nome da tabela Bronze de destino |
| `s3_path_origem` | Caminho S3 com os arquivos CSV brutos |
| `s3_path_destino` | Caminho S3 onde o Parquet Bronze será gravado |

#### O que acontece passo a passo

1. **Leitura dos CSVs do S3** — A função `carregar_csvs_para_dataframe_s3()` lista todos os arquivos `.csv` no prefixo S3 informado e os lê tentando encodings em sequência: `UTF-8 → ISO-8859-1 → CP1252`. Isso resolve o problema comum de arquivos brasileiros com codificações mistas. O nome do arquivo de origem é adicionado como coluna (`arquivo_origem`) para rastreabilidade.

2. **Normalização de colunas** — A função `normalizar_colunas()` padroniza todos os nomes de colunas: remove acentos, converte para lowercase, substitui espaços por `_`, remove caracteres especiais e corrige colunas `Unnamed` (lixo do CSV).

3. **Seleção de colunas** — Apenas as 37 colunas do schema definido (`SCHEMA_ORIGEM`) são mantidas. Colunas ausentes geram um aviso em log sem interromper o processo.

4. **Conversão de tipos** — Todos os campos são convertidos para `STRING`. Essa decisão é intencional: a camada Bronze deve refletir os dados exatamente como vieram da fonte, sem nenhuma interpretação de tipo que possa causar perda de dados.

5. **Escrita no S3 (Parquet)** — O DataFrame é gravado em formato Parquet comprimido com Snappy, registrado no Glue Catalog e disponibilizado para consulta no Athena.

6. **Disparo automático** — Ao final, o Glue Job `glue_processar_silver` é disparado automaticamente via `executar_glue_job()`.

#### Schema Bronze (37 colunas, todas STRING)

```
id, pesid, data_inversa, dia_semana, horario, uf, br, km, municipio,
causa_principal, causa_acidente, ordem_tipo_acidente, tipo_acidente,
classificacao_acidente, fase_dia, sentido_via, condicao_metereologica,
tipo_pista, tracado_via, uso_solo, id_veiculo, tipo_veiculo, marca,
tipo_envolvido, ano_fabricacao_veiculo, estado_fisico, idade, sexo,
ilesos, feridos_leves, feridos_graves, mortos, latitude, longitude,
regional, delegacia, uop
```

---

### 🥈 CAMADA SILVER — `02_glue_processa_silver.py`

**Objetivo:** Limpar, padronizar e enriquecer os dados da camada Bronze, aplicando regras de negócio e preparando um dataset analítico completo e confiável.

#### Parâmetros de entrada (Glue Job Arguments)

| Parâmetro | Descrição |
|---|---|
| `db_origem` | Database da tabela Bronze |
| `tb_origem` | Nome da tabela Bronze de origem |
| `db_destino` | Database onde a tabela Silver será criada |
| `tb_destino` | Nome da tabela Silver de destino |
| `s3_path` | Caminho S3 onde o Parquet Silver será gravado |

#### O que acontece passo a passo

1. **Leitura via Athena** — A tabela Bronze é lida diretamente do Athena via `read_table()`, usando a abordagem CTAS para maior performance em volumes grandes.

2. **Seleção de colunas do schema Silver** — Um subset de 32 colunas relevantes é selecionado (removendo `pesid`, `regional`, `delegacia`, `uop` que eram da Bronze).

3. **Limpeza de dados** — `limpar_dados()` remove linhas completamente vazias (onde todas as colunas originais são `NaN`) e linhas duplicadas, registrando o total removido em log.

4. **Renomeação semântica das colunas** — Todas as colunas recebem um prefixo semântico de acordo com o padrão de Data Warehouse adotado pelo projeto:

   | Prefixo | Semântica |
   |---|---|
   | `id_` | Identificador técnico |
   | `dat_` | Campo de data |
   | `nom_` | Campo nominal/descritivo (texto) |
   | `num_` | Campo numérico |
   | `des_` | Campo descritivo longo |
   | `cod_` | Código de negócio |
   | `qtd_` | Quantidade |
   | `vlr_` | Valor numérico contínuo |
   | `ind_` | Indicador/flag |

5. **Limpeza de valores numéricos** — Campos como `num_br`, `num_km`, `num_idade` têm decimais removidos (ex: `"2.8"` → `"2"`, `"100,5"` → `"100"`).

6. **Conversão de tipos tipados** — Cada coluna é convertida para seu tipo correto: `int`, `str`, `date`, `double`.

7. **Regras de negócio aplicadas:**

   - **Sexo:** Padronizado para `MASCULINO`, `FEMININO` ou `NÃO INFORMADO`.
   - **Idade:** Valores inválidos ou acima de 99 anos são substituídos por `-1`.
   - **Faixa etária (`ind_faixa_etaria`):** Coluna calculada com 13 faixas: `n/i`, `< 18`, `18-22`, ..., `> 60`.
   - **Tipo envolvido:** Valores `nan` ou vazios → `"não informado"`.
   - **Condição meteorológica:** `"ignorado"` → `"não informado"`.
   - **Ano de fabricação:** Anos ≤ 1500 ou inválidos → `-1`.
   - **Campos nulos:** `nom_estado_fisico`, `des_classificacao_acidente`, `des_tipo_acidente`, `des_causa_acidente` recebem `"Não informado"` quando nulos.

8. **Padronização textual** — Todos os campos de texto são convertidos para **MAIÚSCULO** para garantir consistência nos joins e filtros analíticos.

9. **Escrita no S3 (Parquet)** — Gravado em Parquet/Snappy no Glue Catalog.

10. **Disparo automático** — O Glue Job `glue_processar_gold` é disparado ao final.

#### Schema Silver (33 colunas)

```
id_ocorrencia, dat_data, nom_dia_semana, num_horario, nom_uf, num_br, num_km,
nom_municipio, des_causa_principal, des_causa_acidente, des_tipo_acidente,
des_classificacao_acidente, nom_fase_dia, nom_sentido_via, nom_condicao_meteorologica,
nom_tipo_pista, nom_tracado_via, nom_uso_solo, cod_veiculo, nom_tipo_veiculo,
nom_marca_veiculo, nom_tipo_envolvido, num_ano_fabricacao, nom_estado_fisico,
num_idade, nom_sexo, ind_faixa_etaria, qtd_ilesos, qtd_feridos_leves,
qtd_feridos_graves, qtd_mortos, vlr_latitude, vlr_longitude
```

---

### 🥇 CAMADA GOLD — `03_glue_processa_gold.py`

**Objetivo:** Transformar o dataset Silver em um modelo dimensional (Star Schema) otimizado para consumo analítico por ferramentas de BI, composto por 6 dimensões e 2 tabelas fato, armazenadas no formato Apache Iceberg com suporte a UPSERT.

#### Parâmetros de entrada (Glue Job Arguments)

| Parâmetro | Descrição |
|---|---|
| `db_origem` | Database da tabela Silver |
| `tb_origem` | Nome da tabela Silver de origem |
| `db_destino` | Database Gold de destino |
| `tabela_destino_01` a `tabela_destino_08` | Nomes das 8 tabelas Gold geradas |
| `s3_path` | Caminho S3 raiz para as tabelas Gold |

#### Modelo Dimensional Gerado (Star Schema)

```
                    ┌─────────────┐
                    │ dim_tempo   │
                    │ (id_tempo)  │
                    └──────┬──────┘
                           │
┌──────────────┐   ┌───────┴──────────┐   ┌─────────────────┐
│dim_localizacao│──▶│  FATO_ACIDENTES  │◀──│   dim_clima     │
│(id_localizacao)   │  (id_acidente)   │   │  (id_clima)     │
└──────────────┘   └───────┬──────────┘   └─────────────────┘
                           │
                    ┌──────┴──────┐
                    │dim_causa_   │
                    │acidente     │
                    │(id_causa_   │
                    │acidente)    │
                    └─────────────┘

                    ┌─────────────┐
                    │ dim_pessoa  │
                    │ (id_pessoa) │
                    └──────┬──────┘
                           │
┌──────────────┐   ┌───────┴──────────┐
│  dim_veiculo │──▶│  FATO_ENVOLVIDOS │
│ (id_veiculo) │   │  (id_envolvido)  │
└──────────────┘   └──────────────────┘
```

---

#### 📊 Dimensões

**`dim_localizacao` (tabela_destino_01)**

Contém os dados geográficos da ocorrência. Particionada por `nom_uf` para performance.

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_localizacao` | INT | Surrogate key gerada |
| `nom_uf` | STRING | Unidade Federativa |
| `num_br` | INT | Número da rodovia BR |
| `num_km` | INT | Quilômetro do acidente |
| `nom_municipio` | STRING | Nome do município |
| `vlr_latitude` | DOUBLE | Latitude geográfica |
| `vlr_longitude` | DOUBLE | Longitude geográfica |
| `nom_uso_solo` | STRING | Tipo de uso do solo (urbano/rural) |

---

**`dim_tempo` (tabela_destino_02)**

Contém os dados temporais da ocorrência.

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_tempo` | INT | Surrogate key gerada |
| `dat_data` | DATE | Data da ocorrência |
| `nom_dia_semana` | STRING | Dia da semana |
| `num_horario` | STRING | Horário da ocorrência |
| `nom_fase_dia` | STRING | Fase do dia (manhã, tarde, noite, etc.) |

---

**`dim_clima` (tabela_destino_03)**

Contém as condições meteorológicas do momento do acidente.

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_clima` | INT | Surrogate key gerada |
| `nom_condicao_meteorologica` | STRING | Condição do tempo (chuva, sol, neblina, etc.) |

---

**`dim_causa_acidente` (tabela_destino_04)**

Contém os dados de causa, tipo e classificação do acidente, e o estado físico dos envolvidos.

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_causa_acidente` | INT | Surrogate key gerada |
| `des_causa_acidente` | STRING | Descrição da causa |
| `des_tipo_acidente` | STRING | Tipo do acidente (colisão, capotamento, etc.) |
| `des_classificacao_acidente` | STRING | Classificação (com vítimas, sem vítimas, fatal) |
| `nom_estado_fisico` | STRING | Estado físico do envolvido |

---

**`dim_pessoa` (tabela_destino_05)**

Contém o perfil demográfico dos envolvidos.

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_pessoa` | INT | Surrogate key gerada |
| `nom_sexo` | STRING | Sexo (MASCULINO / FEMININO / NÃO INFORMADO) |
| `num_idade` | INT | Idade (−1 = não informado) |
| `ind_faixa_etaria` | STRING | Faixa etária calculada (`< 18`, `18-22`, ..., `> 60`) |
| `nom_tipo_envolvido` | STRING | Tipo (Condutor, Passageiro, Pedestre, etc.) |

---

**`dim_veiculo` (tabela_destino_06)**

Contém as características dos veículos envolvidos.

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_veiculo` | INT | Surrogate key gerada |
| `cod_veiculo` | INT | Código original do veículo |
| `nom_tipo_veiculo` | STRING | Tipo do veículo (moto, carro, caminhão, etc.) |
| `nom_marca_veiculo` | STRING | Marca do veículo |
| `num_ano_fabricacao` | INT | Ano de fabricação (−1 = não informado) |

---

#### 📈 Tabelas Fato

**`fato_acidentes` (tabela_destino_07) — Grão: Ocorrência**

Uma linha por `id_ocorrencia`. Agrega as quantidades de vítimas e referencia todas as dimensões pelas surrogate keys. Ideal para análises no nível do acidente.

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_acidente` | INT | Surrogate key da Fato |
| `id_tempo` | INT | FK → dim_tempo |
| `id_localizacao` | INT | FK → dim_localizacao |
| `id_clima` | INT | FK → dim_clima |
| `id_causa_acidente` | INT | FK → dim_causa_acidente |
| `id_ocorrencia` | INT | Chave de negócio original da PRF |
| `qtd_total_pessoas_acidente` | INT | Total de pessoas envolvidas no acidente |
| `qtd_ilesos` | INT | Quantidade de ilesos |
| `qtd_feridos_leves` | INT | Quantidade de feridos leves |
| `qtd_feridos_graves` | INT | Quantidade de feridos graves |
| `qtd_mortos` | INT | Quantidade de mortos |

---

**`fato_envolvidos` (tabela_destino_08) — Grão: Pessoa/Veículo por Ocorrência**

Uma linha por envolvido no acidente. Contém indicadores e scores de gravidade individual. Ideal para análises no nível da vítima.

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_envolvido` | INT | Surrogate key da Fato |
| `id_veiculo` | INT | FK → dim_veiculo |
| `id_tempo` | INT | FK → dim_tempo |
| `id_pessoa` | INT | FK → dim_pessoa |
| `id_ocorrencia` | INT | Chave de negócio original da PRF |
| `qtd_envolvido` | INT | Contador base (sempre 1 por linha) |
| `ind_vitima` | INT | 1 se não saiu ileso; 0 caso contrário |
| `ind_obito` | INT | 1 se óbito; 0 caso contrário |
| `ind_ferido` | INT | 1 se ferido leve ou grave; 0 caso contrário |
| `ind_ileso` | INT | 1 se ileso; 0 caso contrário |
| `ind_condutor` | INT | 1 se era condutor do veículo; 0 caso contrário |
| `vlr_score_gravidade` | INT | Score de gravidade (Ileso=0, Ferido Leve=1, Ferido Grave=3, Óbito=10) |

---

## 🛠️ Biblioteca Utilitária — `utils.py`

Centraliza todas as funções reutilizáveis do pipeline. Abaixo a documentação de cada função:

### Funções de Leitura

| Função | Descrição |
|---|---|
| `carregar_csvs_para_dataframe_s3(caminho_s3, header)` | Lê múltiplos CSVs de um prefixo S3. Tenta encodings UTF-8, ISO-8859-1 e CP1252. Detecta e ignora Mojibake. Adiciona coluna `arquivo_origem`. |
| `read_table(database, table, query, ctas_approach)` | Executa uma query SQL no Athena e retorna um DataFrame Pandas. Suporta CTAS para grandes volumes. |

### Funções de Transformação

| Função | Descrição |
|---|---|
| `normalizar_colunas(df)` | Padroniza nomes de colunas: remove BOM, corrige encoding, converte para lowercase, substitui espaços por `_`, remove caracteres especiais e colunas `Unnamed`. |
| `select_columns(df, columns, verbose)` | Mantém apenas as colunas listadas no schema. Avisa em log sobre colunas ausentes. |
| `limpar_dados(df)` | Remove linhas completamente vazias e duplicadas. Exibe estatísticas do processo. |
| `rename_columns(df, mapping)` | Renomeia colunas conforme dicionário de mapeamento. |
| `alterar_tipos(df, tipos)` | Converte colunas para os tipos especificados: `int`, `str`, `date`, `double`. |
| `padronizar_campos_join(df, coluna_data, lat_col, lon_col)` | Padroniza campos usados em joins: converte datas e coordenadas, corrige vírgula decimal, arredonda para 5 casas. |
| `realizar_merge_limpo(df_left, df_right, keys_left, keys_right, how)` | Realiza merge entre DataFrames e exibe estatísticas de match (quantidade e percentual). |
| `agrupar_dataframe(df, colunas)` | Agrupa o DataFrame por colunas especificadas, eliminando duplicatas para criação de dimensões. |
| `adicionar_id_unico(df, nome_coluna)` | Gera uma coluna de surrogate key sequencial para identificar registros únicos nas dimensões e fatos. |
| `corrigir_mojibake(df)` | Detecta e corrige caracteres com encoding incorreto (Latin-1 lido como UTF-8). |
| `normalizar_colunas(df)` | Vide acima. |

### Funções de Escrita

| Função | Descrição |
|---|---|
| `ingest_dataframe_to_s3_parquet(df, database, table, s3_path, partition_cols, mode, description)` | Grava o DataFrame como Parquet no S3 e registra a tabela no Glue Catalog. Usa compressão Snappy. Suporta modos `overwrite`, `append` e `overwrite_partitions`. |
| `ingest_to_iceberg(df, database, table, s3_path, partition_cols, merge_cols)` | Grava o DataFrame em tabela Apache Iceberg. Se a tabela não existir, faz INSERT inicial. Se existir e `merge_cols` for informado, executa UPSERT dinâmico via SQL MERGE no Athena. Tabelas temporárias são limpas automaticamente após o merge. |

### Funções de Orquestração

| Função | Descrição |
|---|---|
| `executar_glue_job(nome_job)` | Dispara a execução de outro Glue Job via Boto3 e retorna o `JobRunId`. Usado para encadear Bronze → Silver → Gold automaticamente. |

---

## 🔗 Encadeamento Automático dos Jobs

O pipeline é auto-orquestrado sem necessidade de Step Functions ou Airflow:

```
glue_processar_bronze
        │
        └─► executar_glue_job("glue_processar_silver")
                    │
                    └─► executar_glue_job("glue_processar_gold")
```

Cada job dispara o próximo ao finalizar com sucesso.

---

## 📊 Modelo Físico do Star Schema (Gold)

```
┌─────────────────────────────┐
│        fato_acidentes        │
│─────────────────────────────│
│ id_acidente (PK)            │
│ id_tempo (FK)               │──────────────┐
│ id_localizacao (FK)         │──────────┐   │
│ id_clima (FK)               │──────┐   │   │
│ id_causa_acidente (FK)      │──┐   │   │   │
│ id_ocorrencia               │  │   │   │   │
│ qtd_total_pessoas_acidente  │  │   │   │   │
│ qtd_ilesos                  │  │   │   │   │
│ qtd_feridos_leves           │  │   │   │   │
│ qtd_feridos_graves          │  │   │   │   │
│ qtd_mortos                  │  │   │   │   │
└─────────────────────────────┘  │   │   │   │
                                  │   │   │   │
┌─────────────────────────────┐  │   │   │   │
│     fato_envolvidos          │  │   │   │   │
│─────────────────────────────│  │   │   │   │
│ id_envolvido (PK)           │  │   │   │   │
│ id_veiculo (FK)         ─┐  │  │   │   │   │
│ id_tempo (FK)           ──────────────────┘│
│ id_pessoa (FK)          ─────────┐│   │   │
│ id_ocorrencia               │  │ ││   │   │
│ qtd_envolvido               │  │ ││   │   │
│ ind_vitima                  │  │ ││   │   │
│ ind_obito                   │  │ ││   │   │
│ ind_ferido                  │  │ ││   │   │
│ ind_ileso                   │  │ ││   │   │
│ ind_condutor                │  │ ││   │   │
│ vlr_score_gravidade         │  │ ││   │   │
└─────────────────────────────┘  │ ││   │   │
                                  │ ││   │   │
  ┌──────────────────────┐        │ ││   │   │
  │    dim_causa_acidente │◄───────┘ ││   │   │
  │ id_causa_acidente(PK)│          ││   │   │
  │ des_causa_acidente   │          ││   │   │
  │ des_tipo_acidente    │          ││   │   │
  │ des_classificacao_.. │          ││   │   │
  │ nom_estado_fisico    │          ││   │   │
  └──────────────────────┘          ││   │   │
                                     ││   │   │
  ┌──────────────────────┐           ││   │   │
  │      dim_veiculo      │◄──────────┘│   │   │
  │ id_veiculo (PK)      │            │   │   │
  │ cod_veiculo          │            │   │   │
  │ nom_tipo_veiculo     │            │   │   │
  │ nom_marca_veiculo    │            │   │   │
  │ num_ano_fabricacao   │            │   │   │
  └──────────────────────┘            │   │   │
                                      │   │   │
  ┌──────────────────────┐            │   │   │
  │      dim_pessoa       │◄───────────┘   │   │
  │ id_pessoa (PK)       │                │   │
  │ nom_sexo             │                │   │
  │ num_idade            │                │   │
  │ ind_faixa_etaria     │                │   │
  │ nom_tipo_envolvido   │                │   │
  └──────────────────────┘                │   │
                                          │   │
  ┌──────────────────────┐                │   │
  │    dim_localizacao    │◄───────────────┘   │
  │ id_localizacao (PK)  │                    │
  │ nom_uf               │                    │
  │ num_br               │                    │
  │ num_km               │                    │
  │ nom_municipio        │                    │
  │ vlr_latitude         │                    │
  │ vlr_longitude        │                    │
  │ nom_uso_solo         │                    │
  └──────────────────────┘                    │
                                              │
  ┌──────────────────────┐                    │
  │      dim_tempo        │◄───────────────────┘
  │ id_tempo (PK)        │
  │ dat_data             │
  │ nom_dia_semana       │
  │ num_horario          │
  │ nom_fase_dia         │
  └──────────────────────┘

  ┌──────────────────────┐
  │       dim_clima       │
  │ id_clima (PK)        │
  │ nom_condicao_...     │
  └──────────────────────┘
```

---

## 🧠 Decisões de Design

### Por que todos os tipos são STRING na Bronze?
A camada Bronze é uma réplica fiel dos dados brutos. Forçar tipos inteiros ou datas pode causar falhas de ingestão quando o dado vem malformado. A conversão de tipos é responsabilidade exclusiva da camada Silver.

### Por que Parquet na Bronze/Silver e Iceberg na Gold?
Parquet é mais simples e rápido para ingestão. O Iceberg é necessário apenas na Gold, onde os jobs precisam de UPSERT (atualizar registros existentes sem duplicar ao rodar novamente). Isso garante idempotência dos jobs Gold.

### Por que o score de gravidade `vlr_score_gravidade`?
Um campo numérico ponderado (Ileso=0, Ferido Leve=1, Ferido Grave=3, Óbito=10) permite que ferramentas de BI calculem índices de gravidade agregados por região, período ou tipo de veículo, sem precisar filtrar por texto.

### Por que duas tabelas fato?
- **`fato_acidentes`**: grão de ocorrência — uma linha por acidente. Ideal para contar acidentes, somar vítimas totais, analisar distribuição temporal e geográfica.
- **`fato_envolvidos`**: grão de pessoa/veículo — uma linha por envolvido. Ideal para análises de perfil de vítimas, tipo de condutor, taxa de mortalidade por faixa etária.

---

## ⚠️ Pontos de Atenção e Limitações Conhecidas

- **Encoding misto de CSVs:** O pipeline tenta `UTF-8 → ISO-8859-1 → CP1252`. Se um arquivo vier em `UTF-16` ou outro encoding exótico, será ignorado com log de erro crítico.
- **Coluna `num_ordem_tipo_acidente`:** Está presente no mapeamento Silver mas não no schema final de 33 colunas — é descartada silenciosamente.
- **Coordenadas para join geográfico:** A função `padronizar_campos_join()` existe no `utils.py` mas não é chamada no pipeline Silver atual. O join geográfico na Gold usa latitude/longitude diretamente.
- **Tabela Iceberg temporária no UPSERT:** Durante o UPSERT, uma tabela temporária `{tabela}_temp_upsert_{timestamp}` é criada no Athena e apagada em seguida. Em caso de falha, essa tabela pode permanecer no catálogo e precisar de limpeza manual.
- **Idempotência na Bronze/Silver:** Como o modo é `overwrite_partitions` sem particionamento definido (`partition_cols=None`), na prática os jobs fazem full overwrite a cada execução.

---

## 🗂️ Fonte dos Dados

Os dados são disponibilizados publicamente pela **Polícia Rodoviária Federal (PRF)** do Brasil, contendo registros de ocorrências em rodovias federais com informações sobre localização, causas, veículos, perfil dos envolvidos e condições do acidente.

---

## 🏗️ Infraestrutura como Código (Terraform)

Toda a infraestrutura do projeto é provisionada via **Terraform**, organizada em três arquivos dentro da pasta `terraform/`.

### Pré-requisitos

- Terraform `>= 1.3` instalado
- AWS CLI configurado com credenciais válidas (`aws configure`)
- Provider AWS `~> 5.0`

### Como provisionar

```bash
cd terraform/
terraform init
terraform plan
terraform apply
```

---

### `variables.tf` — Variáveis de configuração

| Variável | Tipo | Default | Descrição |
|---|---|---|---|
| `aws_region` | string | `us-east-1` | Região AWS onde todos os recursos serão criados |
| `project_name` | string | `datalake-empresa` | Prefixo usado para nomear todos os recursos criados |

---

### `main.tf` — Recursos principais

#### Buckets S3

São criados dois buckets S3, ambos com versionamento habilitado, criptografia AES256 e bloqueio total de acesso público:

| Bucket | Finalidade |
|---|---|
| `{project_name}-glue-assets-{account_id}` | Armazena os scripts Python dos jobs e o diretório `/temp/` usado pelo Glue e pelo Athena durante queries CTAS |
| `{project_name}-datalake-{account_id}` | Armazena os dados em todas as camadas: `/raw/` (CSVs originais), `/bronze/`, `/silver/` e `/gold/` |

> O Account ID é resolvido automaticamente via `data "aws_caller_identity"`, evitando nomes de bucket hardcoded e garantindo unicidade global.

#### Upload dos scripts para o S3

Os quatro arquivos Python são enviados ao bucket de assets antes da criação dos jobs. O campo `etag = filemd5(...)` garante que o Terraform reenvie o arquivo automaticamente sempre que o conteúdo mudar.

| Arquivo local | Destino no S3 |
|---|---|
| `../scripts/utils.py` | `scripts/utils.py` |
| `../scripts/01_glue_processa_bronze.py` | `scripts/01_glue_processa_bronze.py` |
| `../scripts/02_glue_processa_silver.py` | `scripts/02_glue_processa_silver.py` |
| `../scripts/03_glue_processa_gold.py` | `scripts/03_glue_processa_gold.py` |

#### Glue Catalog Databases

Três databases são criados no Glue Data Catalog, um por camada:

| Database | Camada |
|---|---|
| `{project_name}_bronze` | Bronze |
| `{project_name}_silver` | Silver |
| `{project_name}_gold` | Gold |

#### Glue Jobs

Três jobs são provisionados com as seguintes configurações comuns:

| Configuração | Valor | Motivo |
|---|---|---|
| `glue_version` | `4.0` | Versão mais recente, com suporte nativo a Iceberg e awswrangler |
| `worker_type` | `G.1X` | Balanceamento entre custo e capacidade para volumes médios |
| `number_of_workers` | `10` | Paralelismo suficiente para o processamento |
| `max_retries` | `0` | Sem retentativa automática — falhas devem ser investigadas |
| `--extra-py-files` | `s3://.../scripts/utils.py` | Disponibiliza o `utils.py` para importação dentro dos jobs |
| `--job-bookmark-option` | `job-bookmark-disable` | Os jobs fazem full overwrite — bookmark incremental não se aplica |

O timeout do job Gold é de **120 minutos** (contra 60 dos demais), pois ele cria 8 tabelas, executa múltiplos joins e opera com MERGE no Iceberg.

Todos os parâmetros de negócio (`--db_origem`, `--tb_destino`, `--s3_path`, `--tabela_destino_01..08`, etc.) são injetados via `default_arguments`, eliminando a necessidade de passá-los manualmente a cada execução.

---

### `iam_role.tf` — IAM Role e Políticas

Uma única IAM Role (`{project_name}-glue-role`) é criada com trust policy para o serviço `glue.amazonaws.com`. A ela são anexadas **6 políticas**:

#### Policy 1 — `AWSGlueServiceRole` (AWS Managed)

Política gerenciada pela AWS que concede as permissões base para o Glue funcionar: acesso ao Glue Catalog interno, CloudWatch básico, EC2 para VPC, e outros serviços auxiliares do serviço.

#### Policy 2 — S3 (customizada)

Controla o acesso granular aos buckets do projeto com quatro statements distintos:

| Statement | Ações | Recursos |
|---|---|---|
| `ListBuckets` | `s3:ListBucket`, `s3:GetBucketLocation` | Buckets de assets, datalake e temp do Athena |
| `ReadGlueAssets` | `s3:GetObject`, `s3:GetObjectVersion` | Apenas o bucket de scripts (leitura) |
| `ReadWriteDatalake` | `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` | Todo o bucket do datalake (Bronze/Silver/Gold) |
| `ReadWriteTemp` | Leitura e escrita completa | Prefixo `/temp/` dos assets + bucket temp do Athena |

#### Policy 3 — Athena (customizada)

Necessária porque as funções `read_table()` e `ingest_to_iceberg()` do `utils.py` executam queries via `wr.athena.*`. Concede permissões para iniciar, monitorar e recuperar resultados de queries no Athena.

#### Policy 4 — Glue Data Catalog (customizada)

O `awswrangler` cria e atualiza tabelas e partições no Glue Catalog a cada execução dos jobs. Esta policy concede CRUD completo sobre databases e tabelas, mas **somente nos três databases do projeto** (`_bronze`, `_silver`, `_gold`), seguindo o princípio de menor privilégio.

#### Policy 5 — Trigger de Jobs (customizada)

 **A política mais frequentemente esquecida.** O `utils.py` usa `boto3.client("glue").start_job_run()` para encadear Bronze → Silver → Gold automaticamente. Sem esta policy, a chamada retorna `AccessDeniedException` em runtime e o encadeamento falha silenciosamente.

Concede `glue:StartJobRun` e `glue:GetJobRun` especificamente para os três jobs do projeto.

#### Policy 6 — CloudWatch Logs (customizada)

O argumento `--enable-continuous-cloudwatch-log` nos jobs exige permissão explícita para criar e escrever em log groups sob o prefixo `/aws-glue/*`. Sem esta policy, os logs em tempo real não são gravados.

---

### Diagrama de dependências Terraform

```
data.aws_caller_identity
        │
        ├──► aws_s3_bucket.glue_assets
        │         └──► aws_s3_object.glue_script_* (4 scripts)
        │
        ├──► aws_s3_bucket.datalake
        │
        ├──► aws_glue_catalog_database.bronze
        ├──► aws_glue_catalog_database.silver
        ├──► aws_glue_catalog_database.gold
        │
        └──► aws_iam_role.glue_role
                  ├──► aws_iam_role_policy_attachment.glue_policy        (managed)
                  ├──► aws_iam_policy.glue_s3_policy         ──► attachment
                  ├──► aws_iam_policy.glue_athena_policy      ──► attachment
                  ├──► aws_iam_policy.glue_catalog_policy     ──► attachment
                  ├──► aws_iam_policy.glue_trigger_jobs_policy ──► attachment
                  └──► aws_iam_policy.glue_logs_policy        ──► attachment
                            │
                            ▼
              aws_glue_job.processa_bronze
                            │  depends_on scripts + policies
                            ▼
              aws_glue_job.processa_silver
                            │  depends_on bronze + scripts + policies
                            ▼
              aws_glue_job.processa_gold
```
