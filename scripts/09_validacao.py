"""Monta a planilha de validação para os colegas da Embrapa: amostras sorteadas de cada etapa
(classificação, lugares, pesquisadores, produtos e taxonomia) com colunas para marcar certo/errado."""
import json, pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
B = "/mnt/project-files/embrapa-organicos/"
D, R = B + "dados/", B + "referencias/"
tax = json.load(open(R + "taxonomia.json"))
NOME = {c["id"]: c["nome"] for c in tax["categorias"]}
nomes = lambda s: "; ".join(NOME.get(x, x) for x in str(s).split(";") if x and x != "nan")
cut = lambda s, n=350: (str(s)[:n] + "…") if isinstance(s, str) and len(s) > n else ("" if pd.isna(s) else s)

fontes = [("Publicação", "publicacoes", "Título", "Resumo", "Ano de publicação", "Unidade", "Página da publicação no Portal Embrapa"),
          ("Projeto", "projetos", "Título", "Resumo", "mês/ano de início", "Unidade líder", "Página do projeto no Portal Embrapa"),
          ("Solução", "solucoes", "Nome", "Descrição", "Ano de lançamento", "Unidade responsável", "Página da tecnologia no Portal Embrapa")]
todos = []
for tipo, f, ti, re_, ano, un, url in fontes:
    d = pd.read_csv(D + f + "_classificados.csv", dtype=str)
    todos.append(pd.DataFrame({"ID": d.ID, "Tipo": tipo, "Título": d[ti], "Resumo (início)": d[re_].map(cut), "Ano": d[ano],
        "Unidade": d[un], "Nível atribuído": d.nivel, "Temas": (d.cat_nucleo.fillna("") + ";" + d.cat_pratica.fillna("")).map(nomes),
        "Termos que levaram à classificação": d.termos_encontrados, "Municípios citados": d.municipios_citados, "Estados": d.ufs_citadas,
        "Biomas": d.biomas, "Link": d[url]}))
todos = pd.concat(todos, ignore_index=True)

def amostra(df, n, seed=2026):
    # sorteio proporcional ao tipo, garantindo projetos e soluções na amostra
    partes = [g.sample(min(len(g), max(8, round(n * len(g) / len(df)))), random_state=seed) for _, g in df.groupby("Tipo")]
    return pd.concat(partes).sample(frac=1, random_state=seed).head(n)

cls = pd.concat([amostra(todos[todos["Nível atribuído"] == "Núcleo"], 100), amostra(todos[todos["Nível atribuído"] == "Afim"], 80),
                 amostra(todos[todos["Nível atribuído"] == "Prática isolada"], 40)])
geo = amostra(todos[todos["Nível atribuído"].isin(["Núcleo", "Afim"]) & todos["Municípios citados"].notna()], 50, 7)
pes = pd.read_csv(D + "pesquisadores.csv").head(60)
pes = pd.DataFrame({"Nome": pes.nome, "Afiliação": pes.afiliacao, "Ativo": pes.ativo, "Publicações diretas": pes.pub_nucleo,
                    "Publicações afins": pes.pub_afim, "Projetos liderados": pes.projetos_liderados, "Período": pes.primeiro_ano.astype(str).str[:4] + "–" + pes.ultimo_ano.astype(str).str[:4],
                    "Temas": pes.temas.map(nomes), "Nome de citação compartilhado?": pes.homonimo.map({True: "Sim", False: ""})})
PR = {p["nome"]: p for p in json.load(open(R + "produtos.json"))["produtos"]}
pxc = pd.read_csv(D + "produtos_producao_x_ciencia.csv")
prod = pd.DataFrame({"Produto": pxc.produto, "Grupo": pxc.grupo, "Produtores orgânicos": pxc.produtores, "Conteúdos da Embrapa (todos)": pxc.conteudos_embrapa,
                     "Conteúdos orgânicos/agroecológicos": pxc.conteudos_organicos, "Termos buscados nos produtores": pxc.produto.map(lambda n: PR[n]["prod"]),
                     "Termos buscados nos conteúdos": pxc.produto.map(lambda n: PR[n]["ciencia"])})
tx = []
for c in tax["categorias"]:
    tx.append({"Código": c["id"], "Categoria": c["nome"], "Explicação": c.get("explicacao", ""), "Termos": " | ".join(c.get("termos", []))})
tx = pd.DataFrame(tx)

