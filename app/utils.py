from matplotlib import table
import pandas as pd
import glob
import os
import unicodedata
import re

import boto3
import csv
from io import BytesIO



def carregar_csvs_para_dataframe_s3(caminho_s3, header):

    """
    Lê múltiplos CSV diretamente do S3.
    Exemplo caminho:
    s3://bucket/pasta/
    """

    # -----------------------------
    # separa bucket e prefixo
    # -----------------------------
    caminho_sem_prefixo = caminho_s3.replace("s3://", "")
    bucket = caminho_sem_prefixo.split("/")[0]
    prefixo = "/".join(caminho_sem_prefixo.split("/")[1:])

    s3 = boto3.client("s3")

    # -----------------------------
    # lista arquivos
    # -----------------------------
    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix=prefixo
    )

    if "Contents" not in response:
        print("Nenhum arquivo encontrado.")
        return pd.DataFrame()

    arquivos_csv = [
        obj["Key"]
        for obj in response["Contents"]
        if obj["Key"].endswith(".csv")
    ]

    print(f"Foram encontrados {len(arquivos_csv)} CSV(s) no S3.\n")

    lista_dataframes = []

    encodings_para_testar = [
        "utf-8-sig",
        "cp1252",
        "latin1",
        "utf-8"
    ]

    # -----------------------------
    # leitura dos arquivos
    # -----------------------------
    for key in arquivos_csv:

        print(f"Lendo: {key}")

        obj = s3.get_object(Bucket=bucket, Key=key)
        conteudo_bytes = obj["Body"].read()

        df_lido = None

        for encoding in encodings_para_testar:
            try:
                df_temp = pd.read_csv(
                    BytesIO(conteudo_bytes),
                    encoding=encoding,
                    sep=";",
                    header=header,
                    quotechar='"',
                    quoting=csv.QUOTE_MINIMAL,
                    engine="python",
                    skipinitialspace=True,
                    on_bad_lines="warn"
                )

                if df_temp.columns.astype(str).str.contains("Ã").any():
                    continue

                df_lido = df_temp
                print(f"Sucesso com encoding {encoding}")
                break

            except Exception:
                continue

        if df_lido is not None:
            df_lido["arquivo_origem"] = key.split("/")[-1]
            lista_dataframes.append(df_lido)
        else:
            print(f"Erro ao ler {key}")

    if lista_dataframes:
        df_final = pd.concat(lista_dataframes, ignore_index=True)

        print("\nResumo final:")
        print("Linhas:", len(df_final))
        print("Colunas:", len(df_final.columns))

        return df_final

    return pd.DataFrame()

import unicodedata
import re

def normalizar_colunas(df):

    # 1️⃣ remover colunas lixo do CSV
    df = df.loc[:, ~df.columns.str.contains('^Unnamed', case=False)]

    # 2️⃣ corrigir encoding quebrado (latin1 → utf8)
    df.columns = (
        df.columns
        .str.encode('latin1', errors='ignore')
        .str.decode('utf-8', errors='ignore')
    )

    # 3️⃣ remover BOM (ï»¿)
    df.columns = df.columns.str.replace('ï»¿', '', regex=False)

    # 4️⃣ função de normalização padrão DW
    def normalize(col):

        # remover acentos
        col = unicodedata.normalize('NFKD', col)\
            .encode('ascii', 'ignore')\
            .decode('utf-8')

        # lowercase
        col = col.lower()

        # espaços → _
        col = col.replace(' ', '_')

        # remove caracteres especiais
        col = re.sub(r'[^a-z0-9_]', '', col)

        # remove múltiplos _
        col = re.sub(r'_+', '_', col)

        return col.strip('_')

    df.columns = [normalize(c) for c in df.columns]

    return df

