# Importa as funções que criámos no ficheiro utils.py
import numpy as np
import pandas as pd
import awswrangler as wr

print(f"Versão NumPy: {np.__version__}")
print(f"Versão Pandas: {pd.__version__}")
print(f"Versão Wrangler: {wr.__version__}")
from utils import limpar_dados, rename_columns, padronizar_campos_join, select_columns, normalizar_colunas, alterar_tipos,read_table, ingest_dataframe_to_s3_parquet, ingest_to_iceberg, executar_glue_job


import sys
from awsglue.utils import getResolvedOptions

# Liste exatamente os nomes das chaves que você colocou no Glue (sem o --)
params = [
    'db_origem',
    'tb_origem',
    'db_destino',
    'tb_destino',
    's3_path'
]

# O getResolvedOptions transforma os parâmetros em um dicionário Python
args = getResolvedOptions(sys.argv, params)

# Atribuindo a variáveis para usar no seu código
database_bronze = args['db_origem']
tabela_bronze   = args['tb_origem']
db_destino = args['db_destino']
tb_destino   = args['tb_destino']
s3_path         = args['s3_path']


# Exemplo de log para confirmar se os valores chegaram
print(f"Origem: {database_bronze}.{tabela_bronze}")


df_detran = read_table(
    database=database_bronze, 
    table=tabela_bronze, 
    ctas_approach=True
)

print("dados da tb_bronze_prf_ocorrencia")
print(df_detran.columns.tolist())
print(df_detran.head(5))



SCHEMA_DETRAN = [
    'id',
    'data_inversa',
    'dia_semana',
    'horario',
    'uf',
    'br',
    'km',
    'municipio',
    'causa_principal',
    'causa_acidente',
    'ordem_tipo_acidente',
    'tipo_acidente',
    'classificacao_acidente',
    'fase_dia',
    'sentido_via',
    'condicao_metereologica',
    'tipo_pista',
    'tracado_via',
    'uso_solo',
    'id_veiculo',
    'tipo_veiculo',
    'marca',
    'tipo_envolvido',
    'ano_fabricacao_veiculo',
    'estado_fisico',
    'idade',
    'sexo',
    'ilesos',
    'feridos_leves',
    'feridos_graves',
    'mortos',
    'latitude',
    'longitude'
]
df_detran = select_columns(df_detran, SCHEMA_DETRAN)
print(df_detran.columns.tolist())


# Se o DataFrame não estiver vazio, limpa e exibe os dados
if not df_detran.empty:
    # Chama a nova função de limpeza
    df_detran_limpo = limpar_dados(df_detran)
    
    print("\nVisualização dos primeiros registos:")
    # print(df_detran_limpo.head())

# dicionário de mapeamento
mapping = {

    # =========================
    # dim_estrada
    # =========================
    "id": "id_ocorrencia",
    "sentido_via": "nom_sentido_via",
    "tipo_pista": "nom_tipo_pista",
    "tracado_via": "nom_tracado_via",

    # =========================
    # dim_local
    # =========================
    "uf": "nom_uf",
    "br": "num_br",
    "km": "num_km",
    "municipio": "nom_municipio",
    "latitude": "vlr_latitude",
    "longitude": "vlr_longitude",
    "uso_solo": "nom_uso_solo",

    # =========================
    # dim_tempo
    # =========================
    "fase_dia": "nom_fase_dia",
    "dia_semana": "nom_dia_semana",
    "horario": "num_horario",
    "data_inversa": "dat_data",

    # =========================
    # dim_pessoa
    # =========================
    "idade": "num_idade",
    "sexo": "nom_sexo",
    "tipo_envolvido": "nom_tipo_envolvido",
    "estado_fisico": "nom_estado_fisico",

    # =========================
    # dim_clima
    # =========================
    "condicao_metereologica": "nom_condicao_meteorologica",

    # =========================
    # dim_gravidade_ocorrencia
    # =========================
    "ordem_tipo_acidente": "num_ordem_tipo_acidente",
    "causa_principal": "des_causa_principal",
    "causa_acidente": "des_causa_acidente",
    "tipo_acidente": "des_tipo_acidente",
    "classificacao_acidente": "des_classificacao_acidente",
    "ilesos": "qtd_ilesos",
    "feridos_leves": "qtd_feridos_leves",
    "feridos_graves": "qtd_feridos_graves",
    "mortos": "qtd_mortos",

    # =========================
    # dim_veiculo
    # =========================
    "id_veiculo": "cod_veiculo",
    "tipo_veiculo": "nom_tipo_veiculo",
    "marca": "nom_marca_veiculo",
    "ano_fabricacao_veiculo": "num_ano_fabricacao"
}

