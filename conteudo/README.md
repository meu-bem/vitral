# Conteúdo humano

Esta pasta recebe textos escritos ou cedidos por pessoas para acompanhar as leituras
de um dia. Ela começa vazia de propósito: o Vitral não publica texto gerado por
computador nem texto de terceiros sem licença aberta.

Se não houver texto para um dia, o livro mostra só as referências e os links.

## Formato

Um arquivo Markdown (`.md`) por texto, em qualquer subpasta. O arquivo começa com um
bloco de metadados (front matter) entre linhas `---`:

```markdown
---
autor: Nome de quem escreveu
licenca: CC-BY-SA-4.0
dia: B.advento-1.domingo
titulo: (opcional)
---
O texto, em Markdown.
```

### Campos

| campo | obrigatório | valores |
|---|---|---|
| `autor` | sim | nome de quem escreveu (ou da obra, se for domínio público) |
| `licenca` | sim | `CC0`, `CC-BY-4.0`, `CC-BY-SA-4.0` ou `dominio-publico` |
| `dia` | sim | chave do dia litúrgico (veja abaixo) |
| `fonte` | se `dominio-publico` | `obra`, `edicao`, `ano` e, se houver, `tradutor` e `url` |
| `titulo` | não | título curto |
| `url_licenca` | não | link para o texto da licença ou da cessão |

Exemplo de `fonte` para domínio público:

```yaml
fonte:
  obra: Título da obra
  edicao: Editora, cidade, número da edição
  tradutor: Nome (ou "sem tradução")
  ano: 1900
  url: https://endereço-de-onde-foi-baixado
```

Só inclua texto em domínio público se você o baixou de uma fonte verificável. Registre
a procedência também em `docs/FONTES.md`. Lembre que a **tradução** tem direitos
próprios: um texto antigo numa tradução recente geralmente não está em domínio público.

### Chave do dia (`dia`)

O lecionário é cíclico, então um texto serve a todos os anos que usarem aquele dia:

- domingos e solenidades: ciclo `A`, `B` ou `C` + tempo + semana, ex.: `B.advento-1.domingo`,
  `A.quaresma-3.domingo`, `C.tc-15.domingo`, `B.pascoa.pentecostes`, `A.tc.cristo-rei`;
- dias de semana do Tempo Comum: ciclo `I` (anos ímpares) ou `II` (anos pares),
  ex.: `I.tc-10.quarta`;
- dias de semana dos outros tempos (iguais em todos os anos): ex.: `advento-2.terca`,
  `advento.12-17`, `quaresma-3.sexta`, `pascoa-4.sabado`;
- santos: `santos.<id>`, com o `id` de `data/calendario/santos.yaml`.

Para ver as chaves de um dia: `make calendario ANO=2026` lista cada data com a sua chave.

## Validação

`make validar` confere todos os arquivos desta pasta. A CI **rejeita** texto sem os
campos obrigatórios, com licença fora da lista, domínio público sem `fonte` ou com
chave de dia inexistente.
