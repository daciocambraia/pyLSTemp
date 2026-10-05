> Atualizacao posterior: EVI removido e fluxo padrao alterado para radiancia TOA. Este relatorio registra uma etapa anterior. Consulte [a verificacao atual](FLUXO_RADIANCIA_v1.11.md) para os contratos e resultados vigentes.

# Melhorias identificadas apos a execucao dos modulos

Atualizacao de escopo em 05/10/2026: Xiaolei foi removido da versao atual. Este documento preserva os resultados da rodada anterior, que incluia o metodo. Os 204 casos sem SR nao fazem parte do catalogo atual. Consulte docs/ESCOPO_LEVEL1_v1.11.md e Verificacao/v1.11.0/escopo_level1_sem_xiaolei_2026-10-05/RELATORIO_ESCOPO.md.

Atualizacao em 05/10/2026: os defeitos NDVI 0/0 e EVI com BLUE infinito foram corrigidos e revalidados. A duplicacao de NDVI no catalogo foi removida; reflectance e mensagens foram ampliadas. Consulte docs/CORRECOES_INDICES_REFLECTANCIA_v1.11.md e Verificacao/v1.11.0/correcoes_indices_mensagens_2026-10-05/RELATORIO_CORRECOES.md. A avaliacao original abaixo foi preservada.

Data: 05/10/2026. Avaliacao baseada na rodada de matriz profunda.

A suite numerica teve 793 testes aprovados e 66 subtestes.
A matriz real teve 282 execucoes aprovadas, 204 rejeicoes esperadas e 204
casos sem SR. Os diagnosticos adicionais encontraram dois defeitos.
Nenhum algoritmo de producao foi alterado nesta etapa de avaliacao.

## P1: corrigir entradas invalidas dos indices

### NDVI com denominador zero

Reproducao:

~~~python
spectral_index("ndvi", nir=np.array([[0.]]), red=np.array([[0.]]))
# atual: [[0.]]
~~~

A expressao matematica e 0/0. O epsilon em compute_ndvi transforma esse caso
em 0 e permite a propagacao como indice valido, inclusive para emissividade.
A conversao radiometrica das cenas ja mascara DN zero, mas a API publica
tambem aceita arrays fornecidos diretamente pelo usuario.

Melhoria: mascarar denominadores nulos e entradas nao finitas explicitamente.
Definir e documentar qualquer tolerancia para denominadores quase nulos.
Verificar a regressao nas duas cenas e a contagem de pixels afetados.
Fonte de codigo: pylstemp/utils.py, compute_ndvi.

### EVI com banda azul infinita

Reproducao:

~~~python
spectral_index("evi", nir=np.array([[.6]]), red=np.array([[.2]]),
               blue=np.array([[np.inf]]))
# atual: [[-0.]]
~~~

O denominador infinito produz zero finito, que passa pela filtragem final.
Esse pixel deve ser invalidado pela banda de entrada nao finita.

Melhoria: propagar a mascara de nao finitos de NIR, RED e BLUE antes da divisao.
Manter testes para NaN, +inf e -inf em cada banda. Reavaliar separadamente
a politica que descarta |EVI|>1, hoje implicita no algoritmo.
Fonte de codigo: pylstemp/algorithms/spectral_index/evi.py.

## P1: completar a verificacao cientifica com insumos adequados

### Reflectancia de superficie e Xiaolei

A implementacao Xiaolei foi testada nas duas bandas, nas classes NDVI e nas
combinacoes de LST com SR sintetica. Faltam produtos SR_B* das duas cenas
para executar essas mesmas combinacoes com insumos reais apropriados.

Melhoria: obter Level-2 correspondente a cada data, sensor e path/row.
Utilizar SR_B4/SR_B5 para NDVI e SR_B4 para a dependencia red_band;
SR_B2 tambem permite repetir EVI. Verificar grade e QA e combinar com
BT10/BT11 derivados do produto Level-1 correspondente, mantendo a procedencia.

O helper surface_reflectance so aplica escala a SR Level-2 existente;
ele nao remove os efeitos atmosfericos de Level-1.
A USGS distingue expressamente TOA de reflectancia de superficie e informa
o processamento atmosferico e os insumos auxiliares.
[USGS Level-2](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products).

### Acuracia LST/PWV e transferencia de coeficientes

Concordar com as equacoes nao valida a parametrizacao para cada sensor.
Sobrino chegou a 111,31 C na cena L9, com QA aplicada. Esse extremo deve
ser inspecionado espacialmente e comparado a referencias, sem ser ocultado
por um limite universal de temperatura.

