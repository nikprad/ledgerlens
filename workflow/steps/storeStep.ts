import { createStep } from '@mastra/core/workflows';
import { z } from 'zod';
import { callBackend } from '../client.ts';
import { transactionItemSchema } from './extractStep.ts';

export const storeStep = createStep({
  id: 'store-step',
  description: 'Persists validated transactions to local SQLite database with zero cloud egress',
  inputSchema: z.object({
    imageName: z.string(),
    validItems: z.array(transactionItemSchema),
    droppedDuplicates: z.number().optional(),
    flaggedItemsCount: z.number().optional(),
    summaryMessage: z.string().optional(),
  }),
  outputSchema: z.object({
    imageName: z.string(),
    validItems: z.array(transactionItemSchema),
    storedCount: z.number(),
  }),
  execute: async ({ inputData }) => {
    console.log(`[Mastra Workflow] Step 3: Storing ${inputData.validItems.length} transactions to SQLite...`);

    const result = await callBackend<{
      status: string;
      inserted_count: number;
      ids: number[];
    }>('store', {
      method: 'POST',
      body: JSON.stringify(inputData.validItems),
    });

    console.log(`[Mastra Workflow] Step 3 complete: ${result.inserted_count} rows persisted.`);

    return {
      imageName: inputData.imageName,
      validItems: inputData.validItems,
      storedCount: result.inserted_count,
    };
  },
});
