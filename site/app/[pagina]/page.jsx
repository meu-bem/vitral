import { getPage, listPages } from "../../lib/content";

export const dynamicParams = false;

export function generateStaticParams() {
  return listPages().map((p) => ({ pagina: p.slug }));
}

export async function generateMetadata({ params }) {
  const { pagina } = await params;
  return { title: getPage(pagina).titulo };
}

export default async function Pagina({ params }) {
  const { pagina } = await params;
  const page = getPage(pagina);
  return (
    <article className="texto">
      <h1>{page.titulo}</h1>
      <div dangerouslySetInnerHTML={{ __html: page.html }} />
    </article>
  );
}
