"""Integra CNPO (Cadastro Nacional de Produtores Orgânicos, MAPA) e SIGORG: produtores, entidades
(certificadoras, OPAC e OCS) e resumo por município, ligado à base IBGE (região e bioma)."""
import re, unicodedata, pandas as pd
SRC, REF, DADOS = "/mnt/project-files/Orgânicos/", "/mnt/project-files/embrapa-organicos/referencias/", "/mnt/project-files/embrapa-organicos/dados/"
def norm(s): return re.sub(r"[\s\-']+", " ", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()).strip()
mun = pd.read_csv(REF + "municipios_ibge_bioma.csv")
mun["chave"] = mun.municipio.map(norm) + "|" + mun.uf
chave2id = dict(zip(mun.chave, mun.id_local))
# grafias diferentes encontradas nos cadastros
APELIDOS = {"SAO TOME DAS LETRAS": "SAO THOME DAS LETRAS", "EMBU": "EMBU DAS ARTES", "MOJI MIRIM": "MOGI MIRIM", "MOJI DAS CRUZES": "MOGI DAS CRUZES",
            "PARATI": "PARATY", "SANTA ISABEL DO PARA": "SANTA IZABEL DO PARA", "ITAPAGE": "ITAPAJE", "AMPARO DA SERRA": "AMPARO DO SERRA",
            "SAO LUIS DO PARAITINGA": "SAO LUIZ DO PARAITINGA", "BRASILIA": "BRASILIA", "PICARRAS": "BALNEARIO PICARRAS", "ELDORADO DOS CARAJAS": "ELDORADO DO CARAJAS",
            "SANTANA DO LIVRAMENTO": "SANT ANA DO LIVRAMENTO", "GRAO PARA": "GRAO PARA", "TRAJANO DE MORAIS": "TRAJANO DE MORAES", "ASSU": "ACU",
            "SAO VICENTE FERRER": "SAO VICENTE FERRER", "POXOREO": "POXOREU", "OLHO D AGUA DO BORGES": "OLHO D AGUA DO BORGES"}
import difflib
por_uf = mun.groupby("uf").chave.apply(lambda x: [k.split("|")[0] for k in x]).to_dict()
def local(cidade, uf):
    uf = str(uf).strip().upper()
    if uf == "DF": return "Brasília-DF"  # regiões administrativas (Sobradinho, Brazlândia...) fazem parte de Brasília
    bruto = re.sub(r"\(.*?\)", " ", str(cidade))
    for c in [norm(bruto), norm(re.split(r",|/| - ", bruto)[0]), norm(re.split(r",|/| - | [Ee] ", bruto)[0])]:
        c = APELIDOS.get(c, c)
        k = chave2id.get(f"{c}|{uf}")
        if k: return k
    perto = difflib.get_close_matches(c, por_uf.get(uf, []), n=1, cutoff=0.85)
    return chave2id[f"{perto[0]}|{uf}"] if perto else ""

def escopos(t):
    t = norm(t); e = []
    if "PRIMARIA VEGETAL" in t: e.append("Produção vegetal")
    if "PRIMARIA ANIMAL" in t: e.append("Produção animal")
    if "EXTRATIVISMO" in t: e.append("Extrativismo")
    if "PROCESSAMENTO" in t and "VEGETAL" in t.split("PROCESSAMENTO", 1)[1]: e.append("Processamento vegetal")
    if "PROCESSAMENTO" in t and "ANIMAL" in t.split("PROCESSAMENTO", 1)[1]: e.append("Processamento animal")
    if "INSUMOS" in t: e.append("Insumos")
    return ";".join(e)
TIPO = {"CERTIFICADORA": "Certificadora (auditoria)", "CERT": "Certificadora (auditoria)", "OPAC": "OPAC (sistema participativo)", "OCS": "OCS (venda direta)"}

