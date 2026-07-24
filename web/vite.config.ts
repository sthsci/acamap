/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const repositoryName = process.env.GITHUB_REPOSITORY?.split('/').at(-1);
const pagesBase = repositoryName
  ? repositoryName.endsWith('.github.io')
    ? '/'
    : `/${repositoryName}/`
  : '/';

export default defineConfig({
  // GitHub Actions supplies GITHUB_REPOSITORY. Project Pages require the
  // repository subpath; owner Pages repositories are served from '/'.
  base: pagesBase,
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,
  },
});
