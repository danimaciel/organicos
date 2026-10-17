"""Georreferencia os conteúdos classificados: municípios, estados e biomas citados no texto,
mais o município da Unidade da Embrapa responsável (como referência separada)."""
import re, unicodedata, pandas as pd
REF, DADOS = "/mnt/project-files/embrapa-organicos/referencias/", "/mnt/project-files/embrapa-organicos/dados/"

def sem_acento(s): return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
def norm(s): return re.sub(r"[\s\-']+", " ", sem_acento(s).lower()).strip()

mun = pd.read_csv(REF + "municipios_ibge_bioma.csv", dtype={"cod_ibge": "Int64"})
mun["n"] = mun.municipio.map(norm)
por_nome = mun.groupby("n").uf.apply(set).to_dict()
id_por = {(r.n, r.uf): r.id_local for r in mun.itertuples()}
UFS = set(mun.uf)
ESTADOS = sorted(mun[["estado", "uf"]].drop_duplicates().values.tolist(), key=lambda x: -len(x[0]))
def estados_no_texto(t):
    # nomes com acento e inicial maiúscula (evita "para", "acre" etc.); nomes longos primeiro (Mato Grosso do Sul antes de Mato Grosso)
    achou = set()
    for e, uf in ESTADOS:
        rx = re.compile(rf"\b{re.escape(e)}\b")
        if rx.search(t): achou.add(uf); t = rx.sub(" ", t)
    return achou
NOMES_ESTADO = {norm(e) for e, _ in ESTADOS}
MAX_PAL = max(len(n.split()) for n in por_nome)

UNIDADES = {
 "Amazônia Oriental": "Belém-PA", "Semiárido": "Petrolina-PE", "Milho e Sorgo": "Sete Lagoas-MG", "Arroz e Feijão": "Santo Antônio de Goiás-GO",
 "Florestas": "Colombo-PR", "Pecuária Sudeste": "São Carlos-SP", "Amazônia Ocidental": "Manaus-AM", "Gado de Leite": "Juiz de Fora-MG",
 "Clima Temperado": "Pelotas-RS", "Meio Ambiente": "Jaguariúna-SP", "Soja": "Londrina-PR", "Recursos Genéticos e Biotecnologia": "Brasília-DF",
 "Cerrados": "Brasília-DF", "Uva e Vinho": "Bento Gonçalves-RS", "Trigo": "Passo Fundo-RS", "Meio-Norte": "Teresina-PI",
 "Mandioca e Fruticultura": "Cruz das Almas-BA", "Caprinos e Ovinos": "Sobral-CE", "Acre": "Rio Branco-AC", "Solos": "Rio de Janeiro-RJ",
 "Agropecuária Oeste": "Dourados-MS", "Suínos e Aves": "Concórdia-SC", "Instrumentação": "São Carlos-SP", "Hortaliças": "Brasília-DF",
 "Algodão": "Campina Grande-PB", "Gado de Corte": "Campo Grande-MS", "Agricultura Digital": "Campinas-SP", "Informática Agropecuária": "Campinas-SP",
 "Tabuleiros Costeiros": "Aracaju-SE", "Rondônia": "Porto Velho-RO", "Agroindústria Tropical": "Fortaleza-CE", "Roraima": "Boa Vista-RR",
 "Agroindústria de Alimentos": "Rio de Janeiro-RJ", "Amapa": "Macapá-AP", "Amapá": "Macapá-AP", "Territorial": "Campinas-SP",
 "Monitoramento por Satélite": "Campinas-SP", "Pecuária Sul": "Bagé-RS", "Pantanal": "Corumbá-MS", "Agrobiologia": "Seropédica-RJ",
 "Café": "Brasília-DF", "Agrossilvipastoril": "Sinop-MT", "Agroenergia": "Brasília-DF", "Pesca e Aquicultura": "Palmas-TO",
 "Maranhão": "São Luís-MA", "Cocais": "São Luís-MA", "Alimentos e Territórios": "Maceió-AL", "Sede": "Brasília-DF", "Estudos e Capacitação": "Brasília-DF",
 "Quarentena Vegetal": "Brasília-DF", "Gestão Territorial": "Campinas-SP", "Transferência de Tecnologia": "Brasília-DF", "Produtos e Mercado": "Brasília-DF",
}
def unidade_local(u):
    u = str(u).replace("Embrapa ", "").strip()
    return UNIDADES.get(u, "")

BIOMAS = {"Amazônia": r"amazoni(a|co|ca)|amazon\b|amazon (forest|region|basin|biome)", "Caatinga": r"caatinga|semiarid|semi-arid|semiárid",
          "Cerrado": r"cerrado|savana brasileira|brazilian savanna", "Mata Atlântica": r"mata atlantica|atlantic (rain ?)?forest",
          "Pampa": r"\bpampa", "Pantanal": r"pantanal"}
