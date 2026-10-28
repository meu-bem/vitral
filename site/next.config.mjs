// Site 100% estático (output: 'export'). Sem servidor, sem rastreadores.
const basePath = process.env.VITRAL_BASE_PATH || "";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  basePath,
  trailingSlash: true,
  images: { unoptimized: true },
  poweredByHeader: false,
  env: { VITRAL_BASE_PATH: basePath },
};

export default nextConfig;