c = pd.read_excel(SRC + "CNPO.xlsx", dtype=str)
c = c.assign(fonte="CNPO", tipo=c["Tipo de Entidade"].map(TIPO), escopo=c.Escopo.map(escopos), situacao=c["Situação"].str.title(),
             atividades=c.Atividade.fillna("").str.replace(r";\s*$", "", regex=True), referencia=c.Ano + "-" + c["Mês"])
c = c.rename(columns={"CNPF_CNPJ_NIF": "documento", "Nome do Produtor": "produtor", "País": "pais"})

s = pd.read_excel(SRC + "SIGORG.xlsx", dtype=str)
s["escopo"] = s.Escopo.map(escopos)
s = s.groupby(["Tipo de entidade", "Entidade", "País", "UF", "Cidade", "CPF/CNPJ", "Nome do Produtor"], dropna=False).agg(
    escopo=("escopo", lambda x: ";".join(sorted(set(";".join(x).split(";")) - {""}))), atividades=("Atividade", lambda x: "; ".join(sorted(set(x.dropna())))),
    validade=("Data de validade", "max"), referencia=("Data do certificado", "max")).reset_index()
s = s.assign(fonte="SIGORG", tipo=s["Tipo de entidade"].map(TIPO), situacao="Ativo", pais="BRASIL", referencia=s.referencia.str[:10], validade=s.validade.str[:10])
s = s.rename(columns={"CPF/CNPJ": "documento", "Nome do Produtor": "produtor"})

cols = ["fonte", "tipo", "Entidade", "pais", "UF", "Cidade", "situacao", "documento", "produtor", "escopo", "atividades", "referencia"]
p = pd.concat([c[cols], s[cols + ["validade"]]], ignore_index=True).rename(columns={"Entidade": "entidade", "UF": "uf", "Cidade": "cidade"})
p["id_local"] = [local(ci, uf) if str(pa).upper().startswith("BRA") else "" for ci, uf, pa in zip(p.cidade, p.uf, p.pais)]
br = p.pais.str.upper().str.startswith("BRA")
p = p.merge(mun[["id_local", "cod_ibge", "regiao", "bioma_predominante"]], on="id_local", how="left")
p.to_csv(DADOS + "produtores_organicos.csv", index=False)
fora = p[br & (p.id_local == "")]
print("produtores:", p.fonte.value_counts().to_dict(), "| no exterior:", (~br).sum(), "| BR sem município:", len(fora))
print(fora.groupby(["cidade", "uf"]).size().sort_values(ascending=False).head(25).to_string())

# entidades
ent = p.groupby(["fonte", "tipo", "entidade"]).agg(produtores=("produtor", "count"), municipios=("id_local", lambda x: x[x != ""].nunique()),
                                                   ufs=("uf", lambda x: ";".join(sorted(set(x.dropna()))))).reset_index().sort_values("produtores", ascending=False)
ent.to_csv(DADOS + "entidades_organicos.csv", index=False)

# resumo por município
def top(x, n=5):
    v = pd.Series([a.strip().split(" (")[0] for t in x.dropna() for a in re.split(r";", t) if a.strip()]).value_counts()
    return "; ".join(v.index[:n].str.title())
q = p[p.id_local != ""]
pm = q.groupby("id_local").agg(produtores_cnpo=("fonte", lambda x: (x == "CNPO").sum()), produtores_sigorg=("fonte", lambda x: (x == "SIGORG").sum()),
                               certificadora=("tipo", lambda x: x.str.startswith("Cert").sum()), opac=("tipo", lambda x: x.str.startswith("OPAC").sum()),
                               ocs=("tipo", lambda x: x.str.startswith("OCS").sum()), entidades=("entidade", "nunique"), principais_produtos=("atividades", top)).reset_index()
pm = mun[["id_local", "cod_ibge", "municipio", "uf", "regiao", "bioma_predominante", "latitude", "longitude"]].merge(pm, on="id_local")
pm.to_csv(DADOS + "produtores_por_municipio.csv", index=False)
print("municípios com produtores:", len(pm)); print(pm.groupby("regiao")[["produtores_cnpo", "produtores_sigorg"]].sum())
