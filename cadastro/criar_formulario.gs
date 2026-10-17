/**
 * Cria o formulário "Onde comprar orgânicos" e a planilha que recebe as respostas.
 *
 * Como usar: abra https://script.google.com, crie um projeto novo, cole este arquivo
 * no lugar do código de exemplo, salve e clique em Executar (função criarTudo).
 * Na primeira vez o Google pede autorização para criar o formulário e a planilha.
 * No fim, o registro de execução mostra os links do formulário e da planilha.
 *
 * A planilha ganha:
 *  - a coluna "aprovado" (sim/não) na aba de respostas, para a equipe validar cada cadastro;
 *  - a aba "Publicar", que mostra só os cadastros aprovados e só os campos públicos
 *    (o nome e o e-mail de quem cadastrou ficam de fora). É essa aba que vai para o site.
 */
const UFS = ["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT","PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"];

function criarTudo() {
  const form = FormApp.create("Onde comprar orgânicos – cadastro de feiras e pontos de venda");
  form.setDescription("Cadastre uma feira, grupo de consumo, loja ou outro lugar que vende alimentos orgânicos ou agroecológicos. " +
    "Cada cadastro é conferido pela equipe antes de aparecer no mapa do site Orgânicos na Embrapa.");
  form.setCollectEmail(false);

  form.addTextItem().setTitle("Nome do local").setHelpText("Ex.: Feira Agroecológica do Bairro X").setRequired(true);
  form.addMultipleChoiceItem().setTitle("Tipo").setRequired(true).showOtherOption(true)
    .setChoiceValues(["Feira", "Grupo de consumo ou CSA", "Loja ou mercado", "Restaurante", "Entrega em domicílio", "Venda na propriedade"]);
  form.addListItem().setTitle("Estado (UF)").setChoiceValues(UFS).setRequired(true);
  form.addTextItem().setTitle("Município").setRequired(true);
  form.addTextItem().setTitle("Endereço ou ponto de referência");
  form.addTextItem().setTitle("Link do Google Maps").setHelpText("Opcional. Abra o lugar no Google Maps, toque em Compartilhar e cole o link aqui. Ajuda a pôr o ponto no lugar exato.");
  form.addCheckboxItem().setTitle("Dias de funcionamento").setChoiceValues(["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]);
  form.addTextItem().setTitle("Horário").setHelpText("Ex.: 7h às 12h");
  form.addCheckboxItem().setTitle("Produtos").showOtherOption(true)
    .setChoiceValues(["Hortaliças", "Frutas", "Grãos e cereais", "Ovos", "Leite e derivados", "Carnes", "Mel", "Pães e processados", "Plantas medicinais e temperos"]);
  form.addCheckboxItem().setTitle("Como a produção é garantida como orgânica").setHelpText("Marque todas as formas que existem no local.")
    .setChoiceValues(["Certificadora (selo por auditoria)", "Sistema participativo (OPAC)", "Venda direta com OCS", "Agroecológico sem certificação", "Não sei"]);
  form.addMultipleChoiceItem().setTitle("Faz entregas?").setChoiceValues(["Sim", "Não"]);
  form.addTextItem().setTitle("Contato público").setHelpText("Telefone, site ou rede social que pode aparecer no mapa.");
  form.addTextItem().setTitle("Seu nome").setHelpText("Para a equipe. Não aparece no mapa.").setRequired(true);
  form.addTextItem().setTitle("Seu e-mail").setHelpText("Para a equipe tirar dúvidas. Não aparece no mapa.").setRequired(true)
    .setValidation(FormApp.createTextValidation().requireTextIsEmail().build());
  form.addCheckboxItem().setTitle("Autorização").setRequired(true)
    .setChoiceValues(["Autorizo a publicação no mapa das informações do local (nome, tipo, endereço, dias, produtos e contato público)."]);

  const planilha = SpreadsheetApp.create("Onde comprar orgânicos – cadastros");
  form.setDestination(FormApp.DestinationType.SPREADSHEET, planilha.getId());
  SpreadsheetApp.flush();
  Utilities.sleep(3000);

  // aba de respostas: a primeira que o formulário criou
  const resp = planilha.getSheets().find(s => s.getFormUrl()) || planilha.getSheets()[0];
  const nome = resp.getName();
  // colunas: A carimbo, B nome, C tipo, D UF, E município, F endereço, G link, H dias, I horário,
  // J produtos, K garantia, L entrega, M contato, N nome de quem cadastrou, O e-mail, P autorização, Q aprovado, R observação
  resp.getRange("Q1:R1").setValues([["aprovado", "observação da equipe"]]).setFontWeight("bold").setBackground("#fff4cc");
  resp.getRange("Q2:Q").setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(["sim", "não"], true).build());

  const pub = planilha.insertSheet("Publicar");
  pub.getRange("A1").setFormula(`=QUERY('${nome}'!A:Q, "select B, C, D, E, F, G, H, I, J, K, L, M, A where Q = 'sim'", 1)`);
  pub.getRange("A1").setNote("Não edite esta aba: ela se monta sozinha com os cadastros aprovados.");
  const vazias = planilha.getSheets().filter(s => s.getName() !== nome && s.getName() !== "Publicar");
  vazias.forEach(s => { if (s.getLastRow() === 0) planilha.deleteSheet(s); });

  Logger.log("Formulário para divulgar: " + form.getPublishedUrl());
  Logger.log("Editar o formulário: " + form.getEditUrl());
  Logger.log("Planilha da equipe: " + planilha.getUrl());
  Logger.log("Próximo passo: na planilha, Arquivo > Compartilhar > Publicar na Web > aba Publicar > CSV > Publicar. Mande esse link e o do formulário para ligarmos ao site.");
}
