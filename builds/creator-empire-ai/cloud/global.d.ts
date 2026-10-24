// Next.js's own build pipeline handles CSS imports natively; this
// ambient declaration exists only so `tsc --noEmit` (our standalone
// `npm run typecheck`, run independent of `next build`) doesn't choke
// on `import "./globals.css"`.
declare module "*.css";
