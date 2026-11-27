"""Atualização automática do CNPO (Cadastro Nacional de Produtores Orgânicos, MAPA).

Uso:
  python scripts/10_atualizar_cnpo.py baixar    acha a planilha mais nova na página do MAPA, baixa, confere o formato
                                                e diz se mudou (saída "mudou=true/false" para o GitHub Actions)
  python scripts/10_atualizar_cnpo.py resumir   depois dos scripts 05, 07 e 06: confere o resultado, compara com a versão
                                                anterior e escreve o resumo em linguagem simples (resumo_cnpo.md)

A planilha e a lista de produtores um a um ficam só na pasta temporária (ORG_SRC e ORG_PRIVADO), nunca no repositório.
No repositório ficam: dados/fontes.json (qual arquivo foi usado) e dados/cnpo_chaves.txt (códigos embaralhados de cada
produtor, só para contar quem entrou e quem saiu; não dá para voltar ao nome).
"""
import hashlib, io, json, os, re, subprocess, sys, urllib.request
from datetime import datetime, timezone
import pandas as pd

PAGINA = "https://www.gov.br/agricultura/pt-br/assuntos/sustentabilidade/organicos/cadastro-nacional-de-produtores-organicos-cnpo"
B = os.environ.get("ORG_BASE", ".").rstrip("/") + "/"
SRC = os.environ.get("ORG_SRC", "/tmp/origem").rstrip("/") + "/"
PRIV = os.environ.get("ORG_PRIVADO", "/tmp/privado").rstrip("/") + "/"
CNPO = os.environ.get("ORG_CNPO", SRC + "CNPO.xlsx")
FONTES, CHAVES, RESUMO = B + "dados/fontes.json", B + "dados/cnpo_chaves.txt", B + "resumo_cnpo.md"
COLUNAS = ["Tipo de Entidade", "Entidade", "País", "UF", "Cidade", "Situação", "CNPF_CNPJ_NIF", "Nome do Produtor",
           "Escopo", "Atividade", "Contato", "Ano", "Mês"]
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def saida(**kv):  # passa valores para os próximos passos do GitHub Actions
    for k, v in kv.items():
        print(f"{k}={v}")
        if os.environ.get("GITHUB_OUTPUT"):
            open(os.environ["GITHUB_OUTPUT"], "a").write(f"{k}={v}\n")


def falha(msg):
    open(RESUMO, "w").write(f"## Atualização do CNPO não foi feita\n\n{msg}\n\nNada foi mudado no site.\n")
    print("ERRO:", msg); sys.exit(1)


def ler_fontes():
    return json.load(open(FONTES)) if os.path.exists(FONTES) else {}


def chaves(df):
    k = df["CNPF_CNPJ_NIF"].fillna("").str.strip() + "|" + df["Nome do Produtor"].fillna("").str.strip().str.upper()
    return set(k.map(lambda x: hashlib.sha1(x.encode()).hexdigest()[:12]))


def pegar(url, timeout=120):
    """Baixa com até 4 tentativas; se o Python falhar, tenta o curl (outro jeito de conectar)."""
    import time
    erro = None
    for n in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except Exception as e:
            erro = e; print(f"tentativa {n + 1} falhou: {e}"); time.sleep(10 * (n + 1))
    r = subprocess.run(["curl", "-sSfL", "--retry", "3", "--max-time", str(timeout), "-A", UA["User-Agent"], url], capture_output=True)
    if r.returncode == 0: return r.stdout
    raise RuntimeError(f"{erro} | curl: {r.stderr.decode().strip()}")