def select_columns(df, columns, verbose=True):
    """
    Mantém apenas as colunas desejadas em um DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame de entrada
    columns : list
        Lista de colunas desejadas (schema alvo)
    verbose : bool
        Mostra aviso de colunas faltantes

    Returns
    -------
    pandas.DataFrame
        DataFrame apenas com as colunas selecionadas
    """

    # colunas existentes
    existing_cols = [c for c in columns if c in df.columns]

    # colunas faltantes
    missing_cols = list(set(columns) - set(df.columns))

    if verbose and missing_cols:
        print(f"⚠️ Colunas não encontradas: {missing_cols}")

    # mantém ordem do schema
    df = df.loc[:, existing_cols]

    return df


def limpar_dados(df):
    """
    Removes empty and duplicate rows from the DataFrame.
    Considers a row empty if all original CSV columns are null.
    """
    print("\n--- A iniciar limpeza de dados ---")
    
    linhas_iniciais = len(df)
    
    # Define as colunas originais (ignora 'arquivo_origem' para a verificação de linhas vazias)
    colunas_originais = [col for col in df.columns if col != 'arquivo_origem']
    
    # 1. Remove as linhas onde TODAS as colunas originais são NaN (vazias)
    df_limpo = df.dropna(how='all', subset=colunas_originais)
    linhas_apos_vazias = len(df_limpo)
    print(f"Linhas vazias removidas: {linhas_iniciais - linhas_apos_vazias}")
    
    # 2. Remove as linhas duplicadas (mantém a primeira ocorrência)
    df_limpo = df_limpo.drop_duplicates()
    linhas_apos_duplicadas = len(df_limpo)
    print(f"Linhas duplicadas removidas: {linhas_apos_vazias - linhas_apos_duplicadas}")
    
    print(f"Total de linhas finais (após limpeza): {len(df_limpo)}")
    print("----------------------------------")
    
    return df_limpo




import pandas as pd

def padronizar_campos_join(df, coluna_data, lat_col="latitude", lon_col="longitude"):
    """
    Padroniza campos utilizados como chave de join:
    - converte datas para datetime
    - corrige latitude/longitude (vírgula decimal)
    - converte coordenadas para float
    - arredonda coordenadas para evitar problemas de precisão
    """

    # =========================
    # 1️⃣ Padronizar DATA
    # =========================
    df[coluna_data] = pd.to_datetime(
        df[coluna_data],
        errors="coerce",
        dayfirst=True  # funciona para 03/06/2022
    )

    # =========================
    # 2️⃣ Padronizar COORDENADAS
    # =========================
    for col in [lat_col, lon_col]:

        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(",", ".", regex=False)  # decimal BR → padrão
        )

        df[col] = pd.to_numeric(df[col], errors="coerce")

        # arredondamento (ESSENCIAL para join geográfico)
        df[col] = df[col].round(5)

    return df

import pandas as pd

def realizar_merge_limpo(df_left, df_right, keys_left, keys_right, how='left', verbose=True):
    """
    Realiza o merge e exibe a quantidade e porcentagem de sucesso (match).
    """
    df_l = df_left.copy()
    df_r = df_right.copy()

    # 1. Limpeza das chaves
    def limpar_chaves_join(df, colunas):
        for col in colunas:
            if any(x in col.lower() for x in ['km', 'br', 'num']):
                s = df[col].astype(str).str.replace('BR-', '', case=False).str.replace(',', '.')
                s = s.str.split('.').str[0]
                df[col] = pd.to_numeric(s, errors='coerce').astype('Int64')
        return df

    df_l = limpar_chaves_join(df_l, keys_left)
    df_r = limpar_chaves_join(df_r, keys_right)

    # 2. Execução do Merge
    df_resultado = df_l.merge(
        df_r,
        left_on=keys_left,
        right_on=keys_right,
        how=how,
        suffixes=('', '_join_r')
    )

    # 3. Cálculo de Estatísticas de Match
    if verbose:
        # Identificamos uma coluna que veio da direita para checar o match
        # Se a chave existe nos dois, ela terá o sufixo '_join_r'
        col_check = keys_right[0] + '_join_r'
        
        # Se por acaso a chave não tinha nome igual, pegamos qualquer coluna da direita
        if col_check not in df_resultado.columns:
            # Pega as colunas que estão no df_right mas não estavam no df_left original
            cols_exclusivas_r = [c for c in df_right.columns if c not in df_left.columns]
            col_check = cols_exclusivas_r[0] if cols_exclusivas_r else None

        if col_check:
            qtd_match = df_resultado[col_check].notna().sum()
            porcentagem_match = (qtd_match / len(df_resultado)) * 100
        else:
            qtd_match = "N/A"
            porcentagem_match = 0

        print(f"--- Relatório de Merge ---")
        print(f"✅ Merge concluído com sucesso!")
        print(f"📦 Total de linhas no resultado: {len(df_resultado)}")
        print(f"🤝 Quantidade de linhas com Match: {qtd_match}")
        print(f"📊 Porcentagem de Match: {porcentagem_match:.2f}%")
        print(f"--------------------------")
        
    return df_resultado

