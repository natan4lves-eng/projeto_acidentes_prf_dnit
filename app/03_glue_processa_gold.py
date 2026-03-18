# Importa as funções que criámos no ficheiro utils.py
import numpy as np
import pandas as pd
import awswrangler as wr

print(f"Versão NumPy: {np.__version__}")
print(f"Versão Pandas: {pd.__version__}")
print(f"Versão Wrangler: {wr.__version__}")
from utils import limpar_dados, rename_columns, realizar_merge_limpo, padronizar_campos_join, select_columns, normalizar_colunas, alterar_tipos,read_table, ingest_dataframe_to_s3_parquet, ingest_to_iceberg, agrupar_dataframe, adicionar_id_unico


import sys
from awsglue.utils import getResolvedOptions

# Liste exatamente os nomes das chaves que você colocou no Glue (sem o --)
params = [
    'db_origem',
    'tb_origem',
    'db_destino',
    'tabela_destino_01',
    'tabela_destino_02',
    'tabela_destino_03',
    'tabela_destino_04',
    'tabela_destino_05',
    'tabela_destino_06',
    'tabela_destino_07',
    'tabela_destino_08',
    's3_path'
]

# O getResolvedOptions transforma os parâmetros em um dicionário Python
args = getResolvedOptions(sys.argv, params)

# Atribuindo a variáveis para usar no seu código
database_origem = args['db_origem']
tabela_origem   = args['tb_origem']
database_destino = args['db_destino']
tabela_destino_01   = args['tabela_destino_01']
tabela_destino_02   = args['tabela_destino_02']
tabela_destino_03   = args['tabela_destino_03']
tabela_destino_04   = args['tabela_destino_04']
tabela_destino_05   = args['tabela_destino_05']
tabela_destino_06   = args['tabela_destino_06']
tabela_destino_07   = args['tabela_destino_07']
tabela_destino_08   = args['tabela_destino_08']
s3_path         = args['s3_path']


# Exemplo de log para confirmar se os valores chegaram
print(f"Origem: {database_origem}.{tabela_origem}")


df_origem = read_table(
    database=database_origem, 
    table=tabela_origem, 
    ctas_approach=True
)

print("dados da tb_bronze_prf_ocorrencia")
print(df_origem.columns.tolist())
print(df_origem.head(5))

#------------- DIM LOCALIZACAO ------------- 
DIM_LOCALIZACAO = [
 'nom_uf',
 'num_br',
 'num_km',
 'nom_municipio',
 'vlr_latitude',
 'vlr_longitude',
 'nom_uso_solo',
 ]
df_dim_localizacao = select_columns(df_origem, DIM_LOCALIZACAO)
df_dim_localizacao = agrupar_dataframe(df_dim_localizacao, DIM_LOCALIZACAO)
df_dim_localizacao = adicionar_id_unico(df_dim_localizacao, nome_coluna="id_localizacao")


print("===== df_final =====")
print(df_dim_localizacao.head(5))
print(df_dim_localizacao.columns.tolist())

# Chamada CORRETA para a função minimalista
print(f'Carregando dados na tabela final {database_destino}.{tabela_destino_01}')

# 3. Agora chama a carga com o df_final reordenado
ingest_to_iceberg(
    df=df_dim_localizacao, 
    database=database_destino, 
    table=tabela_destino_01, 
    s3_path=f"{s3_path}/{tabela_destino_01}",
    partition_cols=["nom_uf"]
)



#------------- DIM TEMPO ------------- 
DIM_TEMPO = [
 'nom_dia_semana',
 'num_horario',
 'nom_fase_dia',
 'dat_data'

 ]
df_dim_tempo = select_columns(df_origem, DIM_TEMPO)
df_dim_tempo = agrupar_dataframe(df_dim_tempo, DIM_TEMPO)
df_dim_tempo = adicionar_id_unico(df_dim_tempo, nome_coluna="id_tempo")

# Chamada CORRETA para a função minimalista
print(f'Carregando dados na tabela final {database_destino}.{tabela_destino_02}')
print("===== df_final =====")
print(df_dim_tempo.head(5))
print(df_dim_tempo.columns.tolist())


# 3. Agora chama a carga com o df_final reordenado
ingest_to_iceberg(
    df=df_dim_tempo, 
    database=database_destino, 
    table=tabela_destino_02, 
    s3_path=f"{s3_path}/{tabela_destino_02}",
    partition_cols=None
)

#------------- DIM CLIMA ------------- 
DIM_CLIMA = [
    'nom_condicao_meteorologica'
 ]
