import { createStep } from '@mastra/core/workflows';
import { z } from 'zod';
import { callBackend } from '../client.js';
import { transactionItemSchema } from './extractStep.js';

export const forecastStep = createStep({
  id: 'forecast-step',
  description: 'Runs TabPFN on historical ledger transactions for 30-day cash flow projection and anomaly detection',
  inputSchema: z.object({
    imageName: z.string(),
    validItems: z.array(transactionItemSchema),
    storedCount: z.number().optional(),
  }),
  outputSchema: z.object({
    imageName: z.string(),
    validItems: z.array(transactionItemSchema),
    forecast: z.any(),
    anomalies: z.any(),
  }),
  execute: async ({ inputData }) => {
    console.log(`[Mastra Workflow] Step 4: Running TabPFN Forecasting & Anomaly Detection...`);

    // Call /forecast and /anomalies concurrently
    const [forecastRes, anomaliesRes] = await Promise.all([
      callBackend<any>('forecast?days=30', { method: 'POST' }),
      callBackend<any>('anomalies', { method: 'POST' }),
    ]);

    console.log(`[Mastra Workflow] Step 4 complete: Forecast status '${forecastRes.status}', ${anomaliesRes.anomalies_found} anomalies flagged.`);

    return {
      imageName: inputData.imageName,
      validItems: inputData.validItems,
      forecast: forecastRes,
      anomalies: anomaliesRes,
    };
  },
});
