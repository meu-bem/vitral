// Lê o catalog.json gerado pelo pipeline dos livros. É a ÚNICA ligação do site com o pipeline:
// se o arquivo não existir, o site é gerado mesmo assim, sem a lista de livros.
import fs from "node:fs";
import path from "node:path";

const CANDIDATES = [process.env.VITRAL_CATALOG, "dados/catalog.json", "../dist/catalog.json"].filter(Boolean);

export function loadCatalog() {
  for (const rel of CANDIDATES) {
    const file = path.resolve(process.cwd(), rel);
    if (!fs.existsSync(file)) continue;
    try {
      const data = JSON.parse(fs.readFileSync(file, "utf8"));
      if (Array.isArray(data.anos)) return data;
    } catch (err) {
      console.warn(`catalog.json inválido em ${file}: ${err.message}`);
    }
  }
  console.warn("catalog.json não encontrado: o site sai sem a lista de livros.");
  return { anos: [], repositorio: null };
}

export function formatBytes(n) {
  if (n >= 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1).replace(".", ",")} MB`;
  return `${Math.round(n / 1024)} KB`;
}

export function formatDate(iso) {
  return iso.split("-").reverse().join("/");
}

export const FORMAT_LABELS = {
  pdf: { nome: "PDF", nota: "para ler na tela ou imprimir (A5)" },
  epub: { nome: "EPUB", nota: "para Kindle (Enviar para o Kindle) e outros leitores" },
  azw3: { nome: "AZW3", nota: "para copiar direto no Kindle pelo cabo" },
};