wb = Workbook(); ws = wb.active; ws.title = "Como validar"
texto = [
    ("Validação do ambiente Orgânicos na Embrapa", True),
    ("Cada aba traz uma amostra sorteada de uma etapa do trabalho. Marque nas colunas amarelas se o resultado está certo e, quando não estiver, diga o que seria o certo.", False),
    ("", False),
    ("Como organizar", True),
    ("1. Distribua as abas conforme a experiência de cada colega (ex.: taxonomia para quem conhece agroecologia; pesquisadores para quem conhece as equipes).", False),
    ("2. O ideal é que cada linha seja vista por duas pessoas, com o nome na coluna Validador. Quando discordarem, a dúvida vira assunto de reunião.", False),
    ("3. Não é preciso validar tudo: a amostra já permite estimar a taxa de acerto de cada etapa.", False),
    ("4. Devolva a planilha preenchida. Eu calculo a taxa de acerto, ajusto as regras (termos, exclusões, nomes) e refaço os números do ambiente.", False),
    ("", False),
    ("O que cada aba pergunta", True),
    ("1 Classificação: o conteúdo é mesmo de orgânicos/agroecologia? O nível (direto, afim ou fora) está certo? Inclui 40 itens que ficaram FORA do ambiente, para achar o que deixamos escapar.", False),
    ("2 Lugares: os municípios, estados e biomas atribuídos ao conteúdo estão certos?", False),
    ("3 Pesquisadores: a pessoa atua mesmo no tema? Há confusão com outra pessoa de nome parecido?", False),
    ("4 Produtos: os termos usados para achar cada produto fazem sentido? A comparação produção × pesquisa parece razoável?", False),
    ("5 Taxonomia: as categorias e seus termos estão bons? Falta alguma? Algum termo traz coisa errada?", False),
    ("", False),
    ("Sugestão de meta: 85% de acerto na classificação e nos lugares antes de divulgar os números.", False),
]
for i, (t, b) in enumerate(texto, 1):
    c = ws.cell(row=i, column=1, value=t); c.font = Font(bold=b, size=14 if i == 1 else 11); c.alignment = Alignment(wrap_text=True, vertical="top")
ws.column_dimensions["A"].width = 120

AMARELO = PatternFill("solid", fgColor="FFF4CC"); CAB = PatternFill("solid", fgColor="2F6B4F")
def aba(nome, df, perguntas, larguras):
    w = wb.create_sheet(nome); cols = list(df.columns) + [p for p, _ in perguntas] + ["Comentário", "Validador"]
    w.append(cols)
    for row in df.itertuples(index=False): w.append([("" if pd.isna(v) else v) for v in row])
    n = len(df) + 1
    for j, c in enumerate(cols, 1):
        h = w.cell(row=1, column=j); h.font = Font(bold=True, color="FFFFFF"); h.fill = CAB; h.alignment = Alignment(wrap_text=True, vertical="top")
        w.column_dimensions[get_column_letter(j)].width = larguras.get(c, 22 if j > len(df.columns) else 16)
        if j > len(df.columns):
            for r in range(2, n + 1): w.cell(row=r, column=j).fill = AMARELO
    for k, (p, ops) in enumerate(perguntas):
        if ops:
            dv = DataValidation(type="list", formula1='"' + ",".join(ops) + '"', allow_blank=True); w.add_data_validation(dv)
            col = get_column_letter(len(df.columns) + 1 + k); dv.add(f"{col}2:{col}{n}")
    for r in range(2, n + 1):
        for j in range(1, len(cols) + 1): w.cell(row=r, column=j).alignment = Alignment(wrap_text=True, vertical="top")
    w.freeze_panes = "C2"; w.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{n}"
L = {"Título": 45, "Resumo (início)": 60, "Temas": 30, "Termos que levaram à classificação": 30, "Comentário": 40, "Link": 25}
aba("1 Classificação", cls.drop(columns=["Municípios citados", "Estados", "Biomas"]),
    [("É de orgânicos/agroecologia?", ["Sim", "Não", "Em parte"]), ("Nível correto", ["Direto", "Afim", "Fora"]), ("Temas corretos?", ["Sim", "Não", "Em parte"])], L)
aba("2 Lugares", geo[["ID", "Tipo", "Título", "Resumo (início)", "Unidade", "Municípios citados", "Estados", "Biomas", "Link"]],
    [("Municípios certos?", ["Sim", "Não", "Em parte"]), ("Estados certos?", ["Sim", "Não", "Em parte"]), ("Biomas certos?", ["Sim", "Não", "Em parte"])], {**L, "Municípios citados": 30})
aba("3 Pesquisadores", pes, [("Atua no tema?", ["Sim", "Não", "Em parte"]), ("Erro de nome ou de pessoa?", ["Não", "Sim"])], {"Nome": 34, "Temas": 40, "Comentário": 40})
aba("4 Produtos", prod, [("Termos adequados?", ["Sim", "Não", "Em parte"]), ("Resultado faz sentido?", ["Sim", "Não", "Em parte"])], {"Termos buscados nos produtores": 40, "Termos buscados nos conteúdos": 40, "Comentário": 40})
aba("5 Taxonomia", tx, [("Categoria adequada?", ["Sim", "Não", "Em parte"]), ("Termos a incluir", None), ("Termos a retirar", None)], {"Explicação": 40, "Termos": 70, "Termos a incluir": 30, "Termos a retirar": 30})
out = B + "validacao/validacao_organicos_embrapa.xlsx"; wb.save(out)
print(out, {s.title: s.max_row - 1 for s in wb.worksheets[1:]})