# aplicar a renomeação no dataframe

df_detran_limpo = rename_columns(df_detran_limpo, mapping=mapping)

# visualizar as colunas renomeadas
print(df_detran_limpo.columns.tolist())



# exemplo: "2.8" -> "2"
df_detran_limpo['num_br'] = df_detran_limpo['num_br'].astype(str).str.split('.').str[0]
# exemplo: "2.8" -> "2"
df_detran_limpo['num_km'] = df_detran_limpo['num_km'].astype(str).str.split(',').str[0]
df_detran_limpo['num_idade'] = df_detran_limpo['num_idade'].astype(str).str.split('.').str[0]
df_detran_limpo['id_ocorrencia'] = df_detran_limpo['id_ocorrencia'].astype(str).str.split('.').str[0]
df_detran_limpo['cod_veiculo'] = df_detran_limpo['cod_veiculo'].astype(str).str.split('.').str[0]
df_detran_limpo['qtd_ilesos'] = df_detran_limpo['qtd_ilesos'].astype(str).str.split('.').str[0]
df_detran_limpo['qtd_feridos_leves'] = df_detran_limpo['qtd_feridos_leves'].astype(str).str.split('.').str[0]
df_detran_limpo['qtd_feridos_graves'] = df_detran_limpo['qtd_feridos_graves'].astype(str).str.split('.').str[0]
df_detran_limpo['qtd_mortos'] = df_detran_limpo['qtd_mortos'].astype(str).str.split('.').str[0]
df_detran_limpo['num_ano_fabricacao'] = df_detran_limpo['num_ano_fabricacao'].astype(str).str.split('.').str[0]


# dicionário com os tipos de dados desejados
tipos = {
    'id_ocorrencia': 'int',
    'dat_data': 'date',
    'nom_dia_semana': 'str',
    'num_horario': 'str',
    'nom_uf': 'str',
    'num_br': 'int',
    'num_km': 'int',
    'nom_municipio': 'str',
    'des_causa_principal': 'str',
    'des_causa_acidente': 'str',
    'des_tipo_acidente': 'str',
    'des_classificacao_acidente': 'str',
    'nom_fase_dia': 'str',
    'nom_sentido_via': 'str',
    'nom_condicao_meteorologica': 'str',
    'nom_tipo_pista': 'str',
    'nom_tracado_via': 'str',
    'nom_uso_solo': 'str',
    'cod_veiculo': 'int',
    'nom_tipo_veiculo': 'str',
    'nom_marca_veiculo': 'str',
    'nom_tipo_envolvido': 'str',
    'num_ano_fabricacao': 'int',
    'nom_estado_fisico': 'str',
    'num_idade': 'int',
    'nom_sexo': 'str',
    'qtd_ilesos': 'int',
    'qtd_feridos_leves': 'int',
    'qtd_feridos_graves': 'int',
    'qtd_mortos': 'int',
    'vlr_latitude': 'double',
    'vlr_longitude': 'double',
    'regional': 'str',
    'delegacia': 'str',
    'uop': 'str',
    'arquivo_origem': 'str',
    'uf_dnit': 'str',
    'rodovia': 'str',
    'km_inicial': 'double',
    'km_final': 'double',
    'extensao_km': 'double',
    'data': 'date',
    'icmnp': 'double',
    'arquivo_origem_dnit': 'str',
    'observacao': 'str',
    'icc': 'double',
    'icp': 'double',
    'icm': 'double'
}

