# CLASH AI - Vite Frontend

This is the frontend for the CLASH AI application, built with Vite, React, and TypeScript.

## Project Setup

### Prerequisites
*   **Node.js:** This project uses Node.js v20.
    *   An `.nvmrc` file is included in the project root. If you use Node Version Manager (nvm), run `nvm use` in the project directory to switch to the correct Node.js version.
    *   Otherwise, ensure Node.js v20.x is installed.
*   **npm:** (Node Package Manager) comes with Node.js.

### Installation
1.  Clone the repository (if you haven't already).
2.  Navigate to the project directory: `cd /path/to/CLASH-AI-Restored-Project`
3.  Install dependencies:
    ```bash
    npm install
    ```

## Development

### Key Scripts
*   **Start Development Server:**
    ```bash
    npm run dev
    ```
    This will start the Vite development server with Hot Module Replacement (HMR).

*   **Build for Production:**
    ```bash
    npm run build
    ```
    This command first runs the TypeScript compiler (`tsc`) to check for type errors, then uses Vite to build the application for production. The output will be in the `dist/` directory.
    **IMPORTANT: Always run this command locally and ensure it passes without errors *before* pushing changes intended for deployment.**

*   **Preview Production Build:**
    ```bash
    npm run preview
    ```
    This command serves the contents of the `dist/` directory locally, allowing you to test the production build before deploying.

## Core Technologies & Architecture

*   **Framework:** Vite + React
*   **Language:** TypeScript
*   **Styling:** Tailwind CSS
*   **Blog/Markdown Handling:**
    *   Markdown files for blog posts are located in `src/data/blogArticles/`.
    *   **Loading Mechanism:** Blog posts are loaded client-side using Vite's `import.meta.glob` feature in `src/utils/markdownLoader.ts`.
        *   **Critical Note:** This approach is browser-compatible. Avoid using Node.js-specific modules like `fs` (file system) or `path` directly in client-side code, as they will cause errors (e.g., `process is not defined`) in the browser or during the Vite build for client bundles.
    *   **Dependencies:**
        *   `gray-matter`: For parsing frontmatter from markdown files.
        *   `remark` & `remark-html`: For converting markdown content to HTML.

## Deployment

*   **Platform:** Netlify
*   **Connected Repository:** `findmikeymike/CLASH-AI`
*   **Deployment Branch:** `vite-project-final` (or `main` if merged)
*   **Build Command (on Netlify):** `npm run build` (or `tsc ; vite build` as defined in `package.json`)
*   **Publish Directory (on Netlify):** `dist`
*   **Node.js Version (on Netlify):** v20 (controlled by the `.nvmrc` file in the project root)

## Troubleshooting Common Issues

*   **Blank Page on Deploy / `process is not defined` Error:**
    *   **Cause:** Typically due to Node.js-specific code (e.g., `process.cwd()`, `fs`, `path`) being included in the client-side JavaScript bundle.
    *   **Solution:** Refactor the problematic code to use browser-compatible APIs or Vite-specific features (like `import.meta.glob` for loading multiple files, or environment variables prefixed with `VITE_`).

*   **TypeScript Errors During Build (`tsc` fails):**
    *   Read the error messages carefully. They usually point to the exact file and line number.
    *   **`Cannot find module '...' or its corresponding type declarations.`**:
        *   Ensure the module is listed in `package.json` and installed (`npm install`).
        *   If it's a JavaScript library, it might require separate type declarations (e.g., `npm install --save-dev @types/module-name`). Some modern libraries bundle their own types.
        *   If no types exist, you might consider creating a custom declaration file (`.d.ts`) or, in some cases, using `// @ts-ignore` sparingly if you are certain the code is correct.
    *   **`Property 'glob' does not exist on type 'ImportMeta'.`**:
        *   Ensure `src/vite-env.d.ts` exists and contains `/// <reference types="vite/client" />`.
        *   Ensure your `tsconfig.json` includes the `src` directory (e.g., `"include": ["src"]`).
        *   A clean `npm install` (after removing `node_modules` and `package-lock.json`) can sometimes resolve inconsistencies.
    *   **JSX errors (e.g., duplicate props, unknown props):**
        *   Check component usage against its definition or the documentation of the UI library being used.

*   **Netlify Build Fails:**
    *   **Examine Build Logs on Netlify:** The logs are the primary source for diagnosing Netlify-specific build failures.
    *   **Node.js Version:** Double-check that your `.nvmrc` file specifies a Node.js version compatible with your dependencies and supported by Netlify.
    *   **Build Command & Publish Directory:** Verify these are correctly set in your `netlify.toml` file or in the Netlify UI settings.
    *   **Dependencies:** Ensure all necessary `dependencies` (and `devDependencies` if needed by the build process) are correctly listed in `package.json`.

## Workflow Best Practices

*   **Local Build Before Push:** Re-iterating this because it's crucial: **Always run `npm run build` locally and resolve any errors *before* pushing your changes.** This will save a lot of time and prevent broken deployments.
*   **Atomic Commits:** Make small, focused commits with clear messages describing the changes.
*   **Branching:** Use feature branches for new work. Create Pull Requests (PRs) to merge changes into your main deployment branch (e.g., `vite-project-final` or `main`). This allows for code review and discussion.
*   **Environment Variables:** For any client-side accessible environment variables in Vite, they **must** be prefixed with `VITE_` (e.g., `VITE_API_URL`). Access them in your code via `import.meta.env.VITE_API_URL`. Do not store sensitive keys in client-side code; use backend functions for operations requiring secrets.