def rename_columns(df, mapping=None):
    """
    Renomeia colunas de um DataFrame aplicando um mapping opcional e/ou
    normalização canônica dos nomes de coluna.

    Parâmetros:
    df : pandas.DataFrame
        DataFrame de entrada (retorna cópia).
    mapping : dict, optional
        Dicionário old_name->new_name para renomeação direta.
    normalize : bool, optional
        Se True aplica normalização (strip, removes BOM, removes acentos, lowercase,
        substitui espaços por '_', remove caracteres especiais).
    
    Retorna:
    pandas.DataFrame
        Cópia do DataFrame com colunas renomeadas.
    """
    import unicodedata, re

    df_out = df.copy()

    # Aplica mapping se fornecido
    if mapping:
        df_out = df_out.rename(columns=mapping)


    return df_out

# Exemplo: df = rename_columns(df, mapping={'KM Inicial':'km_inicial'})


import os

def salvar_csv(df, caminho, nome_arquivo, separador=";"):
    """
    Salva um DataFrame em CSV.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame a ser salvo
    caminho : str
        Diretório destino
    nome_arquivo : str
        Nome do arquivo CSV
    separador : str
        Separador do CSV (default=';')
    """

    # cria pasta se não existir
    os.makedirs(caminho, exist_ok=True)

    # caminho completo
    caminho_completo = os.path.join(caminho, nome_arquivo)

    # salvar arquivo
    df.to_csv(
        caminho_completo,
        sep=separador,
        index=False,
        encoding="utf-8-sig"  # BOM para Excel reconhecer UTF-8 corretamente
    )

    print(f"✅ Arquivo salvo com sucesso em:\n{caminho_completo}")


def adicionar_id_unico(df, nome_coluna):
    """
    Adiciona uma coluna com IDs únicos incrementais a um DataFrame.

    Parâmetros:
    df : pandas.DataFrame
        DataFrame ao qual a coluna será adicionada.
    nome_coluna : str
        Nome da nova coluna (padrão: "id_unico").

    Retorna:
    pandas.DataFrame
        DataFrame com a nova coluna de IDs únicos.
    """
    df[nome_coluna] = range(len(df))
    return df

def agrupar_dataframe(df, colunas_agrupamento, operacoes_agregacao=None):
    """
    Realiza um agrupamento em um DataFrame com base em colunas especificadas e aplica operações de agregação, se fornecidas.

    Parâmetros:
    df : pandas.DataFrame
        DataFrame de entrada.
    colunas_agrupamento : list
        Lista de colunas para realizar o agrupamento.
    operacoes_agregacao : dict, optional
        Dicionário onde as chaves são os nomes das colunas e os valores são as funções de agregação a serem aplicadas.
        Se None, apenas realiza o agrupamento sem agregação.

    Retorna:
    pandas.DataFrame
        DataFrame resultante do agrupamento.
    """
    if operacoes_agregacao:
        df_agrupado = df.groupby(colunas_agrupamento).agg(operacoes_agregacao).reset_index()
    else:
        df_agrupado = df.groupby(colunas_agrupamento).size().reset_index()
        df_agrupado = df_agrupado.drop(columns=0)  # Remove a coluna extra gerada automaticamente
    return df_agrupado


