// Seções extras do site: cada arquivo em site/content/*.md vira uma página /<nome>/.
// Front matter mínimo entre linhas "---": titulo, ordem (número) e menu (sim|nao).
import fs from "node:fs";
import path from "node:path";
import MarkdownIt from "markdown-it";

const DIR = path.join(process.cwd(), "content");
const md = new MarkdownIt({ html: false, linkify: true, typographer: true });

function parse(raw) {
  const meta = {};
  let body = raw;
  if (raw.startsWith("---\n")) {
    const end = raw.indexOf("\n---", 4);
    for (const line of raw.slice(4, end).split("\n")) {
      const i = line.indexOf(":");
      if (i > 0) meta[line.slice(0, i).trim()] = line.slice(i + 1).trim();
    }
    body = raw.slice(end + 4);
  }
  return { meta, body };
}

export function listPages() {
  if (!fs.existsSync(DIR)) return [];
  return fs
    .readdirSync(DIR)
    .filter((f) => f.endsWith(".md") && f.toLowerCase() !== "readme.md")
    .map((f) => {
      const slug = f.replace(/\.md$/, "");
      const { meta } = parse(fs.readFileSync(path.join(DIR, f), "utf8"));
      return { slug, titulo: meta.titulo || slug, ordem: Number(meta.ordem || 99), menu: meta.menu !== "nao" };
    })
    .sort((a, b) => a.ordem - b.ordem || a.slug.localeCompare(b.slug));
}

export function getPage(slug) {
  const { meta, body } = parse(fs.readFileSync(path.join(DIR, `${slug}.md`), "utf8"));
  return { titulo: meta.titulo || slug, html: md.render(body) };
}