df_dim_clima = select_columns(df_origem, DIM_CLIMA)
df_dim_clima = agrupar_dataframe(df_dim_clima, DIM_CLIMA)
df_dim_clima = adicionar_id_unico(df_dim_clima, nome_coluna="id_clima")

print("===== df_final =====")
print(df_dim_clima.head(5))
print(df_dim_clima.columns.tolist())

# Chamada CORRETA para a função minimalista
print(f'Carregando dados na tabela final {database_destino}.{tabela_destino_03}')

# 3. Agora chama a carga com o df_final reordenado
ingest_to_iceberg(
    df=df_dim_clima, 
    database=database_destino, 
    table=tabela_destino_03, 
    s3_path=f"{s3_path}/{tabela_destino_03}",
    partition_cols=None
)



#------------- DIM CAUSA ACIDENTE ------------- 
DIM_CAUSA_ACIDENTE = [
 'des_causa_acidente',
 'des_tipo_acidente',
 'des_classificacao_acidente',
 'nom_estado_fisico'
 ]
df_dim_causa_acidente = select_columns(df_origem, DIM_CAUSA_ACIDENTE)
df_dim_causa_acidente = agrupar_dataframe(df_dim_causa_acidente, DIM_CAUSA_ACIDENTE)
df_dim_causa_acidente = adicionar_id_unico(df_dim_causa_acidente, nome_coluna="id_causa_acidente")

# Chamada CORRETA para a função minimalista
print(f'Carregando dados na tabela final {database_destino}.{tabela_destino_04}')
print(df_dim_causa_acidente.head(5))
print(df_dim_causa_acidente.columns.tolist())

# 3. Agora chama a carga com o df_final reordenado
ingest_to_iceberg(
    df=df_dim_causa_acidente, 
    database=database_destino, 
    table=tabela_destino_04, 
    s3_path=f"{s3_path}/{tabela_destino_04}",
    partition_cols=None
)


#------------- DIM PESSOA ------------- 
DIM_PESSOA = [
    'nom_sexo',
    'num_idade',
    'ind_faixa_etaria',
    'nom_tipo_envolvido'
 ]
df_dim_pessoa = select_columns(df_origem, DIM_PESSOA)
df_dim_pessoa = agrupar_dataframe(df_dim_pessoa, DIM_PESSOA)
df_dim_pessoa = adicionar_id_unico(df_dim_pessoa, nome_coluna="id_pessoa")

# Chamada CORRETA para a função minimalista
print(f'Carregando dados na tabela final {database_destino}.{tabela_destino_05}')


print(df_dim_pessoa.head(5))
print(df_dim_pessoa.columns.tolist())

# 3. Agora chama a carga com o df_final reordenado
ingest_to_iceberg(
    df=df_dim_pessoa, 
    database=database_destino, 
    table=tabela_destino_05, 
    s3_path=f"{s3_path}/{tabela_destino_05}",
    partition_cols=None
)

#------------- DIM VEICULO ------------- 
DIM_VEICULO = [
    "cod_veiculo",
    "nom_tipo_veiculo",
    "nom_marca_veiculo",
    "num_ano_fabricacao"
 ]
df_dim_veiculo = select_columns(df_origem, DIM_VEICULO)
df_dim_veiculo = agrupar_dataframe(df_dim_veiculo, DIM_VEICULO)
df_dim_veiculo = adicionar_id_unico(df_dim_veiculo, nome_coluna="id_veiculo")

# Chamada CORRETA para a função minimalista
print(f'Carregando dados na tabela final {database_destino}.{tabela_destino_06}')
print(df_dim_veiculo.head(5))
print(df_dim_veiculo.columns.tolist())

# 3. Agora chama a carga com o df_final reordenado
ingest_to_iceberg(
    df=df_dim_veiculo, 
    database=database_destino, 
    table=tabela_destino_06, 
    s3_path=f"{s3_path}/{tabela_destino_06}",
    partition_cols=None
)

# ==========================================
# CARGA 1: FATO_ACIDENTES (Grão: Ocorrência)
# ==========================================
df_stg = df_origem.copy()

print('Iniciando carga da Fato')

# A. Agrupamos PRIMEIRO para garantir 1 linha por ID_OCORRENCIA
# Note que incluímos as colunas que usaremos para o Join no 'first'
df_fato_acidente = df_stg.groupby('id_ocorrencia').agg({
    'dat_data': 'first',
    'num_horario': 'first',
    'vlr_latitude': 'first',
    'vlr_longitude': 'first',
    'nom_condicao_meteorologica': 'first',
    'qtd_ilesos': 'sum',
    'qtd_feridos_leves': 'sum',
    'qtd_feridos_graves': 'sum',
    'qtd_mortos': 'sum'
}).reset_index()

