"""Classifica publicações, projetos e soluções da Embrapa com a taxonomia de orgânicos/agroecologia."""
import json, re, unicodedata, pandas as pd
SRC, OUT = "/mnt/project-files/Orgânicos/", "/mnt/project-files/embrapa-organicos/dados/"
tax = json.load(open("/mnt/project-files/embrapa-organicos/referencias/taxonomia.json"))
def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s)
excl = re.compile("|".join(tax["excluir"]))
cats = [(c["id"], c["eixo"], c["nome"], re.compile("|".join(f"\\b(?:{t})" for t in c["termos"]))) for c in tax["categorias"]]
cads = [(c["nome"], re.compile("|".join(f"\\b(?:{t})" for t in c["termos"]))) for c in tax["cadeias"]]

def classificar(txt):
    t0 = norm(txt)
    t = excl.sub(" ", t0)
    zon = t != t0  # texto fala de zoneamento/condições "agroecológicas" (aptidão de terras, não agroecologia)
    hit, ev = {}, []
    for i, e, n, rx in cats:
        m = rx.search(t)
        if m:
            hit[i] = e
            if e != "contexto": ev.append(m.group(0))
    nuc = [i for i, e in hit.items() if e == "nucleo"]
    if zon and nuc == ["N2"]: nuc = []
    pra = [i for i, e in hit.items() if e == "pratica"]
    ctx = [i for i, e in hit.items() if e == "contexto"]
    nivel = "Núcleo" if nuc else "Afim" if len(pra) >= 2 else "Prática isolada" if pra else ""
    cad = [n for n, rx in cads if rx.search(t)] if nivel else []
    return nivel, "; ".join(dict.fromkeys(ev)), ";".join(nuc), ";".join(pra), ";".join(ctx), ";".join(cad)

def rodar(df, campos, nome, id_col="ID"):
    txt = df[campos].fillna("").agg(" | ".join, axis=1)
    pre = re.compile(r"organic|agroecolog|agro-ecolog|biodinam|biodynam|permacult|ecologic|adubac|adubo|green manur|cobertura|cover crop|compost|humus|bokashi|biofert|bioch|biocarv|biolog|biocontrol|inimigo|natural enem|bioins|bio-ins|biopest|biodef|entomopat|trichoderma|thuring|baculo|beauveria|metarh|parasit|calda|extrato|botanic|neem|nim|homeopat|fitoterap|agroflorest|agroforest|saf|sintrop|fixacao|fixation|fbn|inocul|micorr|mycorr|rizob|promotoras|remineral|rocha|rock|consorc|policult|intercrop|quinta|espontan|companh|spdh|cobertura morta|mulch|zoneam|sisorg|cnpo|opac|10\.?831|participat|pnapo|planapo|regenerat|alternativ|natural")
    res = [classificar(x) if pre.search(norm(x)) else ("","","","","","") for x in txt]
    r = pd.DataFrame(res, columns=["nivel","termos_encontrados","cat_nucleo","cat_pratica","cat_contexto","cadeias"], index=df.index)
    out = pd.concat([df, r], axis=1)
    sel = out[out.nivel != ""]
    sel.to_csv(OUT + f"{nome}_classificados.csv", index=False)
    print(nome, len(df), sel.nivel.value_counts().to_dict())
    return sel

pub = pd.read_csv(SRC + "publicacoes-da-embrapa-2026-09.csv", dtype=str)
rodar(pub, ["Título", "Palavras-chave", "Resumo"], "publicacoes")
proj = pd.read_csv(SRC + "projetos-da-embrapa-2026-09.csv", dtype=str)
rodar(proj, ["Título", "Palavras-chave", "Resumo"], "projetos")
sol = pd.read_csv(SRC + "solucoes-tecnologicas-da-embrapa-2026-09.csv", dtype=str)
rodar(sol, ["Nome", "Palavras-chave", "Descrição"], "solucoes")
