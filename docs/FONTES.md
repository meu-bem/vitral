# Fontes

Registro de toda fonte usada para dados ou para conferir algoritmos. Cada
entrada tem um id (usado em `fontes:` nos arquivos de `data/`), URL, licença,
data de acesso e o que foi aproveitado.

Política: não copiamos texto de leitura, oração ou comentário. Destas fontes
saem só **fatos** (datas, graus, cores, regras de transferência) e **referências
bíblicas**. Os testes verificam **regras** em todos os anos de 2024 a 2060, sem
reproduzir datas tiradas de publicações com direitos reservados.

## Fontes usadas na fase 1 (calendário)

### `nualc`: Normas Universais sobre o Ano Litúrgico e o Calendário

- URL: <https://www.liturgyoffice.org/Calendar/Info/GNLY.pdf> (tradução inglesa, Liturgy Office, Conferência Episcopal da Inglaterra e País de Gales)
- Texto oficial latino aprovado pela carta *Mysterii Paschalis* (Paulo VI, 14/2/1969): <https://www.vatican.va/content/paul-vi/la/motu_proprio/documents/hf_p-vi_motu-proprio_19690214_mysterii-paschalis.pdf>
- Licença: texto protegido (LEV / tradução ICEL). Não reproduzido.
- Acesso: 2026-10-27
- Aproveitado: regras implementadas em código, citadas pelo número: nn. 5-7 (domingo e transferências), 14-16 (memórias, dias de semana), 22-44 (tempos), 35 (oitava do Natal), 56 (São José), 59 (Tabela dos Dias Litúrgicos), 60 (ocorrência e transferência).

### `igmr`: Instrução Geral do Missal Romano, n. 346 (cores)

- URL: <https://www.usccb.org/prayer-and-worship/the-mass/general-instruction-of-the-roman-missal/girm-chapter-6>
- Licença: texto protegido. Não reproduzido.
- Acesso: 2026-10-27
- Aproveitado: cores do próprio do tempo (roxo no Advento e Quaresma, rosa opcional no 3º Domingo do Advento e no 4º da Quaresma, vermelho em Ramos, Sexta-feira Santa e Pentecostes, branco no Natal e na Páscoa, verde no Tempo Comum).

### Documentos da Santa Sé (regras)

Textos oficiais publicados pela Santa Sé, usados só como **regra** implementada em código
(nada é reproduzido além da citação).

