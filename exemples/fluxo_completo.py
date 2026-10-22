"""Execute os principais metodos em um recorte Landsat Level-1.

Uso na raiz do projeto:
    python exemples/fluxo_completo.py CAMINHO_DA_CENA --saida resultados
"""
from pathlib import Path
import argparse
from pylstemp.scene import LandsatScene
from pylstemp import spectral_index, emissivity, single_window, split_window, water_vapor, toa_radiance


def executar(pasta, saida):
    """Leia uma cena e salve resultados de um recorte central de ate 256 pixels."""
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    with LandsatScene(pasta) as cena:
        altura, largura = cena.shape
        linha = max(0, altura // 2 - 128)
        coluna = max(0, largura // 2 - 128)
        janela = (linha, min(altura, linha + 256), coluna, min(largura, coluna + 256))
        bandas, temperatura, mascara = cena.calibrated(janela, exclude_water=True)
        vermelho, infravermelho = bandas[4], bandas[5]  # radiancia TOA
        bt10, bt11 = temperatura[10], temperatura[11]  # kelvin

        ndvi = spectral_index("ndvi", nir=infravermelho, red=vermelho, mask=mascara)
        emissividade10 = emissivity(ndvi, band=10, emissivity_method="gopinadh-2018")
        emissividade11 = emissivity(ndvi, band=11, emissivity_method="gopinadh-2018")
        lst_single = single_window(bt10, vermelho, infravermelho,
                                   emissivity_method="avdan-2016", unit="celsius", mask=mascara)
        lst_du = split_window(bt10, bt11, vermelho, infravermelho,
                              lst_method="du-2015", unit="celsius", mask=mascara)
        pwv = water_vapor(bt10, bt11, ndvi, mask=mascara)
        radiancia10 = toa_radiance(cena.read("B10", janela), metadata=cena.metadata,
                                   band=10, mask=mascara)
        lst_jimenez_sc = single_window(
            bt10, vermelho, infravermelho, lst_method="jimenez-munoz-sc-2014",
            emissivity_method="gopinadh-2018", radiance_band_10=radiancia10,
            water_vapor=pwv, unit="celsius", mask=mascara,
        )
        mascara_pwv = mascara | (pwv < 0.066) | (pwv > 7.833)
        lst_jimenez = split_window(bt10, bt11, vermelho, infravermelho,
                                   lst_method="jimenez-munoz-2014", water_vapor=pwv,
                                   unit="celsius", mask=mascara_pwv)

        produtos = {
            "ndvi": (ndvi, "dimensionless"),
            "bt10": (bt10, "kelvin"),
            "bt11": (bt11, "kelvin"),
            "emissividade10": (emissividade10, "dimensionless"),
            "emissividade11": (emissividade11, "dimensionless"),
            "lst_single": (lst_single, "celsius"),
            "lst_du": (lst_du, "celsius"),
            "pwv": (pwv, "g/cm2"),
            "lst_jimenez_sc": (lst_jimenez_sc, "celsius"),
            "lst_jimenez": (lst_jimenez, "celsius"),
        }
        for nome, (imagem, unidade) in produtos.items():
            caminho = saida / f"{cena.product_id}_{nome}.tif"
            cena.write_geotiff(caminho, imagem, window=janela, units=unidade)
            print(caminho)
        return {"scene": cena.product_id, "window": janela, "products": len(produtos)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pasta", type=Path, help="Pasta Landsat com bandas, MTL e QA")
    parser.add_argument("--saida", type=Path, default=Path("resultados"))
    args = parser.parse_args()
    executar(args.pasta, args.saida)
