"""Tabela de referência de municípios: IBGE (lista do projeto) + código, coordenadas, região e bioma(s).
Fontes externas: kelvins/municipios-brasileiros (lat/lon) e geobr/IPEA (malhas IBGE 2022 e biomas 2019)."""
import sys, unicodedata, geopandas as gpd, pandas as pd
DL, OUT = sys.argv[1], "/mnt/project-files/embrapa-organicos/referencias/"
def norm(s): return unicodedata.normalize("NFKD", str(s)).encode("ascii","ignore").decode().upper().replace("-"," ").replace("'"," ").replace("  "," ").strip()
ibge = pd.read_excel("/mnt/project-files/Orgânicos/IBGE - Estados e municípios.xlsx", dtype=str)
m = gpd.read_parquet(f"{DL}/municipalities_2022_simplified.parquet")
m["code_muni"] = m.code_muni.astype(int)
b = gpd.read_parquet(f"{DL}/biomes_2019_simplified.parquet")
b = b[b.name_biome != "Sistema Costeiro"]
mp, bp = m.to_crs(5880), b.to_crs(5880)
inter = gpd.overlay(mp[["code_muni","geometry"]], bp[["name_biome","geometry"]], how="intersection", keep_geom_type=True)
inter["area"] = inter.area
inter["share"] = inter.area / inter.groupby("code_muni").area.transform("sum")
inter = inter.sort_values(["code_muni","share"], ascending=[True,False])
pred = inter.groupby("code_muni").first()[["name_biome"]].rename(columns={"name_biome":"bioma_predominante"})
todos = inter[inter.share >= .05].groupby("code_muni").name_biome.agg(", ".join).rename("biomas")
coords = pd.read_csv(f"{DL}/municipios.csv")[["codigo_ibge","latitude","longitude"]].rename(columns={"codigo_ibge":"code_muni"})
ref = m.drop(columns="geometry").merge(pred, on="code_muni", how="left").merge(todos, on="code_muni", how="left").merge(coords, on="code_muni", how="left")
ref = ref.rename(columns={"code_muni":"cod_ibge","name_muni":"municipio","abbrev_state":"uf","name_state":"estado","name_region":"regiao"})
ref["chave"] = ref.municipio.map(norm) + "|" + ref.uf
ibge["chave"] = ibge.Municipio.map(norm) + "|" + ibge.UF
r = ibge.merge(ref, on="chave", how="left", suffixes=("_lista",""))
print("sem casamento na malha IBGE:", r.cod_ibge.isna().sum()); print(r[r.cod_ibge.isna()][["id_local"]].to_string())
r = r[["id_local","cod_ibge","Municipio","uf","estado","regiao","bioma_predominante","biomas","latitude","longitude","chave"]].rename(columns={"Municipio":"municipio"})
r.to_csv(OUT+"municipios_ibge_bioma.csv", index=False)
print(r.regiao.value_counts(), r.bioma_predominante.value_counts())
# malha leve para mapas (GeoJSON simplificado)
mm = m.merge(pred, on="code_muni", how="left")
mm["geometry"] = mm.geometry.simplify(0.01, preserve_topology=True)
mm[["code_muni","name_muni","abbrev_state","geometry"]].to_file(OUT+"malha_municipios.geojson", driver="GeoJSON", COORDINATE_PRECISION=3)
bb = b.copy(); bb["geometry"] = bb.geometry.simplify(0.02, preserve_topology=True)
bb[["name_biome","geometry"]].to_file(OUT+"biomas.geojson", driver="GeoJSON", COORDINATE_PRECISION=3)
