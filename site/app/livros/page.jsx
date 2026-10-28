import { FORMAT_LABELS, formatBytes, formatDate, loadCatalog } from "../../lib/catalog";

export const metadata = { title: "Livros" };

const ORDER = ["pdf", "epub", "azw3"];

export default function Livros() {
  const { anos } = loadCatalog();
  const lista = [...anos].sort((a, b) => b.ano - a.ano);
  return (
    <>
      <h1>Livros</h1>
      <p>Um arquivo por ano litúrgico, do 1º Domingo do Advento ao sábado anterior ao Advento seguinte.
        Os anos futuros já ficam disponíveis como <em>pré-gerados</em> e são publicados oficialmente
        um mês antes do Advento.</p>
      {lista.length === 0 && <p>Nenhum livro publicado ainda.</p>}
      {lista.map((a) => (
        <section key={a.ano} id={`ano-${a.ano}`} className="ano" aria-labelledby={`t-${a.ano}`}>
          <h2 id={`t-${a.ano}`}>
            {a.titulo} {!a.publicado && <span className="selo">pré-gerado</span>}
          </h2>
          <p className="detalhe">
            Ano {a.ciclo_dominical} · ciclo ferial {a.ciclo_ferial} · {formatDate(a.inicio)} a {formatDate(a.fim)}
            {a.dias_com_lacuna > 0 && <> · {a.dias_com_lacuna} dias com algum dado ainda a conferir</>}
          </p>
          <ul className="formatos">
            {Object.entries(a.formatos)
              .sort(([x], [y]) => ORDER.indexOf(x) - ORDER.indexOf(y))
              .map(([fmt, f]) => (
              <li key={fmt}>
                <a href={f.url} className="botao" download>{FORMAT_LABELS[fmt]?.nome ?? fmt.toUpperCase()}</a>
                <span className="nota"> {FORMAT_LABELS[fmt]?.nota} · {formatBytes(f.bytes)}</span>
                <details>
                  <summary>Verificar o arquivo (SHA-256)</summary>
                  <code>{f.sha256}</code>
                </details>
              </li>
            ))}
          </ul>
          <p className="detalhe">
            {a.calendario?.png && <><a href={a.calendario.png.url}>Calendário do ano (PNG)</a> · </>}
            {a.calendario?.svg && <><a href={a.calendario.svg.url}>SVG</a> · </>}
            <a href={a.release}>Página da versão</a>
          </p>
        </section>
      ))}
    </>
  );
}