print(df_dim_veiculo.head(5))
print(df_dim_veiculo.columns.tolist())

print('Agrupamento das métricas concluído')

# 2. SANEAMENTO DE TIPOS (Evita o erro de "merge on object and datetime64")
df_fato_acidente['dat_data'] = pd.to_datetime(df_stg['dat_data'])
df_dim_tempo['dat_data'] = pd.to_datetime(df_dim_tempo['dat_data'])

# B. Joins para buscar as SKs (Agora usamos o DF já agrupado)
# Correção da sintaxe: as listas [col1, col2] são obrigatórias
df_fato_acidente = pd.merge(df_fato_acidente, df_dim_tempo, 
                            left_on=['dat_data', 'num_horario'], 
                            right_on=['dat_data', 'num_horario'], how='left')

df_fato_acidente = pd.merge(df_fato_acidente, df_dim_localizacao, 
                            left_on=['vlr_latitude', 'vlr_longitude'], 
                            right_on=['vlr_latitude', 'vlr_longitude'], how='left')

df_fato_acidente = pd.merge(df_fato_acidente, df_dim_clima, 
                            on='nom_condicao_meteorologica', how='left')
                            
# df_fato_acidente = pd.merge(df_fato_acidente, df_dim_causa_acidente, 
#                             left_on=['des_tipo_acidente', 'des_classificacao_acidente', 'nom_estado_fisico'], 
#                             right_on=['des_tipo_acidente', 'des_classificacao_acidente', 'nom_estado_fisico'], how='left')


print('Junção das Dimensões concluída')
print(df_dim_veiculo.head(5))
print(df_dim_veiculo.columns.tolist())

df_fato_acidente["qtd_total_pessoas_acidente"] = (
    df_fato_acidente[
        [
            "qtd_ilesos",
            "qtd_feridos_leves",
            "qtd_feridos_graves",
            "qtd_mortos"
        ]
    ]
    .fillna(0)
    .sum(axis=1)
    .astype("int32")   # equivalente a BIGINT
)

df_fato_acidente = adicionar_id_unico(df_fato_acidente, nome_coluna="id_acidente")
# C. Limpeza e Seleção Final (Garantindo apenas o que vai para a Fato)
# Mantemos o id_ocorrencia para o MERGE do Iceberg
cols_finais = ['id_acidente', 'id_tempo', 'id_localizacao', 'id_clima', 'qtd_total_pessoas_acidente',
                'qtd_ilesos', 'qtd_feridos_leves', 'qtd_feridos_graves', 'qtd_mortos']

df_fato_acidente = df_fato_acidente[cols_finais]


# df_fato_acidente = df_fato_acidente["id_tempo"].astype("int64")

print('--- RESULTADO FINAL DA FATO ---')
print(df_fato_acidente.head(10))

# # D. Escrita no Iceberg (O 'merge' garante que não duplica se rodar de novo)
# wr.athena.to_iceberg(
#     df=df_fato_acidente, database=DB, table="fato_acidentes",
#     temp_path=S3_TEMP, action="merge", merge_cols=["id_ocorrencia"]
# )


# 3. Agora chama a carga com o df_final reordenado
ingest_to_iceberg(
    df=df_fato_acidente, 
    database=database_destino, 
    table=tabela_destino_07, 
    s3_path=f"{s3_path}/{tabela_destino_07}",
    partition_cols=None
)



# ==========================================
# CARGA 2: FATO_ENVOLVIDOS (Grão: Pessoa/Veículo)
# ==========================================

print('Iniciando carga da Fato Envolvidos...')

# 1. Preparação da Staging (Cópia dos dados brutos com as colunas necessárias)
# Diferente da Fato Acidentes, aqui NÃO usamos groupby
df_fato_env = df_origem.copy()

# 2. Saneamento de Tipos para o Join
# Garantimos que as colunas de cruzamento sejam do mesmo tipo que nas Dimensões
df_fato_env['nom_sexo'] = df_fato_env['nom_sexo'].astype(str)
df_fato_env['num_idade'] = pd.to_numeric(df_fato_env['num_idade'], errors='coerce').fillna(0).astype(int)
df_dim_pessoa['num_idade'] = pd.to_numeric(df_dim_pessoa['num_idade'], errors='coerce').fillna(0).astype(int)

# 3. JOINS para buscar as Surrogate Keys (IDs)
# Join com Dimensão Veículo
df_fato_env = pd.merge(
    df_fato_env, 
    df_dim_veiculo, 
    on='cod_veiculo', 
    how='left'
)

