# Tradução das passagens: critérios

A tradução é feita por IA (Claude) sob responsabilidade e edição de Mateus Santos, a partir de
`sblgnt` (Novo Testamento), `oshb` (Antigo Testamento) e, nos deuterocanônicos, `clementina`
(ver `docs/FONTES.md`). Não há texto de interpretação gerado por IA. Sugestões de leitores: `CONTRIBUINDO.md`.

## Estilo (decisões do mantenedor, 2026-10-29)

- Português do Brasil, registro litúrgico: **vós** no plural ("Preparai", "Eu vos batizei"); **tu** no singular.
- O nome divino (YHWH, Yah) é traduzido **"Senhor"**.
- Aspas duplas curvas (“ ”); aspas internas, simples (‘ ’). Nada de «».
- Cada versículo começa com maiúscula, mesmo quando continua uma frase do anterior. A citação abre no
  versículo em que a fala começa e fecha onde termina, ainda que em versículos diferentes.
- Títulos de salmos (“De Davi.”, “Cântico das subidas.”, “Aleluia.”) ficam no campo `titulo` do versículo 1,
  fora de `texto`: o Lecionário numera o v. 1 sem o título, e o livro não o imprime. Onde o Lecionário cita
  letras no v. 1 (Sl 28(29), 130(131), 143(144)), o título é também `partes[0]` (a letra `a`).
- Ordem das palavras e vocabulário seguem o original, sem consultar tradução portuguesa existente.
  Trechos muito conhecidos têm risco de coincidir com versões protegidas; ver revisão por amostragem abaixo.

## Daniel

`DAN.yaml` usa a numeração católica (a do Lecionário) no cap. 3 e nos caps. 13 e 14: Dn 3,24-90 (oração de
Azarias e cântico dos três jovens), Dn 13 (Susana) e Dn 14 (Bel e o dragão) vêm do latim da Clementina, com `observacao`
no primeiro versículo de cada trecho; Dn 3,91-100 é o aramaico 3,24-33. O resto do livro vem do hebraico/aramaico (OSHB).

## Deuteronômio

Os discursos de Moisés, sem verbo de dizer, vão sem aspas; falas citadas dentro deles levam aspas duplas (“ ”).
Dt 6,4: “o Senhor é nosso Deus, o Senhor é um só”, com `observacao` para a outra construção possível.

## Deuterocanônicos e acréscimos gregos

Tobias, Judite, Sabedoria, Baruc e 1-2 Macabeus vêm do latim da Clementina, com `observacao` no primeiro versículo
traduzido de cada livro. Onde a numeração da Clementina difere da do Lecionário (Nova Vulgata), o versículo usa a
numeração do Lecionário e a `observacao` diz onde está no latim:

- Jt 13,18-20 = Clementina 13,23-26. A Clementina não traz a frase “Que Deus faça isto por ti em exaltação perpétua…”
  de Jt 13,20 (Nova Vulgata).
- Est 4,17a-t (oração de Mardoqueu e de Ester, acréscimos gregos) = Clementina Est 13,8–14,14. O hebraico não os traz.
  A divisão em letras é reconstruída e pode diferir da do Lecionário; o resto de Ester vem do hebraico (OSHB).

## Qual texto seguir

Segue-se o texto-base de cada fonte (SBLGNT, OSHB). Onde ele diverge da Nova Vulgata, base do Lecionário,
o versículo traz `observacao` e entra na lista abaixo. Não se mistura outra leitura ao texto.

| Passagem | Texto-base | Nova Vulgata / Lecionário |
|---|---|---|
| Mc 1,1 | Jesus Cristo | Jesus Cristo, Filho de Deus |
| Mc 1,41 | “irado” | “movido de compaixão” |
| Mc 7,16; 9,44; 9,46; 11,26; 15,28 | versículo ausente (listado em `omitidos`) | versículo presente |
| Mc 9,29 | “mediante a oração” | “mediante a oração e o jejum” |
| Mc 16,9-20 | entre colchetes duplos (final longo, provavelmente posterior) | incluído |
| Mt 12,47; 21,44 | versículo mantido, mas alguns manuscritos o omitem | versículo presente |
| Mt 17,21; 18,11; 23,14 | versículo ausente (listado em `omitidos`) | versículo presente |
| Mt 27,16-17 | “Jesus Barrabás” | “Barrabás” |
| Lc 17,36; 23,17 | versículo ausente (listado em `omitidos`) | versículo presente |
| Lc 22,19b-20; 22,43-44; 23,34a; 24,12; 24,40; 24,51-52 | trecho entre colchetes (texto longo; alguns manuscritos o omitem), mantido | trecho presente |
| Jo 1,18 | “o Deus unigênito” | “Filho unigênito” |
| Jo 1,34 | “o Escolhido de Deus” | “Filho de Deus” |
| Jo 5,4 | versículo ausente (listado em `omitidos`) | versículo presente |
| Jo 6,69 | “o Santo de Deus” | “o Cristo, o Filho de Deus” |
| Jo 7,53–8,11 | entre colchetes duplos (a mulher adúltera; ausente dos manuscritos mais antigos), mantido | passagem presente |
| At 8,37; 15,34; 24,7; 28,29 | versículo ausente (listado em `omitidos`) | versículo presente |
| Rm 16,25-27 | ausente do SBLGNT; traduzido do Nestle 1904 (domínio público, `data/fontes/nestle1904/`) | presente |
| 1Cor 11,24 | “o meu corpo, que é para vós” | “o meu corpo, que será entregue por vós” |
| Hb 2,9 | “à parte de Deus” | “pela graça de Deus” |
| Jd 5 | “Jesus” (outros manuscritos: “o Senhor”, “Deus”) | conferir com o Lecionário |
| Is 7,14 | “a jovem está grávida” | “a virgem conceberá” |
| 1Rs 19,12 | “o som de um silêncio sutil” | “o sopro de uma brisa leve” |
| Gn 3,15 | “ele te ferirá a cabeça” | “ela te ferirá a cabeça” (em algumas edições) |
| Gn 4,8 | as palavras de Caim não constam | “Vamos ao campo” |
| Gn 49,10 | “até que venha Silo” | “até que venha aquele a quem pertence” |
| Sl 8,6 | “pouco menor que Deus” (Elohim) | “pouco menor que os anjos” |
| Sl 27,13 | “Ah, se eu não tivesse confiado em ver…” (pontos extraordinários sobre “se não”) | “Creio que verei…” |
| Sl 40,7 | “abriste-me os ouvidos” | “preparaste-me um corpo” (Hb 10,5, segundo a Septuaginta) |
| Sl 100,3 | “e somos seus” (qere; o ketiv traz “e não nós”) | “e somos seus” |
| Sl 145,13cd | ausente do hebraico; traduzido da Vulgata (“O Senhor é fiel em todas as suas palavras…”) | presente |
| Mc 16,8 | acrescenta, entre colchetes duplos, um final breve; não traduzido | sem o final breve |

## Controle de qualidade

- Cada versículo tem `status`: `ia-sem-revisao` ou `revisado` (só depois de revisão humana).
- `make traducao` valida o esquema e a cobertura das referências do Lecionário (`COMPLETO=1` falha se faltar algo).
- Conferência por amostragem dos trechos mais conhecidos, por quem tiver acesso a outras traduções, só para
  detectar coincidências de redação.
