# Melhorias ainda relevantes - v1.11.0

Os defeitos antigos de NDVI, EVI e duplicacao do catalogo ja foram tratados.
EVI, Xiaolei e o dispatcher generico reflectance foram removidos. O historico
completo da avaliacao foi preservado em `Verificacao/v1.11.0/`.

## Justificar a convencao radiometrica

O fluxo padrao utiliza radiancia TOA. Nas duas cenas, o NDVI medio foi cerca de
0.18 em radiancia e 0.40 em reflectancia TOA. Os limiares publicados de NDVI
para emissividade nao foram reajustados. Avaliar sua adequacao com referencia
independente e documentar a convencao de cada produto permanece prioridade.

## Validar acuracia com observacoes independentes

As referencias numericas verificam equacoes e unidades; as imagens verificam
execucao. Ainda precisamos de observacoes de temperatura da superficie e PWV
para quantificar acuracia, erro e incerteza. Temperatura do ar nao substitui
medicao de temperatura da superficie.

## Validar transferencia entre sensores e modelos

Coeficientes de recuperacao Landsat 8 aplicados ao Landsat 9 seguem experimentais.
Price/Kerr/Sobrino permanecem como comparacoes historicas de modelos AVHRR.
Resultados extremos positivos sao preservados para avaliacao, sem corte arbitrario.

## Processamento de cenas grandes

Os exemplos atuais leem imagens e demonstram as funcoes em recortes pequenos.
O workflow Du ja permite janelas com halo e grupos globais de NDVI para Wang.
Uma evolucao util e a orquestracao completa de cenas grandes com exportacao
incremental. Os verificadores usam blocos; o leitor Pillow pode manter
uma banda inteira em memoria. Nao misturar recortes locais de PWV como se fossem
uma recuperacao unica da cena sem atender a esses requisitos.

Veja [a verificacao atual](validation.md) e [os contratos cientificos](scientific-methods.md).
