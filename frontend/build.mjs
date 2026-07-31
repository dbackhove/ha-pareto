// Builds the card into the integration, where Home Assistant serves it from.
// The output is committed: HACS ships the repository as it stands, so nobody
// downstream ever runs this.
import { build } from "esbuild";

await build({
  entryPoints: ["src/pareto-card.ts"],
  outfile: "../custom_components/pareto/www/pareto-card.js",
  bundle: true,
  minify: true,
  format: "iife",
  target: "es2021",
  legalComments: "none",
  banner: {
    js: "/* Pareto card -- built from frontend/src, do not edit by hand. */",
  },
});
