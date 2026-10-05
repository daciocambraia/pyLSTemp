# Relatorio final - pyLSTemp v1.11.0

Atualizacao de escopo em 05/10/2026: Xiaolei foi removido da versao atual. Este documento preserva os resultados da rodada anterior, que incluia o metodo. Os 204 casos sem SR nao fazem parte do catalogo atual. Consulte docs/ESCOPO_LEVEL1_v1.11.md e Verificacao/v1.11.0/escopo_level1_sem_xiaolei_2026-10-05/RELATORIO_ESCOPO.md.

Data: 04/10/2026. Base anterior: v1.10.0 / commit 688a2a5.

## Resultado

As falhas confirmadas na auditoria foram corrigidas e os testes de software passaram.
As duas cenas foram processadas com calibracao do MTL e mascaras QA.
A versao esta preparada para revisao e envio ao GitHub.
**Nao e uma certificacao de acuracia cientifica da LST.** Ainda faltam refletancia
de superficie e dados independentes de temperatura/PWV para essa etapa.

## Correcoes e decisoes

- Mono-window: lambda em metros e rho=0.01438 m K; BT=300 K, emissividade=0.98 agora produz 301.383946 K.
- Removido o teto global de 56.7 C, que confundia temperatura do ar e de superficie.
- Xiaolei recebe refletancia de superficie em [0,1], sem converter DN por uma escala fixa.
- Avdan usa solo=0.966 da Tabela 2; preserva classes e termo de cavidade da parametrizacao escolhida.
  As descontinuidades entre classes e a divergencia do texto original foram documentadas.
- Wang usa a media da regressao direta e inversa prevista na Figura 3.
- Jimenez usa c1=1.378 da Tabela I.
- Mascaras incorporam valores nao finitos, NoData central, ambas as bandas termais e QA.
- PWV escalar negativo/infinito e parametros nao inteiros sao rejeitados.
- A restricao Avdan/split-window funciona com maiusculas e aliases.
- Colisoes de chaves/aliases no registro sao rejeitadas.
- Price foi preservado como aproximacao de emissividade inversa, com aviso explicito de adaptacao
  AVHRR/Landsat. Nao se afirma reproducao literal da expressao conflitante do artigo.
- Wang foi vetorizado em blocos de memoria limitada e comparado com janelas escalares.
- Documentacao, notebooks, versao, manifesto, SPDX e estrutura Git/CI foram atualizados.

## Verificacoes de software

- 77 testes aprovados, incluindo as oito regressoes independentes da auditoria.
- Dez blocos Python do guia de uso executados com sucesso.
- Seis notebooks executados para cada cena: 12 execucoes aprovadas.
  Um recorte real calibrado por cena foi reutilizado para executar os seis exemplos.
- Cobertura combinada de instrucoes/ramificacoes: 88.68%.
  O escopo aumentou com leitura/calibracao; cobertura nao mede acuracia.
- Python local: 3.14.7. Sintaxe verificada no modo 3.9.
- CI preparado para Python 3.9, 3.11 e 3.14 em Windows/Linux; essas execucoes remotas estao pendentes.
- sdist e wheel construidos, metadados validados e wheel importado fora da arvore de fontes.
- 40 GeoTIFFs conferidos quanto a modo, escala espacial, projecao e NoData.
- Valores exportados de TOA vermelha, mono-window e Du comparados a recalculo em recortes 64x64
  nas duas cenas, com tolerancia absoluta de 2e-5 para armazenamento float32.

O rasterio foi bloqueado pelo Controle de Aplicativos do Windows. A leitura alternativa
Pillow foi usada e testada; o backend rasterio continua pendente de execucao nesta maquina.
Os testes de IO verificam alinhamento e preservacao do georreferenciamento.
As tags de coordenadas originais foram preservadas, inclusive EPSG 32623 com northing negativo.

## Processamento das cenas

Landsat 8: LC08_L1TP_221071_20260919_20260925_02_T1.
Landsat 9: LC09_L1TP_221071_20260927_20260927_02_T1.

- Produtos Collection 2 Level-1, da mesma regiao e de datas diferentes.
- Bandas B2/B4/B5 convertidas para TOA pelo MTL.
- Usado SZA por pixel em centesimos de grau. O SZA fornecido e de B4; sua utilizacao para
  B2/B5 e uma aproximacao comum de angulo optico, explicitamente registrada.
