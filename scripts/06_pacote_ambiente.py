"""Gera o pacote de dados (JSON) e as malhas leves usadas pelo ambiente interativo."""
import json, re, pandas as pd, geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.polygon import orient
def horario(g):  # d3-geo espera anel externo no sentido horário
    return MultiPolygon([orient(p, -1.0) for p in g.geoms]) if g.geom_type == "MultiPolygon" else orient(g, -1.0) if g.geom_type == "Polygon" else g
B = "/mnt/project-files/embrapa-organicos/"; D, R, A = B + "dados/", B + "referencias/", B + "ambiente/"
tax = json.load(open(R + "taxonomia.json"))
cads = [c["nome"] for c in tax["cadeias"]]
def lst(v): return [x for x in str(v).split(";") if x and x != "nan"]
PRODS = json.load(open(R + "produtos.json"))["produtos"]
cp = pd.read_csv(D + "conteudo_produto.csv", dtype=str)
cp_org = cp[cp.nivel.isin(["Núcleo", "Afim"])].groupby(["tipo", "id"]).produto.apply(lambda x: sorted(int(v) for v in set(x))).to_dict()
cp_all = cp.groupby("produto").size().to_dict()
pes_all = pd.read_csv(D + "pesquisadores.csv", dtype={"k_nome": str})
pidx = {k: i for i, k in enumerate(pes_all.k_nome)}
lig = pd.read_csv(D + "pesquisador_publicacao.csv", dtype=str)
lig_p = lig.groupby("id_pub").k_nome.apply(lambda x: sorted({pidx[k] for k in x if k in pidx})).to_dict()
lid = pd.read_csv(D + "projeto_lider.csv", dtype=str)
lig_j = {i: [pidx[k]] for i, k in zip(lid.ID, lid.k_nome) if k in pidx}
itens = []
for tipo, f, tit, sub, unid, ano, url in [("P", "publicacoes", "Título", "Tipo de publicação", "Unidade", "Ano de publicação", "Página da publicação no Portal Embrapa"),
                                          ("J", "projetos", "Título", "Situação", "Unidade líder", "mês/ano de início", "Página do projeto no Portal Embrapa"),
                                          ("S", "solucoes", "Nome", "Tipo", "Unidade responsável", "Ano de lançamento", "Página da tecnologia no Portal Embrapa")]:
    df = pd.read_csv(D + f + "_classificados.csv", dtype=str)
    df = df[df.nivel.isin(["Núcleo", "Afim"])].fillna("")
    for r in df.to_dict("records"):
        a = re.findall(r"(\d{4})", str(r[ano])); a = int(a[-1]) if a else None
        extra = r.get("Líder do projeto") if tipo == "J" else (str(r.get("Autores") or "")[:160] if tipo == "P" else "")
        itens.append({"t": tipo, "id": r["ID"], "ti": r[tit], "a": a, "st": r[sub], "u": str(r[unid]).replace("Embrapa ", ""), "n": "N" if r["nivel"] == "Núcleo" else "A",
                      "c": lst(r["cat_nucleo"]) + lst(r["cat_pratica"]), "x": lst(r["cat_contexto"]), "k": [cads.index(c) for c in lst(r["cadeias"])],
                      "m": lst(r["municipios_citados"]), "uf": lst(r["ufs_citadas"]), "b": lst(r["biomas"]), "lu": r["local_unidade"], "url": r[url], "au": extra or "", "pr": cp_org.get((tipo, r["ID"]), []),
                      "ps": lig_p.get(r["ID"], []) if tipo == "P" else lig_j.get(r["ID"], []) if tipo == "J" else []})
pes = [{"nome": (r.nome.title() if isinstance(r.nome, str) else ""), "af": r.afiliacao if isinstance(r.afiliacao, str) else "", "at": r.ativo == "Sim",
        "h": bool(r.homonimo) if not pd.isna(r.homonimo) else False} for r in pes_all.itertuples()]
pm = pd.read_csv(D + "produtores_por_municipio.csv")
po = pd.read_csv(D + "produtores_organicos.csv", dtype=str)
po = po[po.id_local.notna()].assign(produtos=lambda x: x.produtos.fillna("").str.split(";")).explode("produtos")
po = po[po.produtos != ""]
pc = po.groupby(["id_local", "produtos"]).size()
pc_d = {}
for (m, k), n in pc.items(): pc_d.setdefault(m, {})[k] = int(n)
prod = [{"id": r.id_local, "uf": r.uf, "rg": r.regiao, "b": r.bioma_predominante, "la": round(r.latitude, 3), "lo": round(r.longitude, 3),
         "cn": int(r.produtores_cnpo), "sg": int(r.produtores_sigorg), "ce": int(r.certificadora), "op": int(r.opac), "oc": int(r.ocs), "pp": r.principais_produtos if isinstance(r.principais_produtos, str) else "", "pc": pc_d.get(r.id_local, {})} for r in pm.itertuples()]
ent = pd.read_csv(D + "entidades_organicos.csv")
ent = [{"f": r.fonte, "tp": r.tipo, "e": r.entidade, "p": int(r.produtores), "m": int(r.municipios), "uf": r.ufs if isinstance(r.ufs, str) else ""} for r in ent.itertuples()]
mun = pd.read_csv(R + "municipios_ibge_bioma.csv")
usados = {m for i in itens for m in i["m"]} | {i["lu"] for i in itens}
munj = {r.id_local: [round(r.latitude, 3), round(r.longitude, 3), r.uf, r.bioma_predominante, r.regiao] for r in mun.itertuples() if r.id_local in usados}
ufs = {r.uf: [r.estado, r.regiao] for r in mun.drop_duplicates("uf").itertuples()}
pacote = {"tax": [{"id": c["id"], "eixo": c["eixo"], "nome": c["nome"], "exp": c["explicacao"]} for c in tax["categorias"]], "cad": cads,
          "itens": itens, "pes": pes, "prod": prod, "ent": ent, "mun": munj, "ufs": ufs, "produtos": [{"nome": p["nome"], "grupo": p["grupo"], "embrapa": int(cp_all.get(str(k), 0))} for k, p in enumerate(PRODS)], "gerado": "2026-10-17"}
json.dump(pacote, open(A + "dados.json", "w"), ensure_ascii=False, separators=(",", ":"))
st = gpd.read_parquet(R + "states_2020_simplified.parquet")
st["geometry"] = st.geometry.simplify(0.05, preserve_topology=True)
st["geometry"] = st.geometry.map(horario)
st[["abbrev_state", "geometry"]].rename(columns={"abbrev_state": "uf"}).to_file(A + "estados.geojson", driver="GeoJSON", COORDINATE_PRECISION=2)
bi = gpd.read_file(R + "biomas.geojson"); bi["geometry"] = bi.geometry.simplify(0.05, preserve_topology=True)
bi["geometry"] = bi.geometry.map(horario)
bi.to_file(A + "biomas.geojson", driver="GeoJSON", COORDINATE_PRECISION=2)
print(len(itens), len(pes), len(prod), len(ent))
