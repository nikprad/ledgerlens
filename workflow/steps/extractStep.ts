import { createStep } from '@mastra/core/workflows';
import { z } from 'zod';
import { callBackend } from '../client.js';

export const transactionItemSchema = z.object({
  id: z.number().optional().nullable(),
  date: z.string(),
  party: z.string(),
  item: z.string(),
  quantity: z.number(),
  amount: z.number(),
  currency: z.string(),
  type: z.enum(['sale', 'expense']),
  confidence: z.number(),
  flagged: z.boolean().default(false),
  flag_reason: z.string().optional().nullable(),
});

export const extractStep = createStep({
  id: 'extract-step',
  description: 'Extracts handwritten ledger rows into strict JSON using Gemma multimodal via Ollama',
  inputSchema: z.object({
    imagePath: z.string(),
    imageName: z.string().default('image.png'),
  }),
  outputSchema: z.object({
    imageName: z.string(),
    rawItems: z.array(transactionItemSchema),
    latencyMs: z.number(),
  }),
  execute: async ({ inputData }) => {
    console.log(`[Mastra Workflow] Step 1: Extracting from ${inputData.imageName}...`);
    
    // Call FastAPI /extract endpoint using form-encoded body
    const formData = new URLSearchParams();
    formData.append('image_path', inputData.imagePath);

    const result = await callBackend<{
      status: string;
      image_name: string;
      items: any[];
      latency_ms: number;
    }>('extract', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    console.log(`[Mastra Workflow] Step 1 complete: ${result.items.length} raw items extracted in ${result.latency_ms}ms`);

    return {
      imageName: inputData.imageName,
      rawItems: result.items,
      latencyMs: result.latency_ms,
    };
  },
});
