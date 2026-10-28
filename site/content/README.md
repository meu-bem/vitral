# Seções do site

Cada arquivo `.md` desta pasta vira uma página do site em `/<nome-do-arquivo>/`
(este README é ignorado). O cabeçalho opcional define:

```markdown
---
titulo: Título no menu e na página
ordem: 20        # posição no menu (menor vem antes)
menu: sim        # "nao" para não aparecer no menu
---
Texto em Markdown (HTML embutido é desligado).
```

Para remover uma seção, apague o arquivo. Lembre a política do projeto: nada de texto
espiritual gerado por computador; texto de terceiros só com licença aberta e procedência
registrada em `docs/FONTES.md`.