- `decreto-sccd-1977`: Sagrada Congregação para os Sacramentos e o Culto Divino, decreto
  *De celebratione Baptismatis Domini*, 7/10/1977, AAS 69 (1977) 682-683
  (<https://www.vatican.va/archive/aas/documents/AAS-69-1977-ocr.pdf>). Regra: onde a Epifania
  vai para o domingo e cai em 7 ou 8 de janeiro, o Batismo do Senhor passa para a segunda-feira
  seguinte. Acesso: 2026-10-27.
- `ccdds-2018-mater-ecclesiae`: Congregação para o Culto Divino e a Disciplina dos Sacramentos,
  *Notificação sobre a memória da Bem-Aventurada Virgem Maria, Mãe da Igreja*, 24/3/2018
  (<https://www.vatican.va/roman_curia/congregations/ccdds/documents/rc_con_ccdds_doc_20180324_notificazione-mater-ecclesiae_en.html>).
  Regras: as leituras da memória são próprias; coincidindo com a memória de um santo, prevalece
  a memória da Virgem Maria ("tradição de preeminência entre as pessoas"); o Imaculado Coração é
  citado como caso análogo. Acesso: 2026-10-27.
- `ccdds-2020-calendario-2022`: Congregação para o Culto Divino e a Disciplina dos Sacramentos,
  *Responsum ad dubia de calendario liturgico exarando pro anno 2022*, 11/5/2020
  (cópia arquivada: <https://web.archive.org/web/2020/http://www.cultodivino.va/content/dam/cultodivino/documenti/DUBIA/Calendario%202022.pdf>).
  Aplica a NUALC n. 60: a Natividade de São João Batista, coincidindo com o Sagrado Coração,
  vai para o dia livre **anterior** (23/6). O Vitral usa essa leitura do n. 60 em todo caso de
  solenidade impedida: o dia livre mais próximo e, em empate, o anterior. Acesso: 2026-10-27.

### Diretórios da Liturgia (só regras gerais, sem datas)

- `diretorio-omb-2025`: Diretório Litúrgico Pastoral 2025, Ordinariado Militar do Brasil, base
  CNBB (<https://arquidiocesemilitar.org.br/wp-content/uploads/2025/01/DIRETORIO-LITURGICO-OMB-2025-1_compressed.pdf>).
  Todos os direitos reservados. Consultado para as **regras** nacionais: celebrações levadas ao
  domingo no Brasil (Epifania, Ascensão, Assunção, São Pedro e São Paulo, Todos os Santos),
  Corpus Christi na quinta-feira e a concessão da Santa Sé para a Imaculada permanecer no
  domingo do Advento. Nenhuma data ou referência dele está no repositório. Acesso: 2026-10-27.
- `diretorio-cnbb-2022`: Diretório da Liturgia da Igreja no Brasil 2022 (CNBB). Todos os
  direitos reservados. Consultado só para a **regra** de que essas transferências vão para o
  domingo **seguinte** (e não para o mais próximo). Nenhuma data ou referência dele está no
  repositório. Acesso: 2026-10-27.

### Orientações e subsídios publicados

- `cnbb-finados-2025`: orientação da CNBB sobre 1º e 2 de novembro, reproduzida em
  <https://www.acidigital.com/noticia/64849/comemoracao-dos-fieis-defuntos-tem-precedencia-sobre-o-domingo-em-1o-de-novembro-diz-cnbb>.
  Regra: quando o domingo seguinte a 1º/11 é Finados, Todos os Santos fica no sábado 1º/11.
- `diocese-sjc-2024`: folheto da Missa de São Pedro e São Paulo (Diocese de São José dos Campos),
  <https://diocese-sjc.org.br/wp-content/uploads/2024/05/30-de-junho-de-2024-SOLENIDADE-DE-SAO-PEDRO-E-SAO-PAULO-APOSTOLOS-MISSA-DO-DIA-.pdf>.
  Confirma a transferência para o domingo seguinte mesmo quando 29/6 é sábado.
- `cnbb-celebrar-em-familia-aparecida`: CNBB, Comissão Episcopal Pastoral para a Liturgia,
  subsídio *Celebrar em Família — Nossa Senhora da Conceição Aparecida* (2021),
  <https://www.cnbb.org.br/wp-content/uploads/2021/10/56-Celebrar-e-Familia-NSraAparecida.pdf>.
  Aproveitado (decisão do mantenedor, 2026-10-27): **só as referências** das leituras da
  solenidade (Est 5,1b-2;7,2b-3; Sl 44(45); Ap 12,1.5.13a.15-16a; Jo 2,1-11), em
  `data/lecionario/proprio-brasil.yaml`, com crédito na página de créditos do livro. O subsídio
  não indica os versículos do salmo. Acesso: 2026-10-27.

## Fontes de dados (fase 3)

Todas estão copiadas em `data/fontes/`, com a licença ao lado, para que a importação
possa ser refeita sem internet. O build não lê nada disto: só os importadores
(`scripts/ingest_*.py`) e os testes de cruzamento.

### `romcal`: romcal, calendário do Brasil em pt-BR

- Projeto: <https://github.com/romcal/romcal> (licença **MIT**), pacotes npm `romcal@3.0.0-dev.143` e `@romcal/calendar.brazil@3.0.0-dev.143`; commit consultado `0a56602dc8167bf45731886df541252033f90cae` (2026-10-26)
- Acesso: 2026-10-27
- Extraído com `data/fontes/romcal/export.mjs`: definições das celebrações (`data/fontes/romcal/definitions.json`: id, nome em pt-BR, data, grau, cor) e o calendário de 2024 a 2061 para cruzamento (`tests/fixtures/romcal-brasil-2024-2061.json.gz`, só ids).
- Usado como base de `data/calendario/santos.yaml` (nomes, datas, graus, cores).
- Correções em relação ao romcal (com fonte): Epifania e Ascensão no domingo (o romcal não liga essas opções para o Brasil); Assunção e São Pedro e São Paulo no domingo **seguinte** (`diretorio-cnbb-2022`, `diocese-sjc-2024`); Imaculada no domingo do Advento (`diretorio-omb-2025`); Todos os Santos no sábado quando Finados cai no domingo (`cnbb-finados-2025`); João Batista impedido no dia anterior (`ccdds-2020-calendario-2022`); memória mariana prevalecendo (`ccdds-2018-mater-ecclesiae`). Relatório: `docs/relatorios/calendario-divergencias.md`.
- Critério de conferência do próprio dos santos: vale a maioria (romcal + uma das outras duas fontes de acordo em data e grau). O calendário tâmil é o da Índia e tem ajustes nacionais.

### `litcal`: Liturgical Calendar API

- Projeto: <https://github.com/Liturgical-Calendar/LiturgicalCalendarAPI> (licença **Apache-2.0**), branch `development`, commit `df092ae9838ead1b662ea4f3a670a16cd34841a8` (2026-10-24)
- Acesso: 2026-10-27
- Copiado: `jsondata/sourcedata/rite/roman/lectionary/*/en.json` (referências do lecionário em inglês, **parciais**), `missals/propriumdesanctis_{1970,2002,2008}` (datas e graus do calendário geral, nomes em português) e `decrees/decrees.json`.
- Usado para conferir datas e graus do próprio dos santos e como segunda fonte das referências do lecionário (numeração hebraica dos versículos, a do lecionário dos EUA).

### `lecionario-tamil`: Tamil Catholic Lectionary (jayarathina)

- Projeto: <https://github.com/jayarathina/Tamil-Catholic-Lectionary> (**Unlicense**, domínio público), commit `c6c9d79d0f56721f6cc17fb8370d089f0dcd5fd2`
- Acesso: 2026-10-27
- Copiado: `MySQL/liturgy_lectionary_table_readings__list.sql` (**só a tabela de referências**; a tabela com o texto bíblico em tâmil não foi copiada), `liturgy_lectionary_table_generalcalendar.sql` (datas e graus) e `lib/TamilLectionary/TamilLectionaryUtil.php` (tabela de abreviações dos livros).
- É a única fonte licenciada encontrada com o lecionário **completo** (domingos A/B/C, dias de semana I/II, tempos fortes e santos). Usa a versificação inglesa; os versículos são convertidos para a hebraica com `versificacao`.
- Também indica se uma memória tem leituras próprias (memórias sem remissão aos comuns).

### `versificacao`: mapas de versificação da Copenhagen Alliance

- Projeto: <https://github.com/Copenhagen-Alliance/versification-specification>, commit `519af776ab65d89a51e37f750779250f940459ef`; dados sob **CC BY-SA 4.0** (código Apache-2.0)
- Acesso: 2026-10-27
- Copiado: `versification-mappings/standard-mappings/eng.json`, `org.json` e `vul.json`.
- Usado para converter versículos da numeração inglesa para a hebraica (ex.: Ml 4,1 → Ml 3,19; títulos dos salmos), saber quantos versículos tem cada capítulo e numerar Daniel 3 como nas Bíblias católicas (Dn 3,24-90 = cântico grego; hebraico 3,24-33 = 3,91-100).
- Versículo sem mapa próprio, vizinho de um deslocado, é deduzido pela posição do vizinho (ex.: Is 64,1 inglês → Is 63,19). Os casos ficam listados em `docs/relatorios/lecionario-divergencias.md`. Como o lecionário gerado é derivado desses mapas, os dados de `data/lecionario/` seguem a licença CC BY-SA 4.0 (a mesma do conteúdo do projeto).

### Convenções brasileiras de citação

- Abreviações dos livros e a forma dos salmos ("Sl 50(51)", "Sl 115(116B)", "Sl 146(147A)", "Sl 113A(114)") seguem a convenção usada nos lecionários brasileiros. **Rt, Jt, Lm, Ab, Jd** seguem o mesmo padrão (marcadas em `src/vitral/bible.py`).

## Relatórios de cruzamento

- `docs/relatorios/santos-divergencias.md`: próprio dos santos, romcal × LitCal × calendário tâmil.
- `docs/relatorios/lecionario-divergencias.md`: referências, lecionário tâmil × LitCal.
- `docs/relatorios/calendario-divergencias.md`: calendário completo 2024-2060, Vitral × romcal. Toda divergência precisa de explicação (teste `tests/test_cross_romcal.py`).

## Fontes avaliadas e não usadas

- Sites de liturgia diária (CNBB, Paulus, Canção Nova): só como **links**; não são raspados. A API da Liturgia Diária da CNBB exige autorização e não foi usada.
- Lecionários com licença GPL ou sem licença declarada, e lecionários de outras tradições (Lecionário Comum Revisado): não usados.

## Decisões do mantenedor sobre os dados (2026-10-27)

- **Divergência entre as fontes do Lecionário:** vale o lecionário tâmil, que segue o Ordo
  Lectionum Missae; a versão da LitCal (lecionário adaptado dos EUA) fica registrada em
  `divergencia` e no relatório, para revisão.
- **Nossa Senhora Aparecida:** referências tiradas do subsídio da CNBB, com crédito.
