import { formatDate, loadCatalog } from "../lib/catalog";

const base = process.env.VITRAL_BASE_PATH || "";

export default function Inicio() {
  const { anos } = loadCatalog();
  const publicados = anos.filter((a) => a.publicado);
  const atual = publicados[publicados.length - 1];
  return (
    <>
      <section className="abertura">
        <h1>Vitral</h1>
        <p className="lead">Um livro por ano litúrgico com as referências das leituras da Missa de cada
          dia, para quem reza com a Palavra (lectio divina).</p>
        <p>Cada dia traz a data, o tempo e a cor litúrgica, as referências da 1ª leitura, do salmo, da
          2ª leitura e do evangelho, e QR codes para buscar o salmo e o evangelho no YouTube. O texto
          bíblico não vem impresso: use a sua Bíblia ou os links oficiais indicados no livro.</p>
      </section>
      {atual ? (
        <section className="destaque" aria-labelledby="ano-atual">
          <h2 id="ano-atual">{atual.titulo}</h2>
          <p>Ano {atual.ciclo_dominical} · de {formatDate(atual.inicio)} a {formatDate(atual.fim)}</p>
          <p><a className="botao" href={`${base}/livros/#ano-${atual.ano}`}>Baixar o livro</a></p>
        </section>
      ) : (
        <p>A lista de livros aparece aqui depois da primeira publicação.</p>
      )}
    </>
  );
}
