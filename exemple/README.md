# Como executar os exemplos

Cada notebook tem um único roteiro principal em **quatro blocos de código**:

1. **Preencher caminhos:** escolha os arquivos da tabela inicial, inclusive QA_PIXEL/QA_RADSAT; configure banda, unidade e pasta de saída quando solicitadas.
2. **Ler e aplicar QA:** execute a leitura, que verifica a grade e combina QA com nodata. Confira as contagens impressas.
3. **Calcular:** execute a chamada do método usando as matrizes já carregadas e `mask=mascara`.
4. **Salvar:** grave o GeoTIFF e use seu caminho na próxima etapa.

Os tópicos “Consulta” ficam ao final. Eles explicam alternativas e parâmetros; não são passos adicionais obrigatórios.

## Se você começa com a cena Level-1

Separe os GeoTIFFs B4, B5, B10 e B11, o MTL e as duas QA da mesma cena. Preserve a grade; se fizer recortes, use a mesma janela em todas as entradas e QA. Cada exemplo por arquivo lê apenas suas entradas necessárias; não exige carregar a cena inteira.

| Ordem | O que preparar | Notebook | Como repetir / o que produzir |
| --- | --- | --- | --- |
| 1 | Radiâncias ópticas e térmicas | [Radiância TOA](toa_radiance.ipynb) | Executar B4/4, B5/5, B10/10 e B11/11 conforme a cadeia escolhida; cada execução salva uma banda. |
| 2 | Temperaturas de brilho | [Brightness](brightness.ipynb) | Executar com radiância B10/`banda=10` e radiância B11/`banda=11`. Produz BT10 e BT11 em K. |
| 3 | Emissividades | [Avdan](emissivity__avdan-2016.ipynb) ou [Rongali](emissivity__rongali-2018.ipynb) | Avdan: ε10 para single-channel. Rongali: executar `banda=10` e `banda=11` para obter o par; manter B4/B5 e mudar a banda de destino. |
| 4, quando o método usa PWV | Vapor d’água | [Wang](water_vapor__wang-2015.ipynb) ou [Ren](water_vapor__ren-2015.ipynb) | Entram BT10/BT11 e bandas ópticas indicadas no notebook. Sai PWV em g/cm². |
| 5 | Temperatura da superfície | Escolher um notebook de LST na tabela abaixo | Carregar apenas os produtos que esse método exige, além de ambas as QA. |

A sequência acima usa a configuração de radiância óptica explicitada nos exemplos. Cada convenção óptica precisa respeitar o contrato do método; ela não é intercambiável com reflectância apenas por ter a mesma grade.

## Onde entram reflectância e DOS/COST

Para uma cadeia que aceita reflectância TOA ou corrigida, prepare B4/B5 com [Reflectância TOA](toa_reflectance.ipynb). Em seguida, quando a combinação pede correção óptica, execute [DOS](optical_correction__chavez-dos.ipynb) ou [COST](optical_correction__chavez-cost.ipynb) separadamente para cada banda. Informe a elevação solar real do MTL e uma pasta de saída distinta por banda/método. QA entra antes do ajuste do objeto escuro.

O método seguinte deve receber a convenção óptica que exige. A saída DOS/COST não substitui radiância TOA em uma chamada que exige radiância. Kerr precisa de NDVI de reflectância superficial coerente com seus limiares; o exemplo não gera esse NDVI a partir de radiância/TOA automaticamente.

## Escolher o método de temperatura

BT entra sempre em **K**. Emissividade é adimensional, específica de banda. As QA são obrigatórias nos exemplos por arquivo e devem estar na mesma grade.

| Notebook | Arquivos físicos que você precisa ter prontos | Saída |
| --- | --- | --- |
| [Mono-window 2016](single_window__mono-window-2016.ipynb) | BT10 e ε10 | LST |
| [Jiménez SC](single_window__jimenez-munoz-2014-sc.ipynb) | BT10, radiância B10, ε10 e PWV | LST |
| [Du](split_window__du-2015.ipynb) | BT10/BT11 e ε10/ε11; roteiro principal com coeficientes gerais, sem PWV | LST |
| [Jiménez SW](split_window__jimenez-munoz-2014-sw.ipynb) | BT10/BT11, ε10/ε11 e PWV | LST |
| [Price](split_window__price-1984.ipynb) | BT10/BT11 e ε10/ε11; adaptação AVHRR → TIRS | LST |
| [Sobrino 1993](split_window__sobrino-1993.ipynb) | BT10/BT11 e ε10/ε11; adaptação AVHRR → TIRS | LST |
| [Kerr](split_window__kerr-1992.ipynb) | BT10/BT11 e NDVI superficial; ε10/ε11 ainda exigidas pela interface comum; adaptação AVHRR → TIRS | LST |

Com emissividade pronta, não forneça também as bandas/seletor usados apenas para calculá-la. Os exemplos explicam a rota alternativa por bandas ao final. `water_vapor()` é a função que estima PWV; `water_vapor=` nas chamadas de LST é o parâmetro que recebe o PWV já pronto.

## Exemplo concreto: executar Rongali e depois Du

1. Prepare `radiancia_B4.tif` e `radiancia_B5.tif` com o notebook de radiância, usando os DN e o MTL originais.
2. Abra [Rongali](emissivity__rongali-2018.ipynb). Preencha `red_path`, `nir_path`, `qa_pixel_path` e `qa_radsat_path`.
3. Execute os quatro blocos com `banda=10`. O GeoTIFF salvo na subpasta `B10` é ε10.
4. Mude para `banda=11` e execute novamente os quatro blocos. O GeoTIFF na subpasta `B11` é ε11; a execução não sobrescreve ε10.
5. Prepare BT10/BT11 com [Brightness](brightness.ipynb), se ainda não estiverem disponíveis.
6. Abra [Du](split_window__du-2015.ipynb), preencha os quatro caminhos físicos e as duas QA, escolha a unidade de saída e execute seus quatro blocos.

Esse roteiro não seleciona automaticamente todas as combinações; ele mostra como produzir e conectar os arquivos de uma cadeia específica. Os demais métodos seguem a própria tabela de entradas.

## Caminhos, ambiente e verificações

Na pasta da biblioteca, instale `python -m pip install -e ".[examples]"` e selecione esse ambiente como kernel. No passo 1, substitua `Path("CAMINHO_...")` por um caminho real, como `Path(r"C:\dados\radiancia_B4.tif")`.

A pasta `saida` é relativa à pasta de trabalho do kernel, se não usar caminho absoluto. O notebook imprime o caminho absoluto. Para calibração, brightness e emissividade, uma subpasta por banda evita misturar B10/B11 ou B4/B5. Uma nova execução para a mesma banda e destino substitui o GeoTIFF anterior.

A ausência de arquivos é apontada no passo 1. Grades incompatíveis interrompem o passo 2. O passo 4 mostra os pixels válidos e o destino salvo. NaN pode decorrer de QA/nodata ou dos critérios do método; executar sem erro não comprova acurácia em campo.

São **16 notebooks**: 14 métodos e duas conversões TOA. [Fluxo QA](../docs/quality-inputs.md) · [API](../docs/api-reference.md) · [Fichas dos métodos](../docs/method-cards.md).