import pandas as pd
import numpy as np
import pandas as pd
import numpy as np

import pandas as pd
import numpy as np

def alterar_tipos(df, tipos):
    if df.empty:
        return df

    # --- 1. Otimização de Encoding ---
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].astype(str).str.contains('Ã', na=False).any():
            df[col] = df[col].astype(str).apply(
                lambda x: x.encode('latin1').decode('utf-8', 'ignore') if 'Ã' in str(x) else x
            )

    # --- 2. Conversão de Tipos ---
    for coluna, tipo in tipos.items():
        if coluna not in df.columns:
            continue
            
        try:
            # --- TRATAMENTO PARA INTEIROS (INT32 para o Athena) ---
            if str(tipo).lower() in ['int', 'int32', 'integer']:
                s = df[coluna].astype(str).str.strip()
                s = s.str.replace('BR-', '', case=False, regex=False)
                s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                v_numeric = pd.to_numeric(s, errors='coerce').fillna(0)
                df[coluna] = v_numeric.round(0).astype('int32')
                print(f"✅ '{coluna}': int32 processado.")

            # --- TRATAMENTO PARA FLOAT/DOUBLE ---
            elif 'float' in str(tipo).lower() or 'double' in str(tipo).lower():
                s = df[coluna].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[coluna] = pd.to_numeric(s, errors='coerce').astype(float)
                print(f"✅ '{coluna}': Float/Double processado.")

            # --- TRATAMENTO PARA DATAS (Ajustado para o Wrangler) ---
            elif str(tipo).lower() == 'date':
                # IMPORTANTE: Mantemos como Datetime64 do Pandas. 
                # O .dt.date gera objetos 'object/binary' que causam o erro de malformed parquet.
                df[coluna] = pd.to_datetime(df[coluna], errors='coerce')
                print(f"✅ '{coluna}': Datetime (compatível com Iceberg) processado.")

            # --- TRATAMENTO PARA DATETIME ---
            elif 'datetime' in str(tipo).lower():
                df[coluna] = pd.to_datetime(df[coluna], errors='coerce')
                print(f"✅ '{coluna}': Datetime processado.")

            # --- TRATAMENTO PARA STRING ---
            elif str(tipo).lower() in ['str', 'object', 'varchar']:
                df[coluna] = df[coluna].astype(str).replace(['nan', 'NaN', 'None', '<NA>'], np.nan)
                print(f"✅ '{coluna}': String processada.")

        except Exception as e:
            print(f"⚠️ Erro na coluna '{coluna}': {e}")
            
    return df

def corrigir_mojibake(df):
    """
    Detecta e corrige caracteres que foram lidos como Latin-1 mas eram UTF-8.
    Ex: 'iluminaÃ§Ã£o' -> 'iluminação'
    """
    def fix_string(text):
        if isinstance(text, str):
            try:
                # O segredo: Reverte o erro de leitura
                return text.encode('latin1').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                return text
        return text

    # Aplica nas colunas e nos dados
    df.columns = [fix_string(c) for c in df.columns]
    for col in df.select_dtypes(include=['object']):
        df[col] = df[col].apply(fix_string)
    
    return df

import pandas as pd
import logging

