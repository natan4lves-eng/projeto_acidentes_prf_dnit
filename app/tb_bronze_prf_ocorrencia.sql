CREATE EXTERNAL TABLE `tb_bronze_prf_ocorrencia`(
  `id` string, 
  `pesid` string, 
  `data_inversa` string, 
  `dia_semana` string, 
  `horaario` string, 
  `uf` string, 
  `br` string, 
  `km` string, 
  `municipio` string, 
  `causa_principal` string, 
  `causa_acidente` string, 
  `ordem_tipo_acidente` string, 
  `tipo_acidente` string, 
  `classificacao_acidente` string, 
  `fase_dia` string, 
  `sentido_via` string, 
  `condicao_metereologica` string, 
  `tipo_pista` string, 
  `tracado_via` string, 
  `uso_solo` string, 
  `id_veiculo` string, 
  `tipo_veiculo` string, 
  `marca` string, 
  `ano_fabricacao_veiculo` string, 
  `tipo_envolvido` string, 
  `estado_fisico` string, 
  `idade` string, 
  `sexo` string, 
  `ilesos` string, 
  `feridos_leves` string, 
  `feridos_graves` string, 
  `mortos` string, 
  `latitude` string, 
  `longitude` string, 
  `regional` string, 
  `delegacia` string, 
  `uop` string)
ROW FORMAT DELIMITED 
  FIELDS TERMINATED BY '\;' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://130355226600-camada-bronze/tb_bronze_prf_ocorrencia'
TBLPROPERTIES (
  'classification'='csv', 
  'transient_lastDdlTime'='1773102875')