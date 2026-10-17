"""Liga autores das publicações e líderes de projetos ao cadastro Autor Pessoal Embrapa
e resume a atuação de cada pessoa em orgânicos e agroecologia."""
import re, unicodedata, pandas as pd
SRC, DADOS = "/mnt/project-files/Orgânicos/", "/mnt/project-files/embrapa-organicos/dados/"
def chave(s): return re.sub(r"[^A-Z]", "", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper())

aut = pd.read_excel(SRC + "AutorPessoalEmbrapa.xls", dtype=str)
aut["k_aut"] = aut.Autoria.map(chave)
aut["k_nome"] = aut.Nome.map(chave)
aut = aut.sort_values("Ativado", ascending=False)  # prefere o cadastro ativo
pessoas = aut.groupby("k_nome").agg(nome=("Nome", "first"), autoria=("Autoria", "first"), afiliacao=("Afiliação", "first"),
                                     ativo=("Ativado", lambda x: "Sim" if (x == "S").any() else "Não"), id_autor=("Id Autor", "first")).reset_index()
# uma forma de autoria pode valer para mais de uma pessoa (homônimos)
k2p = aut.groupby("k_aut").k_nome.apply(lambda x: sorted(set(x))).to_dict()
k_ant = {chave(n): k for n, k in aut[aut["Nome Anterior"].notna()][["Nome Anterior", "k_nome"]].values}

pub = pd.read_csv(DADOS + "publicacoes_classificados.csv", dtype=str)
pub = pub[pub.nivel.isin(["Núcleo", "Afim"])]
linhas = []
for r in pub[["ID", "nivel", "Ano de publicação", "Autores", "cat_nucleo", "cat_pratica", "biomas", "ufs_citadas"]].itertuples(index=False):
    for a in str(r.Autores).split(";"):
        ps = k2p.get(chave(a), [])
        for p in ps:
            linhas.append((p, r.ID, r.nivel, r[2], len(ps) > 1, r.cat_nucleo, r.cat_pratica, r.biomas, r.ufs_citadas))
lig = pd.DataFrame(linhas, columns=["k_nome", "id_pub", "nivel", "ano", "homonimo", "cat_nucleo", "cat_pratica", "biomas", "ufs"])
lig.to_csv(DADOS + "pesquisador_publicacao.csv", index=False)

proj = pd.read_csv(DADOS + "projetos_classificados.csv", dtype=str)
proj = proj[proj.nivel.isin(["Núcleo", "Afim"])]
proj["k_nome"] = proj["Líder do projeto"].map(chave).map(lambda k: k_ant.get(k, k))
proj["no_cadastro"] = proj.k_nome.isin(pessoas.k_nome)
proj[["ID", "k_nome"]].to_csv(DADOS + "projeto_lider.csv", index=False)

def juntar(s): return ";".join(sorted(set(";".join(s.fillna("")).split(";")) - {""}))
g = lig.groupby("k_nome").agg(pub_nucleo=("nivel", lambda x: (x == "Núcleo").sum()), pub_afim=("nivel", lambda x: (x == "Afim").sum()),
                              primeiro_ano=("ano", "min"), ultimo_ano=("ano", "max"), homonimo=("homonimo", "any"),
                              temas=("cat_nucleo", juntar), praticas=("cat_pratica", juntar), biomas=("biomas", juntar), ufs=("ufs", juntar))
gp = proj.groupby("k_nome").agg(projetos_liderados=("ID", "count"), projetos_em_execucao=("Situação", lambda x: (x == "em execução").sum()))
res = g.join(gp, how="outer").reset_index().merge(pessoas, on="k_nome", how="left")
res["nome"] = res.nome.fillna(res.k_nome.map(dict(zip(proj.k_nome, proj["Líder do projeto"]))))
for c in ["pub_nucleo", "pub_afim", "projetos_liderados", "projetos_em_execucao"]: res[c] = res[c].fillna(0).astype(int)
res["pontuacao"] = res.pub_nucleo * 2 + res.pub_afim + res.projetos_liderados * 5
res = res.sort_values("pontuacao", ascending=False)
res.to_csv(DADOS + "pesquisadores.csv", index=False)
print("pessoas:", len(res), "| ativas:", (res.ativo == "Sim").sum(), "| com projeto:", (res.projetos_liderados > 0).sum(),
      "| líderes fora do cadastro:", (~proj.no_cadastro).sum(), "| autorias com homônimo:", lig.homonimo.mean().round(3))
print(res.head(15)[["nome", "afiliacao", "ativo", "pub_nucleo", "pub_afim", "projetos_liderados"]].to_string())
