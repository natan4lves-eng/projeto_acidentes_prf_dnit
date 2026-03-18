# Importa as funções que criámos no ficheiro utils.py
import numpy as np
import pandas as pd
import awswrangler as wr

print(f"Versão NumPy: {np.__version__}")
print(f"Versão Pandas: {pd.__version__}")
print(f"Versão Wrangler: {wr.__version__}")
from utils import limpar_dados, rename_columns, realizar_merge_limpo, padronizar_campos_join, select_columns, normalizar_colunas, alterar_tipos,read_table, ingest_dataframe_to_s3_parquet, ingest_to_iceberg, executar_glue_job


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
database_silver = args['db_destino']
tabela_silver   = args['tb_destino']
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

# Dicionário de mapeamento
mapping = {

    # =========================
    # DIM_ESTRADA
    # =========================
    "id": "ID_OCORRENCIA",
    "sentido_via": "NOM_SENTIDO_VIA",
    "tipo_pista": "NOM_TIPO_PISTA",
    "tracado_via": "NOM_TRACADO_VIA",

    # =========================
    # DIM_LOCAL
    # =========================
    "uf": "NOM_UF",
    "br": "NUM_BR",
    "km": "NUM_KM",
    "municipio": "NOM_MUNICIPIO",
    "latitude": "VLR_LATITUDE",
    "longitude": "VLR_LONGITUDE",
    "uso_solo": "NOM_USO_SOLO",

    # =========================
    # DIM_TEMPO
    # =========================
    "fase_dia": "NOM_FASE_DIA",
    "dia_semana": "NOM_DIA_SEMANA",
    "horario": "NUM_HORARIO",
    "data_inversa": "DAT_DATA",

    # =========================
    # DIM_PESSOA
    # =========================
    "idade": "NUM_IDADE",
    "sexo": "NOM_SEXO",
    "tipo_envolvido": "NOM_TIPO_ENVOLVIDO",
    "estado_fisico": "NOM_ESTADO_FISICO",

    # =========================
    # DIM_CLIMA
    # =========================
    "condicao_metereologica": "NOM_CONDICAO_METEOROLOGICA",

    # =========================
    # DIM_GRAVIDADE_OCORRENCIA
    # =========================
    "ordem_tipo_acidente": "NUM_ORDEM_TIPO_ACIDENTE",
    "causa_principal": "DES_CAUSA_PRINCIPAL",
    "causa_acidente": "DES_CAUSA_ACIDENTE",
    "tipo_acidente": "DES_TIPO_ACIDENTE",
    "classificacao_acidente": "DES_CLASSIFICACAO_ACIDENTE",
    "ilesos": "QTD_ILESOS",
    "feridos_leves": "QTD_FERIDOS_LEVES",
    "feridos_graves": "QTD_FERIDOS_GRAVES",
    "mortos": "QTD_MORTOS",

    # =========================
    # DIM_VEICULO
    # =========================
    "id_veiculo": "COD_VEICULO",
    "tipo_veiculo": "NOM_TIPO_VEICULO",
    "marca": "NOM_MARCA_VEICULO",
    "ano_fabricacao_veiculo": "NUM_ANO_FABRICACAO"
}

# Aplicar a renomeação no DataFrame

df_detran_limpo = rename_columns(df_detran_limpo, mapping=mapping)

# Visualizar as colunas renomeadas
print(df_detran_limpo.columns.tolist())



# Exemplo: "2.8" -> "2"
df_detran_limpo['NUM_BR'] = df_detran_limpo['NUM_BR'].astype(str).str.split('.').str[0]
# Exemplo: "2.8" -> "2"
df_detran_limpo['NUM_KM'] = df_detran_limpo['NUM_KM'].astype(str).str.split(',').str[0]
df_detran_limpo['NUM_IDADE'] = df_detran_limpo['NUM_IDADE'].astype(str).str.split('.').str[0]
df_detran_limpo['ID_OCORRENCIA'] = df_detran_limpo['ID_OCORRENCIA'].astype(str).str.split('.').str[0]
df_detran_limpo['COD_VEICULO'] = df_detran_limpo['COD_VEICULO'].astype(str).str.split('.').str[0]
df_detran_limpo['QTD_ILESOS'] = df_detran_limpo['QTD_ILESOS'].astype(str).str.split('.').str[0]
df_detran_limpo['QTD_FERIDOS_LEVES'] = df_detran_limpo['QTD_FERIDOS_LEVES'].astype(str).str.split('.').str[0]
df_detran_limpo['QTD_FERIDOS_GRAVES'] = df_detran_limpo['QTD_FERIDOS_GRAVES'].astype(str).str.split('.').str[0]
df_detran_limpo['QTD_MORTOS'] = df_detran_limpo['QTD_MORTOS'].astype(str).str.split('.').str[0]
df_detran_limpo['NUM_ANO_FABRICACAO'] = df_detran_limpo['NUM_ANO_FABRICACAO'].astype(str).str.split('.').str[0]


