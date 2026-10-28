// Exporta definições e calendários do romcal (Brasil, pt-BR) para cruzamento.
import { Romcal } from 'romcal';
import { Brazil_PtBr } from '@romcal/calendar.brazil';
import { writeFileSync, mkdirSync } from 'fs';
// O romcal não liga sozinho as opções do Brasil (NUALC 7); conferidas no Diretório 2025.
const romcal = new Romcal({ localizedCalendar: Brazil_PtBr, scope: 'liturgical', epiphanyOnSunday: true, ascensionOnSunday: true, corpusChristiOnSunday: false });
const defs = Object.values(await romcal.getAllDefinitions());
const names = {};
const days = {};
for (let y = 2024; y <= 2061; y++) {
  const cal = await romcal.generateCalendar(y);
  for (const [d, items] of Object.entries(cal)) {
    days[d] = items.map(i => ({ id: i.id, rank: i.rank, precedence: i.precedence, colors: i.colors, isOptional: i.isOptional }));
    for (const i of items) names[i.id] = i.name;
  }
}
mkdirSync('out', { recursive: true });
writeFileSync('out/definitions.json', JSON.stringify(defs.map(d => ({
  id: d.id, name: names[d.id] ?? null, dateDef: d.dateDef, dateExceptions: d.dateExceptions,
  precedence: d.precedence, rank: d.rank, colors: d.colors, properCycle: d.cycles?.properCycle,
  fromCalendarId: d.fromCalendarId, isOptional: d.isOptional,
})), null, 1));
writeFileSync('out/days.json', JSON.stringify(days));
console.log(defs.length, Object.keys(days).length);
