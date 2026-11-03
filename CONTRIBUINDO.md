# Como contribuir

Obrigado pelo interesse. Antes de tudo, leia as regras do projeto em
[docs/LICENCIAMENTO.md](docs/LICENCIAMENTO.md). Em resumo:

- só referências bíblicas e links, nunca o texto das leituras;
- nenhum texto espiritual gerado por IA;
- texto de terceiros só com licença aberta (CC0, CC BY 4.0, CC BY-SA 4.0) ou domínio público
  com procedência comprovada;
- todo dado factual com fonte registrada em [docs/FONTES.md](docs/FONTES.md).

## Escrever ou ceder um comentário

1. Leia [conteudo/README.md](conteudo/README.md) (formato, licenças, chave do dia).
2. Crie o arquivo em `conteudo/`, rode `make validar` e abra um pull request.
3. Ao enviar, você declara que o texto é seu (ou que tem o direito de cedê-lo) e que o licencia
   como indicado no campo `licenca`.

## Sugerir correção na tradução

A tradução das passagens é feita por IA a partir do grego e do hebraico, sem revisão humana completa.
Se você achar um erro, use o formulário
[Sugerir correção na tradução](https://github.com/meu-bem/vitral/issues/new?template=correcao-traducao.yml).
Não precisa saber programar.

- Diga a passagem, o que está no livro e como deveria ficar, com suas palavras.
- **Nunca cole texto de tradução com direitos reservados** (CNBB, Ave-Maria, Bíblia de Jerusalém,
  NVI, ARA etc.). Sugestões que copiem esses textos serão recusadas.
- Cite o original (grego, hebraico ou latim) ou uma fonte em domínio público quando puder.
- Uma sugestão aceita muda o `status` do versículo para revisado e entra no livro do ano seguinte.

## Corrigir um dado (calendário ou referência)

1. Encontre a fonte: documento da Santa Sé, determinação oficial da CNBB publicada ao público
   ou fonte com licença aberta. Não use a memória. Não copie datas nem referências de
   publicações com direitos reservados, como os Diretórios da Liturgia.
2. Corrija o arquivo em `data/`:
   - mude o `status` para `verificado` só se conferiu em fonte;
   - acrescente o id da fonte em `fontes`.
3. Registre a fonte em `docs/FONTES.md` (URL, licença, data de acesso, o que foi usado).
4. Rode `make test` e `make validar`.

As listas do que está pendente estão em `docs/relatorios/`. É um bom lugar para começar.

## Código

- Python 3.11+. Identificadores em inglês; comentários e documentação em português.
- O calendário (`src/vitral/liturgy/`) não pode ter dependências externas.
- Antes de propor dependência nova, veja se dá para evitar; se entrar, fixe a versão e o hash.
- Testes: `make test`. Mudou o calendário? O cruzamento com o romcal
  (`tests/test_cross_romcal.py`) precisa continuar sem divergência sem explicação.

## Conduta

Este projeto segue o [Código de Conduta](CODE_OF_CONDUCT.md).