- B10/B11 convertidas para kelvin pelos quatro coeficientes do MTL de cada banda.
- QA: preenchimento, nuvem dilatada, cirrus/nuvem/sombra/neve de alta confianca,
  saturacao em B2/B4/B5 e oclusao do terreno. Agua excluida para Wang.
- TOA, BT, NDVI/EVI, mono-window e Du avaliados na cena inteira, por blocos.
- Wang e Jimenez avaliados em tres recortes 256x256 por cena, com halo de 10 pixels
  e limites de grupos NDVI derivados da cena inteira.

| Sensor | Dimensoes | Pixels LST validos | Validos | Media mono (C) | Media Du (C) | Mono - Du (K) |
|---|---|---:|---:|---:|---:|---:|
| landsat_8 | 7691 x 7571 | 39,939,067 | 68.59% | 33.59 | 37.97 | -4.38 |
| landsat_9 | 7681 x 7571 | 39,632,897 | 68.15% | 36.24 | 43.43 | -7.19 |

O tempo medido para processar os blocos da cena inteira foi de aproximadamente 45 s
no Landsat 8 e 36 s no Landsat 9; nao inclui todas as exportacoes, figuras e hashes.
As execucoes completas, com os produtos e ROIs, duraram cerca de 87 s e 73 s.
Esses tempos dependem desta maquina e nao sao benchmarks universais.

## Limites e valores que exigem cuidado

A diferenca media entre metodos foi 4.38 K no Landsat 8 e 7.19 K no Landsat 9.
Ela nao mede erro contra referencia de campo. Mono-window aqui corrige emissividade;
nao resolve explicitamente transmitancia atmosferica e radiancia de percurso.
Du usa coeficientes gerais, sem uma estimativa independente da atmosfera.

Wang produziu alguns valores PWV altos (ate aproximadamente 13.96 g/cm2).
A base TIGR3 do artigo cobre 0.066 a 7.833 g/cm2. Foram identificados como extrapolacoes:
Landsat 8, ROIs 1/2/3: 4, 28 e 50 pixels; Landsat 9: 3, 11 e 163 pixels.
Os valores brutos foram preservados. Produtos adicionais possuem mascara de extrapolacao
e PWV/Jimenez com essas extrapolacoes excluidas. Esse filtro e uma verificacao de faixa,
nao validacao independente nem truncamento dos valores para o limite.

**Landsat 9 permanece experimental para os coeficientes de recuperacao LST/PWV derivados
de Landsat 8.** A conversao radiometrica usa seus proprios parametros.
Nao comparar diretamente as duas datas como se fossem uma validacao entre sensores.

Os dados atuais sao TOA. Xiaolei nao foi aplicado a essas imagens: seu calculo foi
testado com entradas sinteticas independentes em refletancia de superficie.
Para completar a validacao cientifica, obter SR Level-2 ou correcao atmosferica
justificada, uma referencia independente de temperatura de superficie/PWV e avaliar
vies, RMSE, dominio de aplicacao e incerteza separadamente para cada sensor.

## Evidencias locais para reproducao

- scene_summary.json: estatisticas de ambas as cenas, parametros e hashes dos insumos.
- software_validation.json e tests_and_coverage.txt: testes e notebooks.
- geotiff_validation.json: verificacoes dos produtos exportados.
- packaging_validation.json: verificacao da distribuicao.
- source_snapshot_sha256.json: hashes da versao final dos arquivos Python.
- Em Verificacao/v1.11.0/, cada pasta de cena contem REPORT.md, results.json, mapas PNG e GeoTIFFs.

Os percentis no JSON sao amostrados de forma deterministica; contagem, minimo,
maximo e media foram calculados sobre todos os pixels finitos.
Relatorios nao substituem inspecao dos mapas e da procedencia dos dados.

## Preparacao para GitHub

A raiz voltou a conter pylstemp/, pyproject.toml, docs/, tests/, exemples/ e .github/.
A v1.10 foi preservada. Imagens, artigos, arquivos historicos, distribuicoes e resultados
locais volumosos estao excluidos pelo .gitignore.
As alteracoes de fonte e um resumo portavel da validacao sao preparados localmente.
Nao houve push, publicacao de release ou envio ao PyPI.

Procedimentos e fontes primarias: [scientific-methods.md](scientific-methods.md).
Executor reproduzivel: [validate_scenes.py](../scripts/validate_scenes.py).