# Configuração básica de log para o Glue CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def ingest_dataframe_to_s3_parquet(
    df, 
    database, 
    table, 
    s3_path, 
    partition_cols=None, 
    mode="overwrite_partitions",
    description=None
):
    """
    Função Genérica para ingestão de DataFrames no S3/Athena via Glue Job.
    
    Args:
        df (pd.DataFrame): Dados a serem salvos.
        database (str): Banco de dados no Glue Catalog.
        table (str): Nome da tabela.
        s3_path (str): Caminho S3 (ex: s3://bucket/prefix/).
        partition_cols (list, optional): Colunas para particionamento.
        mode (str): 'overwrite', 'append' ou 'overwrite_partitions'.
        description (str): Descrição da tabela no catálogo.
    """
    try:
        logger.info(f"Iniciando escrita da tabela {database}.{table} em {s3_path}")
        
        # O wrangler cuida da conversão de tipos Pandas -> Glue/Athena automaticamente
        response = wr.s3.to_parquet(
            df=df,
            path=s3_path,
            dataset=True,
            database=database,
            table=table,
            partition_cols=partition_cols,
            mode=mode,
            compression="snappy"
        )
        
        logger.info(f"Escrita finalizada. Partições criadas: {partition_cols}")
        return response
        
    except Exception as e:
        logger.error(f"Erro na ingestão para {table}: {str(e)}")
        raise e
    
import awswrangler as wr
import logging

# Configuração de logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def read_table(database, table=None, query=None, ctas_approach=False):
    """
    Função Genérica para ler dados do Athena para um DataFrame Pandas.
    
    Args:
        database (str): Banco de dados no Athena.
        table (str, optional): Nome da tabela (se quiser ler a tabela toda).
        query (str, optional): Query SQL customizada. Se informada, ignora o parâmetro 'table'.
        ctas_approach (bool): Se True, utiliza CTAS para acelerar a leitura de grandes volumes.
        
    Returns:
        pd.DataFrame: DataFrame com os resultados.
    """
    try:
        # Se não enviou uma query pronta, monta o SELECT *
        if not query:
            if not table:
                raise ValueError("Você deve informar ou o nome da 'table' ou uma 'query' customizada.")
            query = f"SELECT * FROM {table}"
        
        logger.info(f"Executando leitura no Athena | DB: {database} | Query: {query}")
        
        # Executa a query
        df = wr.athena.read_sql_query(
            sql=query,
            database=database,
            ctas_approach=ctas_approach,
            unload_approach=False # Pode ser True para volumes massivos de dados
        )
        
        logger.info(f"Leitura concluída! Linhas recuperadas: {len(df)}")
        return df
        
    except Exception as e:
        logger.error(f"Erro ao ler tabela {table} no Athena: {str(e)}")
        raise e
    
import awswrangler as wr
import pandas as pd
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
import awswrangler as wr
import logging
import sys

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def ingest_to_iceberg(df, database, table, s3_path, partition_cols):
    try:
        if database not in wr.catalog.databases().values:
            wr.catalog.create_database(name=database)

        # Garantir que dat_data é datetime64[ns] antes de enviar
        if 'dat_data' in df.columns:
            df['dat_data'] = pd.to_datetime(df['dat_data'], errors='coerce')

        logger.info(f"Iniciando carga Iceberg em {database}.{table}")

        wr.athena.to_iceberg(
            df=df,
            database=database,
            table=table,
            table_location=s3_path,
            temp_path=f"{s3_path.rstrip('/')}_temp/",
            partition_cols=partition_cols,
            keep_files=False,
            dtype={'dat_data': 'date'} # Isso aqui é o que resolve o erro do Athena
        )
        
        logger.info(f"Sucesso: {database}.{table} processada.")

    except Exception as e:
        logger.error(f"Erro na carga Iceberg: {str(e)}")
        raise e
    

def executar_glue_job(nome_job):
    """
    Dispara a execução de um Glue Job.

    Parameters
    ----------
    nome_job : str
        Nome do Glue Job que será executado.

    Returns
    -------
    str
        JobRunId da execução iniciada
    """

    glue_client = boto3.client("glue")

    response = glue_client.start_job_run(
        JobName=nome_job
    )

    job_run_id = response["JobRunId"]

    print(f"Glue Job '{nome_job}' iniciado.")
    print(f"JobRunId: {job_run_id}")

    return job_run_id