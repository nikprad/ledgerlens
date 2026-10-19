import { createStep } from '@mastra/core/workflows';
import { z } from 'zod';
import { callBackend } from '../client.js';
import { transactionItemSchema } from './extractStep.js';

export const summarizeStep = createStep({
  id: 'summarize-step',
  description: 'Generates a plain-language weekly financial summary using local Gemma',
  inputSchema: z.object({
    imageName: z.string(),
    validItems: z.array(transactionItemSchema),
    forecast: z.any(),
    anomalies: z.any(),
  }),
  outputSchema: z.object({
    status: z.string(),
    imageName: z.string(),
    transactions: z.array(transactionItemSchema),
    summary: z.any(),
    forecast: z.any(),
    anomalies: z.any(),
  }),
  execute: async ({ inputData }) => {
    console.log(`[Mastra Workflow] Step 5: Generating financial summary...`);

    const summaryRes = await callBackend<any>('summarize', {
      method: 'POST',
    });

    console.log(`[Mastra Workflow] Step 5 complete: Summary: "${summaryRes.plain_language_summary.slice(0, 80)}..."`);

    return {
      status: 'success',
      imageName: inputData.imageName,
      transactions: inputData.validItems,
      summary: summaryRes,
      forecast: inputData.forecast,
      anomalies: inputData.anomalies,
    };
  },
});