BIOMAS = {k: re.compile(v) for k, v in BIOMAS.items()}

SEP_UF = re.compile(r"\s*(?:,|-|–|/|\()\s*([A-Z]{2})\b")
GATILHO = re.compile(r"\b(?:municipios?|cidades?|municipality|municipalities|county|city) (?:de |do |da |dos |das |of )?", re.I)

def achar(texto):
    bruto = sem_acento(texto)
    baixo = norm(bruto)
    ufs_txt = estados_no_texto(texto)
    achados = set()
    # 1) "Nome, UF" / "Nome-UF" / "Nome (UF)" / "Nome/UF"
    for m in SEP_UF.finditer(bruto):
        uf = m.group(1)
        if uf not in UFS: continue
        antes = norm(bruto[max(0, m.start() - 60):m.start()]).split()
        for k in range(min(MAX_PAL, len(antes)), 0, -1):
            nome = " ".join(antes[-k:])
            if nome in por_nome and uf in por_nome[nome]:
                achados.add(id_por[(nome, uf)]); break
    # 2) "município de X", "municípios de X, Y e Z"
    for m in GATILHO.finditer(bruto):
        trecho = norm(re.split(r"[.;:()\n|]", bruto[m.end():m.end() + 160])[0])
        for parte in re.split(r",| e | and ", trecho):
            pal = parte.split()
            for k in range(min(MAX_PAL, len(pal)), 0, -1):
                nome = " ".join(pal[:k])
                if nome in por_nome:
                    if nome in NOMES_ESTADO: break
                    cand = por_nome[nome] & ufs_txt if (len(por_nome[nome]) > 1 or ufs_txt) else por_nome[nome]
                    if len(cand) == 1: achados.add(id_por[(nome, next(iter(cand)))])
                    break
    ufs = ufs_txt | {a.rsplit("-", 1)[1] for a in achados}
    biomas = {b for b, rx in BIOMAS.items() if rx.search(baixo)}
    return sorted(achados), sorted(ufs), sorted(biomas)

info = mun.set_index("id_local")
def completar(df, campos, col_unid, col_bioma=None):
    res = [achar(" | ".join(r)) for r in df[campos].fillna("").values]
    df["municipios_citados"] = [";".join(a) for a, _, _ in res]
    df["ufs_citadas"] = [";".join(u) for _, u, _ in res]
    bio_txt = [set(b) for _, _, b in res]
    bio_mun = [set(info.loc[a, "bioma_predominante"].dropna()) if a else set() for a, _, _ in res]
    bio_col = [set(x.strip() for x in str(v).split(",") if x.strip() and x.strip() != "nan") for v in df[col_bioma]] if col_bioma else [set()] * len(df)
    df["biomas"] = [";".join(sorted(a | b | c)) for a, b, c in zip(bio_txt, bio_mun, bio_col)]
    REG = {"Nordeste": r"\bNordeste|Northeast", "Norte": r"Região Norte|Norte do Brasil|North(ern)? (region|Brazil)", "Centro-Oeste": r"Centro-Oeste|Central-West|Midwest",
           "Sudeste": r"\bSudeste|Southeast", "Sul": r"Região Sul|Sul do Brasil|South(ern)? (region|Brazil)"}
    txt = df[campos].fillna("").agg(" | ".join, axis=1)
    df["regioes"] = [";".join(sorted(set(mun[mun.uf.isin(u)].regiao) | {r for r, rx in REG.items() if re.search(rx, t)})) for (_, u, _), t in zip(res, txt)]
    df["local_unidade"] = df[col_unid].map(unidade_local)
    return df

for nome, campos, unid, bio in [("publicacoes", ["Título", "Palavras-chave", "Resumo"], "Unidade", None),
                                ("projetos", ["Título", "Palavras-chave", "Resumo"], "Unidade líder", None),
                                ("solucoes", ["Nome", "Palavras-chave", "Descrição", "Onde encontrar"], "Unidade responsável", "Bioma")]:
    df = pd.read_csv(DADOS + f"{nome}_classificados.csv", dtype=str)
    df = completar(df, campos, unid, bio)
    df.to_csv(DADOS + f"{nome}_classificados.csv", index=False)
    sem = df[df.local_unidade == ""][unid].value_counts()
    print(nome, "| com município:", (df.municipios_citados != "").mean().round(3), "| com UF:", (df.ufs_citadas != "").mean().round(3),
          "| com bioma:", (df.biomas != "").mean().round(3), "| unidades sem local:", sem.to_dict())
