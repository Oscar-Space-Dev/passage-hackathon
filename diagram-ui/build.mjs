import { build } from 'esbuild';
import { cp, mkdir, copyFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const output = resolve(root, 'passage/static/diagram');
const dist = resolve(import.meta.dirname, 'node_modules/@excalidraw/excalidraw/dist/prod');
await mkdir(output, { recursive: true });
await build({
  entryPoints: [resolve(import.meta.dirname, 'src.jsx')],
  outfile: resolve(output, 'app.js'),
  bundle: true,
  minify: true,
  format: 'esm',
  target: ['es2022'],
  define: { 'process.env.NODE_ENV': '"production"' },
  loader: { '.svg': 'dataurl', '.png': 'dataurl' },
  logLevel: 'warning',
});
await copyFile(resolve(dist, 'index.css'), resolve(output, 'excalidraw.css'));
for (const folder of ['fonts', 'locales', 'data']) {
  await cp(resolve(dist, folder), resolve(output, folder), { recursive: true, force: true });
}
console.log('Schéma Excalidraw construit dans passage/static/diagram');