# Join com Dimensão Pessoa (cruzando por sexo e idade)
df_fato_env = pd.merge(
    df_fato_env, 
    df_dim_pessoa, 
    left_on=['nom_sexo', 'num_idade'], 
    right_on=['nom_sexo', 'num_idade'], 
    how='left'
)

# 2. SANEAMENTO DE TIPOS (Evita o erro de "merge on object and datetime64")
df_fato_env['dat_data'] = pd.to_datetime(df_fato_env['dat_data'])
df_dim_tempo['dat_data'] = pd.to_datetime(df_dim_tempo['dat_data'])
# Na Fato Envolvidos, a data geralmente vem direto da Staging (df_origem)
df_fato_env = pd.merge(df_fato_env, df_dim_tempo, 
                            left_on=['dat_data', 'num_horario'], 
                            right_on=['dat_data', 'num_horario'], how='left')

# 4. CRIAÇÃO DE MÉTRICAS INDIVIDUAIS
# Criamos um indicador numérico (flag) para facilitar somas no BI
# df_fato_env['ind_morto'] = df_fato_env['nom_estado_fisico'].apply(lambda x: 1 if x == 'Óbito' else 0)


# Criando métricas de perfil e comportamento
# df_fato_env['ind_passageiro'] = df_fato_env['nom_tipo_envolvido'].apply(lambda x: 1 if x == 'Passageiro' else 0)
# df_fato_env['ind_pedestre'] = df_fato_env['nom_tipo_envolvido'].apply(lambda x: 1 if x == 'Pedestre' else 0)
# df_fato_env['ind_idoso'] = df_fato_env['num_idade'].apply(lambda x: 1 if x <= 12 else 0)
# # 1. Métrica para Adolescente (Considerando a faixa comum de 12 a 17 anos)
# df_fato_env['ind_adolescente'] = df_fato_env['num_idade'].apply(lambda x: 1 if 12 <= x <= 17 else 0)
# # 2. Métrica para Adulto (Considerando a faixa de 18 a 59 anos)
# df_fato_env['ind_adulto'] = df_fato_env['num_idade'].apply(lambda x: 1 if 18 <= x <= 59 else 0)

# 3. Métrica para Idoso (Que você já possui)
# df_fato_env['ind_idoso'] = df_fato_env['num_idade'].apply(lambda x: 1 if x >= 60 else 0)

# # Métrica de Peso de Gravidade (Score)
# def calcular_score(estado):
#     pesos = {'Ileso': 1, 'Ferido Leve': 2, 'Ferido Grave': 5, 'Morto': 10}
#     return pesos.get(estado, 0)

# df_fato_env['vlr_score_risco'] = df_fato_env['nom_estado_fisico'].apply(calcular_score)


# # A. Agrupamos PRIMEIRO para garantir 1 linha por ID_OCORRENCIA
# # Note que incluímos as colunas que usaremos para o Join no 'first'
# df_fato_acidente = df_stg.groupby('id_ocorrencia').agg({
#     'ind_passageiro': 'sum',
#     'ind_pedestre': 'sum',
#     'ind_idoso': 'sum',
#     'ind_adolescente': 'sum',
#     'ind_adulto': 'sum',
#     'vlr_score_risco': 'sum'
# }).reset_index()

df_fato_env = adicionar_id_unico(df_fato_env, nome_coluna="id_env")

# 5. LIMPEZA E SELEÇÃO FINAL
# Mantemos apenas os IDs e a métrica, descartando os textos (sexo, idade, etc)
cols_finais_env = [
    'id_env', 
    'id_veiculo', 
    'id_tempo', # Assumindo que este é o nome do ID na dim_veiculo
    'id_pessoa'  # Assumindo que este é o nome do ID na dim_pessoa
    # 'ind_morto'
]

# Filtramos apenas as colunas desejadas
df_fato_env = df_fato_env[cols_finais_env]
# df_fato_acidente = df_fato_acidente["id_tempo"].astype("int64")
print('Junção concluída. Colunas finais da Fato Envolvidos:')
print(df_fato_env.columns.tolist())

# 6. ESCRITA NO ICEBERG

# 3. Agora chama a carga com o df_final reordenado
ingest_to_iceberg(
    df=df_fato_acidente, 
    database=database_destino, 
    table=tabela_destino_08, 
    s3_path=f"{s3_path}/{tabela_destino_08}",
    partition_cols=None
)

print('Carga da Fato Envolvidos concluída com sucesso!')
