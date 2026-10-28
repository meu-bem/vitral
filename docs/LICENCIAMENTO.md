# Licenciamento: o que o Vitral inclui e o que não inclui

Política geral: **na dúvida, só referência e link.** Toda dúvida jurídica fica registrada no
fim deste documento.

## O que o livro inclui

| item | origem | por que pode |
|---|---|---|
| Referências bíblicas (ex.: "Jo 3,1-8") | fontes de `docs/FONTES.md` | referência é dado factual, não texto |
| Datas, graus e cores do calendário | algoritmo próprio + dados licenciados | fatos e regras, implementados em código |
| Nomes das celebrações | romcal (MIT), conferidos | dados sob licença aberta |
| Imagem do calendário, QR codes, capa | gerados pelo projeto | obra própria (CC BY-SA 4.0) |
| Textos de interface (títulos, instruções de uso) | escritos para o projeto | obra própria (CC BY-SA 4.0) |
| Comentários de colaboradores | `conteudo/` | só CC0, CC BY 4.0, CC BY-SA 4.0 ou domínio público com procedência |
| Fontes tipográficas | EB Garamond, Source Sans 3 | SIL Open Font License 1.1 |

## O que o livro não inclui

- **Texto das leituras e dos salmos** (tradução da CNBB ou qualquer outra com direitos), nem o
  refrão do salmo. As buscas no YouTube usam só a referência e o nome do dia.
- **Comentários, homilias e meditações de terceiros** sem licença aberta.
- **Texto espiritual gerado por IA.** O código, os testes, a documentação técnica e os textos
  de interface foram escritos com apoio de IA. Nenhum comentário, oração ou meditação foi.
- **Dados raspados** de sites de liturgia. Esses sites só aparecem como links.

## Licenças do repositório

- Código: MIT (`LICENSE`).
- Conteúdo original e dados derivados (`data/`, imagens geradas, textos de interface): CC BY-SA
  4.0 (`LICENSE-CONTEUDO`). Os dados do Lecionário derivam em parte dos mapas de versificação
  da Copenhagen Alliance (CC BY-SA 4.0). Por isso a licença é compartilhável pela mesma licença.
- `data/fontes/`: cópias de terceiros, cada uma com a licença original ao lado (MIT,
  Apache-2.0, Unlicense, CC BY-SA 4.0).
- `CODE_OF_CONDUCT.md`: adaptação da tradução pt-BR do Contributor Covenant 2.1 (CC BY 4.0),
  ajustada à natureza católica do projeto. A atribuição e a lista de alterações estão no próprio
  arquivo, como pede a licença.

## Atribuições exigidas

Ficam na página de créditos de cada livro e em `docs/FONTES.md`:

- romcal (MIT);
- Liturgical Calendar API (Apache-2.0);
- lecionário tâmil de jayarathina (Unlicense);
- Copenhagen Alliance (CC BY-SA 4.0);
- EB Garamond e Source Sans 3 (OFL);
- CNBB, subsídio *Celebrar em Família* (referências das leituras de Nossa Senhora Aparecida).

## Dúvidas registradas

1. **Diretórios da Liturgia (CNBB 2022, Ordinariado Militar 2025).**
   - Obras com todos os direitos reservados.
   - Decisão do mantenedor (2026-10-27): **nenhuma data, referência ou outro dado tirado deles fica
     no repositório**, nem nos testes. Ficam citados só como fonte das regras nacionais (quais
     celebrações vão para o domingo e para qual domingo), que são normas, não conteúdo da obra.
2. **Referências do Lecionário como "dado factual".**
   - O conjunto de referências do Lecionário é parte de um livro litúrgico oficial.
   - O projeto usa só referências obtidas de fontes com licença aberta, não do livro oficial.
   - Elas podem divergir pontualmente do Lecionário brasileiro. Quando as duas fontes abertas
     divergem, vale a que segue o Ordo Lectionum Missae (decisão do mantenedor), e a outra versão
     fica registrada em `docs/relatorios/lecionario-divergencias.md`.
3. **QR codes para buscas no YouTube.**
   - O livro aponta para buscas, não para vídeos específicos, e não endossa o que aparece.
   - Os resultados são conteúdo de terceiros. O aviso está na seção "Como usar".
4. **Leituras de Nossa Senhora Aparecida.**
   - Nenhuma fonte com licença aberta traz as leituras próprias da solenidade.
   - Decisão do mantenedor (2026-10-27): usar as **referências** (Est 5,1b-2;7,2b-3; Sl 44(45);
     Ap 12,1.5.13a.15-16a; Jo 2,1-11) do subsídio *Celebrar em Família* da CNBB, com crédito na
     página de créditos do livro. Nenhum texto do subsídio é reproduzido.
   - Entendimento: referência bíblica é dado factual (Lei 9.610/98, art. 8º). Caminho mais
     restritivo, se um dia for preciso: trocar pelas leituras do Comum de Nossa Senhora (fonte de
     domínio público) e manter o link para a liturgia oficial.
5. **Nomes das celebrações em português.**
   - Vêm do romcal (MIT) e de traduções da LitCal (Apache-2.0).
   - Nomes de celebrações são títulos curtos e factuais. Não foram copiados de livros
     litúrgicos protegidos.
