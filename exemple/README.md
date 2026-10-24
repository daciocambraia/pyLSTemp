# Exemplos por metodo

Escolha um metodo abaixo. Cada notebook e independente e segue a mesma ordem:
introducao e entradas necessarias; funcao geral; parametros; leitura da imagem;
aplicacao; salvamento. Nao e necessario definir linhas ou colunas.

As chamadas usam argumentos nomeados: método primeiro (ou banda, na conversão
térmica), seguido de parâmetros relacionados. Cada tabela segue a mesma ordem
da chamada correspondente e informa condição de uso, padrão da API, unidade
e opções. Entradas alternativas aparecem em blocos próprios com suas tabelas;
opções de outros métodos não são listadas.

Instale na raiz do projeto: `python -m pip install -e ".[examples]"`.
O kernel do notebook deve usar esse mesmo ambiente.

## Imagens de entrada

Os exemplos Landsat8/9 usam uma pasta Collection2 Level1 com B4, B5, B10, B11,
MTL.txt, QA_PIXEL e QA_RADSAT, preservando os nomes e a grade. B2/SZA sao opcionais.
Kerr e Sobrino2004/2008 usam arquivos vermelho/NIR ja em reflectancia superficial; o leitor nao
converte DN em SR. Sobrino2004 e especifico de Landsat5 TM6.

PWV externo, perfis atmosfericos e endmembers mostrados como configuracoes
demonstrativas precisam ser substituidos/justificados para a cena analisada.

| Familia | Metodo e notebook |
|---|---|
| thermal | [Temperatura de brilho TOA](brightness.ipynb) |
| emissivity | [Avdan2016 — Emissividade](avdan_2016_emissivity.ipynb) |
| emissivity | [Rongali2018 — Emissividade](gopinadh_2018.ipynb) |
| emissivity | [Sobrino2004 — Emissividade TM6](sobrino_2004_tm6.ipynb) |
| emissivity | [Sobrino2008 — Emissividade](sobrino_2008.ipynb) |
| single_channel | [Avdan2016 — Temperatura da superficie](avdan_2016_lst.ipynb) |
| single_channel | [Jimenez-Munoz2014 — Single-channel](jimenez_munoz_2014_sc.ipynb) |
| split_window | [Du2015 — Split-window](du_2015.ipynb) |
| split_window | [Jimenez-Munoz2014 — Split-window](jimenez_munoz_2014_sw.ipynb) |
| split_window | [Rozenstein2014 — Split-window](rozenstein_2014.ipynb) |
| split_window | [Price1984 — Split-window](price_1984.ipynb) |
| split_window | [Kerr1992 — Split-window](kerr_1992.ipynb) |
| split_window | [Sobrino1993 — Split-window](sobrino_1993.ipynb) |
| water_vapor | [Wang2015 — Vapor de agua](wang_2015.ipynb) |
| water_vapor | [Ren2015 — Vapor de agua MSWCVR](ren_2015.ipynb) |
| optical_correction | [Chavez1996 — DOS](chavez_dos.ipynb) |
| optical_correction | [Chavez1996 — COST](chavez_cost.ipynb) |

Os guias agregados e scripts antigos foram retirados da distribuicao publica;
as copias de verificacao permanecem no arquivo local `Verificacao/`.
[API](../docs/api-reference.md) · [Fichas cientificas](../docs/method-cards.md).