# chamar a função
df_final = alterar_tipos(df_detran_limpo, tipos)

# exibir o dataframe resultante
print(df_final.dtypes)
# print(df_detran_limpo)
# print(df_detran_limpo.dtypes)

# 1. Padroniza tudo: Maiúsculo e sem espaços sobrando nas pontas
df_final["nom_sexo"] = df_final["nom_sexo"].str.upper().str.strip()

# 2. Faz a checagem (agora buscando as palavras em MAIÚSCULO)
df_final.loc[
    ~df_final["nom_sexo"].isin(["MASCULINO", "FEMININO"]),
    "nom_sexo"
] = "NÃO INFORMADO"

df_final["num_idade"] = (
    df_final["num_idade"]
        .astype(str)      # garante que tudo vire string
        .str.strip()      # remove espaços
        .replace("", "-1") # vazio → -1
        .fillna("-1")     # null → -1
        .astype(int)      # converte para inteiro
)

# regra: idade > 99 vira -1
df_final.loc[df_final["num_idade"] > 99, "num_idade"] = -1

import numpy as np

df_final["ind_faixa_etaria"] = np.select(
    [
        df_final["num_idade"] < 0,
        df_final["num_idade"] < 18,
        df_final["num_idade"] <= 22,
        df_final["num_idade"] <= 26,
        df_final["num_idade"] <= 30,
        df_final["num_idade"] <= 34,
        df_final["num_idade"] <= 38,
        df_final["num_idade"] <= 42,
        df_final["num_idade"] <= 46,
        df_final["num_idade"] <= 52,
        df_final["num_idade"] <= 56,
        df_final["num_idade"] <= 60
    ],
    [
        "n/i",
        "< 18",
        "18 - 22",
        "23 - 26",
        "27 - 30",
        "31 - 34",
        "35 - 38",
        "39 - 42",
        "43 - 46",
        "47 - 52",
        "53 - 56",
        "57 - 60"
    ],
    default="> 60"
)

df_final["nom_tipo_envolvido"] = (
    df_final["nom_tipo_envolvido"]
    .astype(str)
    .str.strip()
    .replace("", "não informado")
    .replace("nan", "não informado")
)

#-- tratamento clima --
df_final["nom_condicao_meteorologica"] = df_final["nom_condicao_meteorologica"].str.strip()
df_final["nom_condicao_meteorologica"] = (
    df_final["nom_condicao_meteorologica"]
    .astype(str)
    .replace("ignorado", "não informado")
)

df_final["num_ano_fabricacao"] = (
    df_final["num_ano_fabricacao"]
    .astype(str)
    .str.strip()
    .str[:4]   # mantém apenas os 4 primeiros caracteres
)

df_final["num_ano_fabricacao"] = (
    pd.to_numeric(
        df_final["num_ano_fabricacao"],
        errors="coerce"
    )
    .fillna(-1)
)

df_final.loc[
    df_final["num_ano_fabricacao"] <= 1500,
    "num_ano_fabricacao"
] = -1

df_final["num_ano_fabricacao"] = df_final["num_ano_fabricacao"].astype(int)
df_final['nom_estado_fisico'] = df_final['nom_estado_fisico'].fillna('Não informado')
df_final['des_classificacao_acidente'] = df_final['des_classificacao_acidente'].fillna('Não informado')
df_final['des_tipo_acidente'] = df_final['des_tipo_acidente'].fillna('Não informado')
df_final['des_causa_acidente'] = df_final['des_causa_acidente'].fillna('Não informado')

print("===== df_final =====")
print(df_final.head(5))
print(df_final.columns.tolist())

