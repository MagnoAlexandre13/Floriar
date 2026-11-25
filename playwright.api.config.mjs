import {defineConfig} from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
import os from 'node:os';

// Cada execução usa um banco separado dos dados locais e das execuções anteriores.
const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'petal-api-browser-'));

export default defineConfig({
  testDir: './tests/api-browser',
  workers: 1,
  timeout: 30000,
  use: {baseURL: 'http://127.0.0.1:8001', channel: 'msedge', headless: true},
  webServer: [{
    command: 'python -B scripts/serve-api-tests.py',
    url: 'http://127.0.0.1:8001/api/health',
    reuseExistingServer: false,
    env: {PETAL_DB_PATH: path.join(directory, 'test.sqlite3')},
  }, {
    command: 'node scripts/serve.mjs',
    url: 'http://127.0.0.1:4174/conta.html',
    reuseExistingServer: false,
    env: {PETAL_FRONTEND_PORT: '4174', PETAL_API_PORT: '8001'},
  }],
});
