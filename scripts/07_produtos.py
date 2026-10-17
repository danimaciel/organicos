"""Cruza os produtos declarados pelos produtores orgânicos (CNPO/SIGORG) com os conteúdos da Embrapa
que tratam de cada produto: todos os conteúdos e só os de orgânicos/agroecologia."""
import json, re, unicodedata, pandas as pd
SRC, R, D = "/mnt/project-files/Orgânicos/", "/mnt/project-files/embrapa-organicos/referencias/", "/mnt/project-files/embrapa-organicos/dados/"
def norm(s): return re.sub(r"[\s\-_/]+", " ", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower())
PR = json.load(open(R + "produtos.json"))["produtos"]
rx_p = [re.compile(p["prod"]) for p in PR]
rx_c = [re.compile(p["ciencia"]) for p in PR]

# produtores
pr = pd.read_csv(D + "produtores_organicos.csv", dtype=str)
pr["a"] = (pr.atividades.fillna("") + " " + pr.escopo.fillna("")).map(norm)
pr["produtos"] = [";".join(str(k) for k, r in enumerate(rx_p) if r.search(a)) for a in pr.a]
pr.drop(columns="a").to_csv(D + "produtores_organicos.csv", index=False)
br = pr[pr.id_local.notna()]

# conteúdos (todos os da Embrapa) — marca produtos
fontes = [("P", "publicacoes-da-embrapa-2026-09.csv", ["Título", "Palavras-chave", "Resumo"]),
          ("J", "projetos-da-embrapa-2026-09.csv", ["Título", "Palavras-chave", "Resumo"]),
          ("S", "solucoes-tecnologicas-da-embrapa-2026-09.csv", ["Nome", "Palavras-chave", "Descrição"])]
linhas = []
for t, f, campos in fontes:
    df = pd.read_csv(SRC + f, dtype=str, usecols=["ID"] + campos)
    for i, txt in zip(df.ID, df[campos].fillna("").agg(" | ".join, axis=1)):
        x = norm(txt)
        for k, r in enumerate(rx_c):
            if r.search(x): linhas.append((t, i, k))
cp = pd.DataFrame(linhas, columns=["tipo", "id", "produto"])
org = pd.concat([pd.read_csv(D + f"{n}_classificados.csv", dtype=str, usecols=["ID", "nivel"]).assign(tipo=t)
                 for t, n in [("P", "publicacoes"), ("J", "projetos"), ("S", "solucoes")]]).rename(columns={"ID": "id"})
cp = cp.merge(org, on=["tipo", "id"], how="left")
cp["nivel"] = cp.nivel.fillna("Outro")
cp.to_csv(D + "conteudo_produto.csv", index=False)

# resumo produção x ciência
tot = len(br)
res = []
for k, p in enumerate(PR):
    q = br[br.produtos.str.split(";").map(lambda l: str(k) in l)]
    c = cp[cp.produto == k]
    o = c[c.nivel.isin(["Núcleo", "Afim"])]
    reg = q.regiao.value_counts()
    res.append({"produto": p["nome"], "grupo": p["grupo"], "produtores": len(q), "pct_produtores": round(100 * len(q) / tot, 1),
                "municipios": q.id_local.nunique(), "regiao_principal": reg.index[0] if len(reg) else "",
                "conteudos_embrapa": len(c), "conteudos_organicos": len(o), "organicos_diretos": (o.nivel == "Núcleo").sum(),
                "publicacoes_org": (o.tipo == "P").sum(), "projetos_org": (o.tipo == "J").sum(), "solucoes_org": (o.tipo == "S").sum()})
res = pd.DataFrame(res)
res["produtores_por_conteudo_organico"] = (res.produtores / res.conteudos_organicos.clip(lower=1)).round(0)
res.sort_values("produtores", ascending=False).to_csv(D + "produtos_producao_x_ciencia.csv", index=False)
print("produtores BR:", tot, "| com algum produto:", (br.produtos != "").mean().round(3))
print(res.sort_values("produtores", ascending=False).to_string())
