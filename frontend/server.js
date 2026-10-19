/**
 * Frontend & Pipeline Server for LedgerLens.
 * Serves the web UI, proxies requests to FastAPI, and triggers Mastra workflows.
 */

import express from 'express';
import cors from 'cors';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import multer from 'multer';
import dotenv from 'dotenv';
import { ledgerLensWorkflow } from '../workflow/index.ts';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.dirname(__dirname);

const app = express();
const PORT = process.env.FRONTEND_PORT || 3000;
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

const UPLOADS_DIR = path.join(ROOT_DIR, 'uploads');
if (!fs.existsSync(UPLOADS_DIR)) {
  fs.mkdirSync(UPLOADS_DIR, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOADS_DIR),
  filename: (req, file, cb) => cb(null, `${Date.now()}_${file.originalname}`),
});
const upload = multer({ storage });

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.use('/samples', express.static(path.join(ROOT_DIR, 'samples')));

// List available sample images
app.get('/api/samples', (req, res) => {
  const samplesDir = path.join(ROOT_DIR, 'samples');
  if (!fs.existsSync(samplesDir)) return res.json([]);
  const files = fs.readdirSync(samplesDir)
    .filter(f => f.endsWith('.png') || f.endsWith('.jpg') || f.endsWith('.jpeg'))
    .map(f => ({
      name: f,
      url: `/samples/${f}`,
      path: path.join(samplesDir, f),
    }));
  res.json(files);
});

// Run Mastra workflow pipeline
app.post('/api/pipeline/run', upload.single('image'), async (req, res) => {
  try {
    let targetImagePath = '';
    let imageName = 'image.png';

    if (req.file) {
      targetImagePath = req.file.path;
      imageName = req.file.originalname;
    } else if (req.body.samplePath) {
      targetImagePath = req.body.samplePath;
      imageName = path.basename(targetImagePath);
    } else {
      return res.status(400).json({ error: 'Must provide an image file or samplePath' });
    }

    console.log(`[Frontend Server] Triggering Mastra workflow on: ${targetImagePath}`);
    const run = await ledgerLensWorkflow.createRun();
    const result = await run.start({
      inputData: {
        imagePath: targetImagePath,
        imageName: imageName,
      },
    });

    res.json({
      success: true,
      data: result,
    });
  } catch (err) {
    console.error('[Frontend Server] Workflow execution error:', err);
    res.status(500).json({ error: err.message || 'Workflow execution failed' });
  }
});

// Proxy routes to FastAPI Backend
app.use('/api/backend', async (req, res) => {
  const targetSubPath = req.url.replace(/^\//, '');
  const targetUrl = `${BACKEND_URL.replace(/\/$/, '')}/${targetSubPath}`;

  try {
    const headers = { ...req.headers };
    delete headers.host;

    const options = {
      method: req.method,
      headers: {
        ...headers,
        'Content-Type': req.headers['content-type'] || 'application/json',
      },
    };

    if (['POST', 'PUT', 'PATCH'].includes(req.method) && req.body && Object.keys(req.body).length > 0) {
      options.body = JSON.stringify(req.body);
    }

    const backendRes = await fetch(targetUrl, options);
    
    // Pass headers
    const contentType = backendRes.headers.get('content-type') || 'application/json';
    const contentDisposition = backendRes.headers.get('content-disposition');
    res.setHeader('Content-Type', contentType);
    if (contentDisposition) {
      res.setHeader('Content-Disposition', contentDisposition);
    }

    if (contentType.includes('application/json') || contentType.includes('text/')) {
      const text = await backendRes.text();
      res.status(backendRes.status).send(text);
    } else {
      const buffer = await backendRes.arrayBuffer();
      res.status(backendRes.status).send(Buffer.from(buffer));
    }
  } catch (proxyErr) {
    console.error(`[Proxy Error] Failed to call ${targetUrl}:`, proxyErr.message);
    res.status(502).json({ error: `Backend unavailable: ${proxyErr.message}` });
  }
});

app.listen(PORT, () => {
  console.log(`LedgerLens Frontend & Orchestrator running on http://localhost:${PORT}`);
});