def baixar():
    html = pegar(PAGINA, 60).decode("utf-8", "ignore")
    links = sorted(set(re.findall(r'href="([^"]*cnpo-mapa[^"]*\.xlsx)"', html, re.I)))
    if not links:
        falha(f"Não achei o link da planilha na [página do CNPO]({PAGINA}). O Ministério pode ter mudado a página.")
    def data(u):  # cnpo-mapa-25-11-2026.xlsx -> 2026-11-25
        m = re.search(r"(\d{1,2})-(\d{1,2})-(\d{4})", u)
        return f"{m[3]}-{int(m[2]):02d}-{int(m[1]):02d}" if m else ""
    url = max(links, key=data)
    url = url if url.startswith("http") else "https://www.gov.br" + url
    os.makedirs(os.path.dirname(CNPO), exist_ok=True)
    corpo = pegar(url, 180)
    open(CNPO, "wb").write(corpo)
    sha = hashlib.sha256(corpo).hexdigest()
    antes = ler_fontes().get("cnpo", {})
    print("planilha:", url, f"{len(corpo) / 1e6:.1f} MB")
    if sha == antes.get("sha256"):
        saida(mudou="false", arquivo=url.rsplit("/", 1)[-1]); return
    # confere o formato antes de seguir
    try:
        df = pd.read_excel(CNPO, dtype=str)
    except Exception as e:
        falha(f"O arquivo baixado ({url}) não abriu como planilha: {e}")
    faltam = [c for c in COLUNAS if c not in df.columns]
    if faltam:
        falha(f"A planilha nova ({url}) veio sem as colunas: {', '.join(faltam)}. O formato mudou e os scripts precisam de ajuste.")
    n_antes = antes.get("linhas")
    if n_antes and not (0.7 * n_antes <= len(df) <= 1.5 * n_antes):
        falha(f"A planilha nova tem {len(df):,} linhas e a anterior tinha {n_antes:,}. A diferença é grande demais para ser normal; confira antes de publicar.".replace(",", "."))
    ref = df["Ano"].dropna().astype(str).str[:4] + "-" + df["Mês"].dropna().astype(str)
    novo = {"arquivo": url.rsplit("/", 1)[-1], "url": url, "data_arquivo": data(url), "sha256": sha, "linhas": len(df),
            "referencia": ref.mode().iat[0] if len(ref) else "", "baixado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    os.makedirs(PRIV, exist_ok=True)
    json.dump({"anterior": antes, "novo": novo}, open(PRIV + "cnpo_novo.json", "w"))
    saida(mudou="true", arquivo=novo["arquivo"], data=novo["data_arquivo"] or novo["baixado_em"])


def numero(n): return f"{n:,}".replace(",", ".")


def resumir():
    info = json.load(open(PRIV + "cnpo_novo.json")); antes, novo = info["anterior"], info["novo"]
    df = pd.read_excel(CNPO, dtype=str)
    k_novo = chaves(df)
    k_antes = set(open(CHAVES).read().split()) if os.path.exists(CHAVES) else set()
    entraram, sairam = len(k_novo - k_antes), len(k_antes - k_novo)
    # confere o resultado dos scripts
    p = pd.read_csv(PRIV + "produtores_organicos.csv", dtype=str)
    br = p[(p.fonte == "CNPO") & p.pais.str.upper().str.startswith("BRA")]
    ligados = br.id_local.notna().mean()
    if ligados < 0.95:
        falha(f"Só {ligados:.0%} dos produtores do Brasil foram ligados a um município (o normal é mais de 98%). Os nomes de cidades podem ter mudado de formato.")
    pm = pd.read_csv(B + "dados/produtores_por_municipio.csv")
    g = subprocess.run(["git", "-C", B, "show", "HEAD:dados/produtores_por_municipio.csv"], capture_output=True, text=True)
    velho = pd.read_csv(io.StringIO(g.stdout)) if g.returncode == 0 else pm.iloc[0:0]  # versão publicada, para comparar
    m_novos = sorted(set(pm[pm.produtores_cnpo > 0].id_local) - set(velho[velho.produtores_cnpo > 0].id_local))
    m_sairam = sorted(set(velho[velho.produtores_cnpo > 0].id_local) - set(pm[pm.produtores_cnpo > 0].id_local))
    tipos = df["Tipo de Entidade"].value_counts()
    uf_d = (pm.groupby("uf").produtores_cnpo.sum() - velho.groupby("uf").produtores_cnpo.sum()).dropna().astype(int)
    uf_d = uf_d[uf_d != 0].sort_values(key=abs, ascending=False).head(5)
    t = [f"## CNPO atualizado: {novo['arquivo']}", "",
         f"Planilha do Ministério de {novo['data_arquivo'] or novo['baixado_em']} ([página do CNPO]({PAGINA})), "
         f"no lugar de {antes.get('arquivo', 'a planilha anterior')}.", "",
         f"- **{numero(len(df))} produtores** no cadastro (antes: {numero(antes['linhas']) if antes.get('linhas') else 'sem registro'})",
         f"- **{numero(entraram)} entraram** e **{numero(sairam)} saíram**" if k_antes else "- Primeira carga com contagem de entradas e saídas: a comparação começa na próxima",
         f"- Por tipo: " + ", ".join(f"{k} {numero(v)}" for k, v in tipos.items()),
         f"- Municípios com produtores: {numero(int((pm.produtores_cnpo > 0).sum()))}"
         + (f" ({len(m_novos)} novos, {len(m_sairam)} deixaram de ter)" if len(velho) else ""),
         f"- Ligados a um município do IBGE: {ligados:.1%}"]
    if len(uf_d): t.append("- Estados que mais mudaram: " + ", ".join(f"{u} {v:+d}" for u, v in uf_d.items()))
    if m_novos: t.append("- Alguns municípios novos: " + ", ".join(m_novos[:8]))
    t += ["", "O SIGORG não foi atualizado (o Ministério não publica planilha dele); seguem os números da última carga.", "",
          "Para publicar no site, aprove este pedido de mudança (botão **Merge**). Se algo parecer estranho, é só fechar sem aprovar."]
    open(RESUMO, "w").write("\n".join(t) + "\n")
    open(CHAVES, "w").write("\n".join(sorted(k_novo)) + "\n")
    f = ler_fontes(); f["cnpo"] = novo; json.dump(f, open(FONTES, "w"), ensure_ascii=False, indent=1)
    print("\n".join(t))


if __name__ == "__main__":
    try:
        {"baixar": baixar, "resumir": resumir}[sys.argv[1]]()
    except SystemExit:
        raise
    except Exception as e:  # qualquer erro vira aviso em linguagem simples, com o detalhe técnico
        falha(f"A tarefa parou com um erro ao {'baixar a planilha' if sys.argv[1] == 'baixar' else 'conferir o resultado'}: `{type(e).__name__}: {e}`")
