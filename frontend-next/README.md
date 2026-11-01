# Imena Next.js interface

This directory contains the Next.js App Router interface for the marketplace. It keeps the existing Vite frontend intact and reuses its live marketplace flows: business discovery and profiles, product stock and cash checkout, date-based booking, phone-based tracking, account login, and verified-purchase reviews.

The app proxies `/api/*` to the local Django API at `http://127.0.0.1:8000/api/*` through `next.config.ts`.

## Run

From this directory, install dependencies and start the app:

```powershell
npm install
npm run dev
```

The requested shadcn command is:

```powershell
pnpm dlx shadcn@latest init --preset b7kDghiZn9 --template next --rtl
```

It could not run in the current workspace: `pnpm` is not installed, and Corepack could not fetch it because connections to `registry.npmjs.org` are rejected (`EACCES`). The Next.js App Router structure, Radix Nova configuration with RTL enabled, reusable button primitive, and Imena marketplace theme are scaffolded here manually. Once registry access is available, run the command above from this directory to apply the preset itself.
