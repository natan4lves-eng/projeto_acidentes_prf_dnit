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
    partition_cols=["nom_uf"],
    merge_cols=['id_localizacao'] # <- O Iceberg vai olhar esse ID. Se existir, ele atualiza a linha inteira. Se não existir, ele insere.
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

df_dim_tempo['id_tempo'] = df_dim_tempo['id_tempo'].astype('Int64')

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
    partition_cols=None,
    merge_cols=['id_tempo'] # <- O Iceberg vai olhar esse ID. Se existir, ele atualiza a linha inteira. Se não existir, ele insere.
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
    partition_cols=None,
    merge_cols=['id_clima'] # <- O Iceberg vai olhar esse ID. Se existir, ele atualiza a linha inteira. Se não existir, ele insere.
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
df_dim_causa_acidente['id_causa_acidente'] = df_dim_causa_acidente['id_causa_acidente'].astype('Int64')

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
    partition_cols=None,
    merge_cols=['id_causa_acidente'] # <- O Iceberg vai olhar esse ID. Se existir, ele atualiza a linha inteira. Se não existir, ele insere.
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
    partition_cols=None,
    merge_cols=['id_pessoa'] # <- O Iceberg vai olhar esse ID. Se existir, ele atualiza a linha inteira. Se não existir, ele insere.
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
    partition_cols=None,
    merge_cols=['id_veiculo'] # <- O Iceberg vai olhar esse ID. Se existir, ele atualiza a linha inteira. Se não existir, ele insere.
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
    'des_causa_acidente': 'first',         
    'des_tipo_acidente': 'first',          
    'des_classificacao_acidente': 'first', 
    'nom_estado_fisico': 'first',          
    'qtd_ilesos': 'sum',
    'qtd_feridos_leves': 'sum',
    'qtd_feridos_graves': 'sum',
    'qtd_mortos': 'sum'
}).reset_index()


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
print("Colunas da Fato: ", df_fato_acidente.columns.tolist())
print("Colunas da Dimensão acidente: ", df_dim_causa_acidente.columns.tolist())                            
# df_fato_acidente = pd.merge(df_fato_acidente, df_dim_causa_acidente, 
#                             left_on=['des_tipo_acidente', 'des_classificacao_acidente', 'nom_estado_fisico'], 
#                             right_on=['des_tipo_acidente', 'des_classificacao_acidente', 'nom_estado_fisico'], how='left')

# 2. Faz o Merge para buscar o ID na Dimensão usando as colunas de texto
df_fato_acidente = pd.merge(
    df_fato_acidente, 
    df_dim_causa_acidente,
    on=['des_causa_acidente', 'des_tipo_acidente', 'des_classificacao_acidente', 'nom_estado_fisico'], # ou as chaves que estiver usando
    how='left'
)
df_fato_acidente['id_causa_acidente'] = df_fato_acidente['id_causa_acidente'].astype('Int64')
# # 3. AGORA SIM! Depois que o 'id_causa_acidente' já está dentro da Fato, 
# # você apaga os textos pesados para a Fato ficar só com números e IDs.
# df_fato_acidente = df_fato_acidente.drop(columns=[
#     'des_causa_acidente', 
#     'des_tipo_acidente', 
#     'des_classificacao_acidente', 
#     'nom_estado_fisico'
# ])


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
df_fato_acidente['id_ocorrencia'] = df_fato_acidente['id_ocorrencia'].astype('Int64')
# C. Limpeza e Seleção Final (Garantindo apenas o que vai para a Fato)
# Mantemos o id_ocorrencia para o MERGE do Iceberg
cols_finais = ['id_acidente', 'id_tempo', 'id_localizacao', 'id_clima', 'id_causa_acidente', 'id_ocorrencia', 'qtd_total_pessoas_acidente',
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
    partition_cols=None,
    merge_cols=['id_acidente'] # <- O Iceberg vai olhar esse ID. Se existir, ele atualiza a linha inteira. Se não existir, ele insere.
)



# ==========================================
# CARGA 2: FATO_ENVOLVIDOS (Grão: Pessoa/Veículo)
# ==========================================
print('Iniciando carga da Fato Envolvidos...')

# 1. Preparação da Staging (Cópia dos dados brutos com as colunas necessárias)
# Diferente da Fato Acidentes, aqui NÃO usamos groupby
df_fato_env = df_origem.copy()
print(df_fato_env.columns.tolist())

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
print("Colunas após join com Dim Veículo: ", df_fato_env.columns.tolist())

# Join com Dimensão Pessoa (cruzando por TODAS as características do grão)
df_fato_env = pd.merge(
    df_fato_env, 
    df_dim_pessoa, 
    on=['nom_sexo', 'num_idade', 'ind_faixa_etaria', 'nom_tipo_envolvido'], 
    how='left'
)

