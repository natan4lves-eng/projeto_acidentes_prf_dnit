# Importa as funções que criámos no ficheiro utils.py
import numpy as np
import pandas as pd
import awswrangler as wr

print(f"Versão NumPy: {np.__version__}")
print(f"Versão Pandas: {pd.__version__}")
print(f"Versão Wrangler: {wr.__version__}")
from utils import carregar_csvs_para_dataframe_s3, ingest_dataframe_to_s3_parquet, select_columns, normalizar_colunas, executar_glue_job


import sys
from awsglue.utils import getResolvedOptions

# Liste exatamente os nomes das chaves que você colocou no Glue (sem o --)
params = [
    'db_destino',
    'tb_destino',
    's3_path_origem',
    's3_path_destino'
]

# O getResolvedOptions transforma os parâmetros em um dicionário Python
args = getResolvedOptions(sys.argv, params)

# Atribuindo a variáveis para usar no seu código
db_destino = args['db_destino']
tb_destino   = args['tb_destino']
s3_path_origem         = args['s3_path_origem']
s3_path_destino         = args['s3_path_destino']

# Chama a função e guarda o resultado na variável 'df'
df_origem = carregar_csvs_para_dataframe_s3(s3_path_origem,0)

# Exibe as 5 primeiras linhas do DataFrame resultante (se não estiver vazio)
if not df_origem.empty:
    print("\nVisualização dos primeiros registos do df_origem:")
    print(df_origem.head())

print("dados da tb_bronze_prf_ocorrencia")
print(df_origem.columns.tolist())
print(df_origem.head(5))

#------------- NORMALIZA COLUNAS ------------- 
df_origem = normalizar_colunas(df_origem)
print(df_origem.columns.tolist())


SCHEMA_ORIGEM = [
    'id',
	'pesid',
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
    'longitude',
	'regional',
	'delegacia',
	'uop'
]
df_origem = select_columns(df_origem, SCHEMA_ORIGEM)
print(df_origem.columns.tolist())

#carregar_csvs_para_dataframedef 
ingest_dataframe_to_s3_parquet(
    df_origem, 
    db_destino, 
    tb_destino, 
    s3_path_destino, 
    partition_cols=None, 
    mode="overwrite_partitions",
    description=None)
    
executar_glue_job("glue_processar_silver")
