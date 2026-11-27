# Orgânicos na Embrapa

**O que se produz e o que se pesquisa.** Ambiente aberto que cruza os produtores orgânicos cadastrados no Brasil (CNPO e SIGORG, do MAPA) com publicações, projetos e soluções tecnológicas da Embrapa sobre produção orgânica e agroecologia, com mapas por município, região e bioma.

- `index.html`: página de abertura, com entradas para produtor, extensionista e pesquisador
- `ambiente/`: o ambiente interativo (mapa, filtros, Produção × Ciência, pesquisadores, produtores e o assistente "Pergunte")
- `referencias/`: taxonomia de orgânicos e agroecologia e dicionário de 62 produtos
- `scripts/`: o passo a passo que gera os dados (Python)
- `dados/`: tabelas geradas pelos scripts (conteúdos classificados, pesquisadores, produtores por município, produção × ciência)
- `cadastro/`: formulário Google (script que cria formulário e planilha) para feiras e pontos de venda, que alimenta a camada "Onde comprar"
- `validacao/`: planilha de validação por amostra, para revisão dos especialistas

Tudo roda no navegador, sem servidor e sem cadastro. O assistente "Pergunte" é um código aberto em JavaScript: ele reconhece produto, lugar, tema, tipo e período na pergunta e responde com os mesmos dados da página, sem enviar nada para fora.

## Como os dados foram feitos

1. `01_municipios.py`: completa a lista de municípios do IBGE com região, bioma predominante (malha IBGE 2022 × biomas 2019, via [geobr](https://github.com/ipeaGIT/geobr)) e coordenadas ([municipios-brasileiros](https://github.com/kelvins/municipios-brasileiros)).
2. `02_classificar.py`: classifica os conteúdos da Embrapa com `referencias/taxonomia.json`. **Ligação direta** = fala de orgânicos, agroecologia, outras correntes de base ecológica ou certificação; **afim** = trata de duas ou mais práticas de base ecológica.
3. `03_georreferenciar.py`: encontra municípios ("Município, UF", "município de ..."), estados e biomas citados nos textos.
4. `04_pesquisadores.py`: liga autores e líderes de projeto ao cadastro Autor Pessoal Embrapa.
5. `05_produtores.py`: integra CNPO e SIGORG e liga cada produtor ao município do IBGE.
6. `07_produtos.py`: cruza os produtos declarados pelos produtores com os textos da Embrapa (`referencias/produtos.json`).
7. `06_pacote_ambiente.py`: gera `ambiente/dados.json` e as malhas leves.
8. `09_validacao.py`: sorteia as amostras da planilha de validação.

Os arquivos de origem (bases da Embrapa de setembro de 2026, CNPO de janeiro de 2026, SIGORG e lista do IBGE) não estão no repositório. A lista de produtores um a um (`produtores_organicos.csv`, gerada pelo script 05) também fica de fora, por trazer nomes e documentos; o site usa só contagens por município e produto. Para refazer, coloque-os numa pasta e ajuste os caminhos no topo de cada script.

## Atualização automática do CNPO

A tarefa `.github/workflows/atualizar-cnpo.yml` roda nos dias 6, 16 e 26 (o Ministério atualiza o CNPO nos dias 5, 15 e 25). Ela:

1. procura a planilha mais nova na [página do CNPO](https://www.gov.br/agricultura/pt-br/assuntos/sustentabilidade/organicos/cadastro-nacional-de-produtores-organicos-cnpo) e baixa (`scripts/10_atualizar_cnpo.py baixar`);
2. para se a planilha for igual à última usada (`dados/fontes.json`);
3. confere as colunas e o número de linhas, roda os scripts 05, 07 e 06 e confere se os produtores foram ligados aos municípios;
4. abre um pedido de mudança com o resumo (quantos entraram e saíram, por tipo e por estado). O site só muda quando o pedido é aprovado. Se algo der errado, abre um aviso (issue) e não muda nada.

A planilha e a lista de produtores um a um ficam só na máquina temporária da tarefa. `dados/cnpo_chaves.txt` guarda um código embaralhado por produtor, só para contar entradas e saídas. O SIGORG não tem planilha pública: `referencias/sigorg_sem_identificacao.csv` guarda a última carga sem nome, documento e contato. Para rodar na mão: aba Actions > Atualizar CNPO > Run workflow.

Os scripts aceitam caminhos por variáveis: `ORG_BASE` (pasta do repositório), `ORG_SRC` (bases de origem), `ORG_PRIVADO` (lista de produtores um a um) e `ORG_CNPO` (planilha do CNPO).

## Limites

Os números vêm de leitura automática de texto e servem para explorar. Só parte dos conteúdos cita o lugar onde o trabalho foi feito. Autores com a mesma forma de citação de outra pessoa aparecem marcados com `*`. Um produtor que declara vários produtos conta uma vez em cada um. Confira o conteúdo original antes de citar.

## Fontes

Embrapa · Ministério da Agricultura e Pecuária (CNPO e SIGORG) · IBGE · Ipea (geobr)