# 2. SANEAMENTO DE TIPOS (Evita o erro de "merge on object and datetime64")
df_fato_env['dat_data'] = pd.to_datetime(df_fato_env['dat_data'])
df_dim_tempo['dat_data'] = pd.to_datetime(df_dim_tempo['dat_data'])

# Na Fato Envolvidos, a data geralmente vem direto da Staging (df_origem)
df_fato_env = pd.merge(
    df_fato_env, 
    df_dim_tempo, 
    left_on=['dat_data', 'num_horario'], 
    right_on=['dat_data', 'num_horario'], 
    how='left'
)

print(df_fato_env.head(5))
print(df_fato_env.columns.tolist())

# 4. CRIAÇÃO DE MÉTRICAS ANALÍTICAS PARA O BI

# A. Métrica de Contagem Base
df_fato_env['qtd_envolvido'] = 1

# B. Métricas Booleanas de Estado Físico (Baseado na PRF)
# Usamos .apply para criar as flags de soma rápida
df_fato_env['ind_obito'] = df_fato_env['nom_estado_fisico'].apply(lambda x: 1 if x in ['Óbito', 'Morto'] else 0)
df_fato_env['ind_ferido'] = df_fato_env['nom_estado_fisico'].apply(lambda x: 1 if x in ['Ferido Leve', 'Ferido Grave'] else 0)
df_fato_env['ind_ileso'] = df_fato_env['nom_estado_fisico'].apply(lambda x: 1 if x == 'Ileso' else 0)

# C. Métrica Avançada: Score de Gravidade da Vítima
def calcular_score_vitima(estado):
    pesos = {
        'Ileso': 0, 
        'Não Informado': 0,
        'Ferido Leve': 1, 
        'Ferido Grave': 3, 
        'Óbito': 10,
        'Morto': 10
    }
    return pesos.get(estado, 0) # Se vier um status bizarro, o peso é 0

df_fato_env['vlr_score_gravidade'] = df_fato_env['nom_estado_fisico'].apply(calcular_score_vitima)


# C. Nova: Indicador Geral de Vítima (Qualquer pessoa que não saiu ilesa)
df_fato_env['ind_vitima'] = df_fato_env['nom_estado_fisico'].apply(
    lambda x: 1 if x in ['Óbito', 'Morto', 'Ferido Leve', 'Ferido Grave'] else 0
)

# D. Nova: Indicador de Condutor (Métrica de conveniência para taxas)
df_fato_env['ind_condutor'] = df_fato_env['nom_tipo_envolvido'].apply(
    lambda x: 1 if x == 'Condutor' else 0
)


# F. Score de Gravidade da Vítima (Peso analítico)
def calcular_score_vitima(estado):
    pesos = {
        'Ileso': 0, 
        'Não Informado': 0,
        'Ferido Leve': 1, 
        'Ferido Grave': 3, 
        'Óbito': 10,
        'Morto': 10
    }
    return pesos.get(estado, 0)

df_fato_env['vlr_score_gravidade'] = df_fato_env['nom_estado_fisico'].apply(calcular_score_vitima)

df_fato_env = adicionar_id_unico(df_fato_env, nome_coluna="id_envolvido")
df_fato_env['id_ocorrencia'] = df_fato_env['id_ocorrencia'].astype('Int64')
df_fato_env['id_veiculo'] = df_fato_env['id_veiculo'].astype('Int64')
# 5. LIMPEZA E SELEÇÃO FINAL
# Mantemos apenas os IDs e a métrica, descartando os textos (sexo, idade, etc)
cols_finais_env = [
    'id_envolvido', 
    'id_veiculo', 
    'id_tempo', 
    'id_pessoa',
    'id_ocorrencia',
    'qtd_envolvido',
    'ind_vitima',
    'ind_obito',
    'ind_ferido',
    'ind_ileso',
    'ind_condutor',
    'vlr_score_gravidade'
]

# Filtramos apenas as colunas desejadas
df_fato_env = df_fato_env[cols_finais_env]

print('Colunas finais da carga da Fato Envolvidos:')
print(df_fato_env.columns.tolist())
print('Junção concluída. Preparando para enviar ao Iceberg...')

# 6. ESCRITA NO ICEBERG

print(f'Carregando dados na tabela final {database_destino}.{tabela_destino_08}')

# Agora a chamada da carga usa df_fato_env e aponta para a tabela 08
ingest_to_iceberg(
    df=df_fato_env, 
    database=database_destino, 
    table=tabela_destino_08, 
    s3_path=f"{s3_path}/{tabela_destino_08}",
    partition_cols=None,
    merge_cols=['id_envolvido'] # Atualiza a linha se o envolvido já existir, senão insere
)

print('Carga da Fato Envolvidos concluída com sucesso!')