df_final['nom_municipio'] = df_final['nom_municipio'].str.upper()
df_final['des_causa_principal'] = df_final['des_causa_principal'].str.upper()
df_final['des_causa_acidente'] = df_final['des_causa_acidente'].str.upper()
df_final['des_tipo_acidente'] = df_final['des_tipo_acidente'].str.upper()
df_final['des_classificacao_acidente'] = df_final['des_classificacao_acidente'].str.upper()
df_final['nom_fase_dia'] = df_final['nom_fase_dia'].str.upper()
df_final['nom_sentido_via'] = df_final['nom_sentido_via'].str.upper()
df_final['nom_uso_solo'] = df_final['nom_uso_solo'].str.upper()
df_final['nom_tipo_envolvido'] = df_final['nom_tipo_envolvido'].str.upper()
df_final['nom_marca_veiculo'] = df_final['nom_marca_veiculo'].str.upper()
df_final['nom_tipo_veiculo'] = df_final['nom_tipo_veiculo'].str.upper()
df_final['nom_sexo'] = df_final['nom_sexo'].str.upper()
df_final['nom_estado_fisico'] = df_final['nom_estado_fisico'].str.upper()
df_final['nom_dia_semana'] = df_final['nom_dia_semana'].str.upper()
df_final['nom_uf'] = df_final['nom_uf'].str.upper()
df_final['nom_tracado_via'] = df_final['nom_tracado_via'].str.upper()
df_final['nom_condicao_meteorologica'] = df_final['nom_condicao_meteorologica'].str.upper()
df_final['nom_tipo_pista'] = df_final['nom_tipo_pista'].str.upper()

# 1. Definimos o Schema (convertendo para minúsculo para garantir compatibilidade)
# 1. SCHEMA EXATO do seu CREATE TABLE (33 colunas)
SCHEMA_FINAL = [
    'id_ocorrencia', 'dat_data', 'nom_dia_semana', 'num_horario', 'nom_uf',
    'num_br', 'num_km', 'nom_municipio', 'des_causa_principal', 'des_causa_acidente',
    'des_tipo_acidente', 'des_classificacao_acidente', 'nom_fase_dia', 'nom_sentido_via',
    'nom_condicao_meteorologica', 'nom_tipo_pista', 'nom_tracado_via', 'nom_uso_solo',
    'cod_veiculo', 'nom_tipo_veiculo', 'nom_marca_veiculo', 'nom_tipo_envolvido', 'num_ano_fabricacao',
    'nom_estado_fisico', 'num_idade', 'nom_sexo', 'ind_faixa_etaria',  'qtd_ilesos', 'qtd_feridos_leves',
    'qtd_feridos_graves', 'qtd_mortos', 'vlr_latitude', 'vlr_longitude'
]

# 2. Padroniza as colunas do DataFrame para minúsculo
df_final.columns = [c.lower() for c in df_final.columns]

# 3. Filtra o DataFrame garantindo apenas as colunas que a tabela possui
# Se alguma coluna do schema faltar no DF, o código avisa em vez de quebrar
colunas_disponiveis = [c for c in SCHEMA_FINAL if c in df_final.columns]
df_final = df_final[colunas_disponiveis]

print(f"Colunas prontas para carga: {len(df_final.columns)} de 33 esperadas.")

print("Colunas ordenadas no DataFrame:")
print(df_final.columns.tolist())


# 3. Agora chama a carga com o df_final reordenado
# ingest_to_iceberg(
#     df=df_final, 
#     database=database_silver, 
#     table=tabela_silver, 
#     s3_path=f"{s3_path}/{tabela_silver}",
#     partition_cols=["nom_uf"]
# )
#carregar_csvs_para_dataframedef 
ingest_dataframe_to_s3_parquet(
    df_final, 
    db_destino, 
    tb_destino, 
    s3_path, 
    partition_cols=None, 
    mode="overwrite_partitions",
    description=None)



# print(f'Carregando dados na tabela final {database_silver}.{tabela_silver}')
# df = ingest_to_iceberg(
#             df=df_final,
#             database=database_silver,
#             table=tabela_silver,
#             s3_path=f'{s3_path}/{tabela_silver}',
#             merge_cols=["ID_OCORRENCIA"],      # A chave primária para o Merge
#             partition_cols=["NOM_UF"]   # Particionando por UF para performance no Athena
#         )
# Chamada CORRETA para a função minimalista
print(f'Carregando dados na tabela final {db_destino}.{tb_destino}')

executar_glue_job("glue_processar_gold")