Melhoria: avaliar PWV contra uma referencia atmosferica externa e LST contra
medicoes compativeis com a data, horario e escala espacial da aquisicao.
ST_B10 Level-2 pode servir como comparacao operacional adicional, mas
compartilha dados Landsat e nao substitui temperatura medida em campo.
A USGS descreve os dados termicos, emissividade e perfis atmosfericos do
[produto ST](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature).

Price, Kerr e Sobrino devem permanecer identificados como adaptacoes AVHRR.
A transferencia dos coeficientes para Landsat 9 exige avaliacao propria.
Consultar os avisos de calibracao do
[Landsat 8](https://www.usgs.gov/landsat-missions/landsat-8-oli-and-tirs-calibration-notices)
e [Landsat 9](https://www.usgs.gov/landsat-missions/landsat-9-oli-and-tirs-calibration-notices)
antes de estabelecer uma politica por sensor/banda.

## P2: melhorar contratos e parametrizacao

| Evidencia observada | Proposta |
|---|---|
| Du aceita PWV escalar; raster gera TypeError de conversao NumPy | Validar e explicar o tipo aceito; avaliar suporte raster por pixel, preservando medias dos intervalos CWV sobrepostos |
| Price/Kerr/Sobrino ignoram water_vapor sem aviso | Declarar parametros usados por metodo e informar quando um argumento nao tem efeito |
| Kerr nao usa valores de emissividade na equacao, mas o workflow calcula e valida emissividade | Declarar requisitos por algoritmo no registro e separar as dependencias numericas das restricoes de workflow |
| Avdan e rejeitado em todo split_window | Manter a restricao atual ate revisar a politica por algoritmo; nao desbloquear apenas para completar combinacoes |
| Gopinadh fixa NDVI solo=0,15 e vegetacao=0,48 | Permitir endmembers configuraveis com defaults documentados e procedencia dos valores |
| Avdan muda de 0,966 para 0,971 em NDVI=0,2 e de 0,978 para 0,973 acima de 0,5 | Estudar sensibilidade desses limites; nao suavizar sem justificativa cientifica e novos testes |
| BT publica usa K1/K2 cadastrados no sensor; calibracao MTL usa os valores do produto | Facilitar o uso direto de MTL na API e manter validacao da procedencia |
| SZA disponivel e da B4, reutilizada em B2/B5 | Avaliar angulos por banda e quantificar a aproximacao adotada |
| Emissividade isolada nao recebe mask explicitamente | Avaliar uma mascara publica consistente ou documentar claramente a propagacao via NDVI NaN |

Suporte Du por pixel e endmembers configuraveis alteram escolhas cientificas.
Devem incluir referencias, testes nas fronteiras e avaliacoes de sensibilidade.

## P3: melhorar consistencia de uso e reproducibilidade

Indices escalares produzem TypeError por atribuicao em numpy.float64.
O alias B10 maiusculo e rejeitado, embora metodos e unidades aceitem maiusculas.
Decidir se escalares devem ser suportados ou rejeitados com mensagem clara;
normalizar aliases de bandas de forma consistente.

Nesta maquina, rasterio nao carregou por bloqueio de DLL. A alternativa Pillow
foi verificada, mas pode carregar bandas inteiras na memoria. Avaliar leitura
por janelas com rasterio em um ambiente configurado e manter comparacao entre
backends. O teste local nao substitui a CI em outros Python/SO.

Preservar manifestos de parametros, hashes, nivel radiometrico, unidades,
mascaras, dominio de coeficientes e origem de PWV junto aos produtos.
Os arquivos desta rodada ja registram esses elementos principais.

## Sequencia proposta para implementacao posterior

1. Corrigir os dois defeitos de NDVI/EVI, com testes de regressao e repeticao nas cenas.
2. Integrar Level-2 correspondente e repetir a matriz Xiaolei com SR real.
3. Melhorar mensagens de PWV e declarar requisitos/parametros utilizados por metodo.
4. Avaliar Du por pixel e endmembers configuraveis, com estudos de sensibilidade.
5. Executar validacao independente de acuracia e CI em outros ambientes.

As propostas foram avaliadas e documentadas; nao foram aplicadas aos algoritmos
nesta rodada. A aprovacao dos testes nao significa ausencia de melhorias nem
validacao cientifica completa de todos os metodos/sensores.
