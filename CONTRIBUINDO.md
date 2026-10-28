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
