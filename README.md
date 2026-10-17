# Orgânicos na Embrapa

**O que se produz e o que se pesquisa.** Ambiente aberto que cruza os produtores orgânicos cadastrados no Brasil (CNPO e SIGORG, do MAPA) com publicações, projetos e soluções tecnológicas da Embrapa sobre produção orgânica e agroecologia, com mapas por município, região e bioma.

- `index.html`: página de abertura, com entradas para produtor, extensionista e pesquisador
- `ambiente/`: o ambiente interativo (mapa, filtros, Produção × Ciência, pesquisadores, produtores e o assistente "Pergunte")
- `referencias/`: taxonomia de orgânicos e agroecologia e dicionário de 62 produtos
- `scripts/`: o passo a passo que gera os dados (Python)
- `dados/`: tabelas geradas pelos scripts (conteúdos classificados, pesquisadores, produtores por município, produção × ciência)
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

## Limites

Os números vêm de leitura automática de texto e servem para explorar. Só parte dos conteúdos cita o lugar onde o trabalho foi feito. Autores com a mesma forma de citação de outra pessoa aparecem marcados com `*`. Um produtor que declara vários produtos conta uma vez em cada um. Confira o conteúdo original antes de citar.

## Fontes

Embrapa · Ministério da Agricultura e Pecuária (CNPO e SIGORG) · IBGE · Ipea (geobr)
