# Sucessão: como outra pessoa assume o Vitral

Este roteiro serve para quem vai manter o projeto sem ajuda de quem o começou. Campos
`PREENCHER` são dados que só o mantenedor atual tem; nada aqui foi inventado.

## 1. Situação atual (preencha e mantenha atualizado)

| item | valor |
|---|---|
| Repositório | PREENCHER (ex.: github.com/ORGANIZACAO/vitral) |
| Organização no GitHub | PREENCHER |
| Pessoas com acesso de administração | PREENCHER (pelo menos duas) |
| Endereço do site | PREENCHER |
| Domínio próprio (se houver) | PREENCHER: registrador, titular, data de renovação |
| Contato do projeto (código de conduta, issues sensíveis) | PREENCHER |
| Internet Archive (opcional) | PREENCHER: conta e prefixo dos itens, se ligado |

## 2. Recomendações de estrutura

- Mantenha o repositório numa **organização** do GitHub com pelo menos dois administradores,
  não numa conta pessoal: a saída de uma pessoa não derruba o projeto.
- Ative o GitHub Pages da organização (Settings → Pages → Source: GitHub Actions).
- Se usar domínio próprio, registre a renovação automática e anote acima quem paga. Sem
  domínio próprio, o endereço `*.github.io` não exige renovação.

## 3. Segredos e variáveis

O fluxo principal **não precisa de segredo**: usa o `GITHUB_TOKEN` automático do Actions.

| nome | tipo | obrigatório | para quê |
|---|---|---|---|
| `VITRAL_ANOS_A_FRENTE` | variável | não (padrão 10) | quantos anos pré-gerar |
| `ARQUIVAR_INTERNET_ARCHIVE` | variável | não | `true` liga o envio ao Internet Archive |
| `IA_PREFIXO` | variável | só se arquivar | prefixo dos itens (ex.: `vitral-livro`) |
| `IA_ACCESS_KEY`, `IA_SECRET_KEY` | segredos | só se arquivar | chaves S3 de <https://archive.org/account/s3.php> |

Zenodo não está implementado. Se quiser, siga o mesmo padrão do `scripts/archive_ia.py`:
script idempotente, job desligado por variável, token em segredo.

## 4. Agendamento e a limitação dos 60 dias

O GitHub **desativa workflows agendados** de repositórios públicos sem atividade por 60 dias.
As defesas do projeto:

1. **Pré-geração (principal).** Cada execução garante as releases do ano atual e dos próximos
   10. Mesmo com o agendamento parado, os livros dos próximos anos já existem como
   pré-releases.
   - Limite: um ano pré-gerado continua marcado como "pré-gerado" até alguém (ou o
     agendamento) rodar a publicação dentro da janela de 30 dias antes do Advento.
2. **Tentativa de manter ativo.** O último passo do `publicar.yml` chama a API
   `PUT /actions/workflows/publicar.yml/enable`.
   - Limite: não há garantia de que isso conte como atividade para o GitHub.
3. **Verificação humana.**
   - Uma vez por ano, antes do Advento (outubro), confira na aba Actions se o `publicar`
     está ativo.
   - Se estiver desativado: Actions → publicar → "Enable workflow", depois "Run workflow".

## 5. Publicar manualmente

Pelo GitHub (sem instalar nada):

1. Actions → **publicar** → *Run workflow*.
2. Deixe "ano" vazio para a regra automática, ou informe o ano civil do 1º Domingo do Advento
   (ex.: `2027`) para forçar aquele ano.

Pela linha de comando (requer o `gh` autenticado com permissão de escrita):

```sh
make venv
GITHUB_REPOSITORY=ORGANIZACAO/vitral .venv/bin/python scripts/publish.py --ano 2027
```

Sem GitHub, gere os arquivos com `make livro ANO=2027`: tudo fica em `dist/2027/`.

## 6. Rotina anual sugerida (outubro)

1. `make validar ANO=<próximo ano>` e leia as lacunas.
2. Resolva o que puder com fonte:
   - exceções datadas da CNBB em `data/calendario/excecoes.yaml`;
   - correções de referências em `data/lecionario/`.
   Registre a procedência em `docs/FONTES.md`.
3. Confira as issues abertas pelo `verificar-links`.
4. Confira que o `publicar` está ativo (seção 4).

## 7. Dependências e atualizações

- Python: versões e hashes em `requirements.txt` / `requirements-dev.txt`. Para atualizar:
  `uv pip compile --generate-hashes requirements.in -o requirements.txt` (idem para `-dev`).
  Rode `make test` e compare um PDF gerado antes e depois.
- Actions: fixadas por SHA de commit com a versão em comentário. Atualize trocando o SHA
  pelo da nova versão (`gh api repos/actions/checkout/commits/vX.Y.Z --jq .sha`).
- Site: versões exatas em `site/package.json` e `site/package-lock.json`.
- Fontes de dados: as cópias em `data/fontes/` não mudam sozinhas. Para reimportar, siga os
  docstrings de `scripts/ingest_*.py`, revise o diff e os relatórios em `docs/relatorios/`.
