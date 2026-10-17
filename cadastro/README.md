# Cadastro de feiras e pontos de venda

O mapa "Onde comprar" do ambiente mostra feiras, grupos de consumo, lojas e outros lugares que vendem orgânicos. Os dados vêm de um formulário do Google. Cada cadastro só aparece no mapa depois que a equipe marca **sim** na coluna `aprovado`.

## Montar uma vez

1. Abra [script.google.com](https://script.google.com) com a conta que vai cuidar do cadastro e clique em **Novo projeto**.
2. Apague o código de exemplo, cole todo o conteúdo de [`criar_formulario.gs`](criar_formulario.gs) e salve.
3. Clique em **Executar**. Na primeira vez o Google pede autorização: aceite.
4. Abra **Registro de execução**. Ele mostra o link do formulário e o da planilha.
5. Na planilha, vá em **Arquivo → Compartilhar → Publicar na Web**, escolha a aba **Publicar**, o formato **CSV** e clique em **Publicar**. Copie o link.
6. Ponha os dois links em [`ambiente/cadastro.json`](../ambiente/cadastro.json):

```json
{ "formulario": "link do formulário", "csv": "link CSV da aba Publicar" }
```

## No dia a dia

- Novos cadastros chegam na aba de respostas da planilha.
- Confira e marque `sim` (entra no mapa) ou `não` na coluna `aprovado`. A coluna ao lado serve para anotações da equipe.
- A aba **Publicar** se monta sozinha com os aprovados e **sem** o nome e o e-mail de quem cadastrou. Só ela é publicada.
- O site lê a aba publicada a cada visita. O Google pode levar alguns minutos para atualizar o CSV.

## Localização

Se o cadastro tiver link do Google Maps com coordenadas, o ponto vai para o lugar exato. Se não tiver, ou se for um link curto (`maps.app.goo.gl`), o ponto fica no centro do município.
