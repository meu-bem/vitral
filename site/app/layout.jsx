import "./globals.css";
import { listPages } from "../lib/content";

const base = process.env.VITRAL_BASE_PATH || "";

export const metadata = {
  title: { default: "Vitral", template: "%s · Vitral" },
  description: "Livros anuais com as referências das leituras litúrgicas, para lectio divina.",
};

export default function RootLayout({ children }) {
  const pages = listPages().filter((p) => p.menu);
  return (
    <html lang="pt-BR">
      <body>
        <a className="pular" href="#conteudo">Pular para o conteúdo</a>
        <header className="topo">
          <a href={`${base}/`} className="marca">Vitral</a>
          <nav aria-label="Principal">
            <ul>
              <li><a href={`${base}/livros/`}>Livros</a></li>
              {pages.map((p) => (
                <li key={p.slug}><a href={`${base}/${p.slug}/`}>{p.titulo}</a></li>
              ))}
            </ul>
          </nav>
        </header>
        <main id="conteudo">{children}</main>
        <footer className="rodape">
          <p>Código sob licença MIT. Conteúdo original sob CC BY-SA 4.0. Os livros trazem referências
            bíblicas e links, não o texto das leituras.</p>
          <p>Este site não usa rastreadores nem cookies.</p>
        </footer>
      </body>
    </html>
  );
}
