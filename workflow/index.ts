/**
 * LedgerLens Mastra Orchestrator
 * Chains steps: extract -> validate -> store -> forecast -> summarize
 */

import { createWorkflow } from '@mastra/core/workflows';
import { z } from 'zod';
import { extractStep } from './steps/extractStep.js';
import { validateStep } from './steps/validateStep.js';
import { storeStep } from './steps/storeStep.js';
import { forecastStep } from './steps/forecastStep.js';
import { summarizeStep } from './steps/summarizeStep.js';

export const ledgerLensWorkflow = createWorkflow({
  id: 'ledgerlens-pipeline',
  inputSchema: z.object({
    imagePath: z.string(),
    imageName: z.string().default('image.png'),
  }),
  outputSchema: z.object({
    status: z.string(),
    imageName: z.string(),
    transactions: z.array(z.any()),
    summary: z.any(),
    forecast: z.any(),
    anomalies: z.any(),
  }),
})
  .then(extractStep)
  .then(validateStep)
  .then(storeStep)
  .then(forecastStep)
  .then(summarizeStep)
  .commit();
