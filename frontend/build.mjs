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
  // Chromium 80, not the newest thing that parses locally. Fire OS 7 tablets
  // run a WebView below 85, where an es2021 bundle threw a SyntaxError on
  // evaluation and the card never registered. 80 keeps `??` and `?.` native
  // and costs ~1.3 KB to transpile the rest. See test/bundle-target.test.ts.
  target: ["chrome80", "safari14", "firefox78"],
  legalComments: "none",
  banner: {
    js: "/* Pareto card -- built from frontend/src, do not edit by hand. */",
  },
});