# Dicionário com os tipos de dados desejados
tipos = {
    'ID_OCORRENCIA': 'int',
    'DAT_DATA': 'date',
    'NOM_DIA_SEMANA': 'str',
    'NUM_HORARIO': 'str',
    'NOM_UF': 'str',
    'NUM_BR': 'int',
    'NUM_KM': 'int',
    'NOM_MUNICIPIO': 'str',
    'DES_CAUSA_PRINCIPAL': 'str',
    'DES_CAUSA_ACIDENTE': 'str',
    'DES_TIPO_ACIDENTE': 'str',
    'DES_CLASSIFICACAO_ACIDENTE': 'str',
    'NOM_FASE_DIA': 'str',
    'NOM_SENTIDO_VIA': 'str',
    'NOM_CONDICAO_METEOROLOGICA': 'str',
    'NOM_TIPO_PISTA': 'str',
    'NOM_TRACADO_VIA': 'str',
    'NOM_USO_SOLO': 'str',
    'COD_VEICULO': 'int',
    'NOM_TIPO_VEICULO': 'str',
    'NOM_MARCA_VEICULO': 'str',
    'NOM_TIPO_ENVOLVIDO': 'str',
    'NUM_ANO_FABRICACAO': 'int',
    'NOM_ESTADO_FISICO': 'str',
    'NUM_IDADE': 'int',
    'NOM_SEXO': 'str',
    'QTD_ILESOS': 'int',
    'QTD_FERIDOS_LEVES': 'int',
    'QTD_FERIDOS_GRAVES': 'int',
    'QTD_MORTOS': 'int',
    'VLR_LATITUDE': 'double',
    'VLR_LONGITUDE': 'double',
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

# Chamar a função
df_final = alterar_tipos(df_detran_limpo, tipos)

# Exibir o DataFrame resultante
print(df_final.dtypes)
# print(df_detran_limpo)
# print(df_detran_limpo.dtypes)

df_final["NOM_SEXO"] = df_final["NOM_SEXO"].str.strip()

df_final.loc[
    ~df_final["NOM_SEXO"].isin(["Masculino", "Feminino"]),
    "NOM_SEXO"
] = "Não Informado"

df_final["NUM_IDADE"] = (
    df_final["NUM_IDADE"]
        .astype(str)      # garante que tudo vire string
        .str.strip()      # remove espaços
        .replace("", "-1") # vazio → -1
        .fillna("-1")     # null → -1
        .astype(int)      # converte para inteiro
)

# regra: idade > 99 vira -1
df_final.loc[df_final["NUM_IDADE"] > 99, "NUM_IDADE"] = -1

import numpy as np

df_final["IND_FAIXA_ETARIA"] = np.select(
    [
        df_final["NUM_IDADE"] < 0,
        df_final["NUM_IDADE"] < 18,
        df_final["NUM_IDADE"] <= 22,
        df_final["NUM_IDADE"] <= 26,
        df_final["NUM_IDADE"] <= 30,
        df_final["NUM_IDADE"] <= 34,
        df_final["NUM_IDADE"] <= 38,
        df_final["NUM_IDADE"] <= 42,
        df_final["NUM_IDADE"] <= 46,
        df_final["NUM_IDADE"] <= 52,
        df_final["NUM_IDADE"] <= 56,
        df_final["NUM_IDADE"] <= 60
    ],
    [
        "N/I",
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

df_final["NOM_TIPO_ENVOLVIDO"] = (
    df_final["NOM_TIPO_ENVOLVIDO"]
    .astype(str)
    .str.strip()
    .replace("", "Não Informado")
    .replace("nan", "Não Informado")
)

#-- tratamento clima --
df_final["NOM_CONDICAO_METEOROLOGICA"] = df_final["NOM_CONDICAO_METEOROLOGICA"].str.strip()
df_final["NOM_CONDICAO_METEOROLOGICA"] = (
    df_final["NOM_CONDICAO_METEOROLOGICA"]
    .astype(str)
    .replace("Ignorado", "Não Informado")
)

df_final["NUM_ANO_FABRICACAO"] = (
    df_final["NUM_ANO_FABRICACAO"]
    .astype(str)
    .str.strip()
    .str[:4]   # mantém apenas os 4 primeiros caracteres
)

df_final["NUM_ANO_FABRICACAO"] = (
    pd.to_numeric(
        df_final["NUM_ANO_FABRICACAO"],
        errors="coerce"
    )
    .fillna(-1)
)

df_final.loc[
    df_final["NUM_ANO_FABRICACAO"] <= 1500,
    "NUM_ANO_FABRICACAO"
] = -1

df_final["NUM_ANO_FABRICACAO"] = df_final["NUM_ANO_FABRICACAO"].astype(int)



print("===== df_final =====")
print(df_final.head(5))
print(df_final.columns.tolist())

# 1. Definimos o Schema (convertendo para minúsculo para garantir compatibilidade)
# 1. SCHEMA EXATO do seu CREATE TABLE (31 colunas)
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

print(f"Colunas prontas para carga: {len(df_final.columns)} de 31 esperadas.")

print("Colunas ordenadas no DataFrame:")
print(df_final.columns.tolist())


# 3. Agora chama a carga com o df_final reordenado
ingest_to_iceberg(
    df=df_final, 
    database=database_silver, 
    table=tabela_silver, 
    s3_path=f"{s3_path}/{tabela_silver}",
    partition_cols=["nom_uf"]
)



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
print(f'Carregando dados na tabela final {database_silver}.{tabela_silver}')

executar_glue_job("glue_processar_gold")