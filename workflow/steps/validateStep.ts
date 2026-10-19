import { createStep } from '@mastra/core/workflows';
import { z } from 'zod';
import { callBackend } from '../client.js';
import { transactionItemSchema } from './extractStep.js';

export const validateStep = createStep({
  id: 'validate-step',
  description: 'Normalizes dates/currency, drops exact duplicates, and flags low confidence without silently mutating amounts',
  inputSchema: z.object({
    imageName: z.string(),
    rawItems: z.array(transactionItemSchema),
    latencyMs: z.number().optional(),
  }),
  outputSchema: z.object({
    imageName: z.string(),
    validItems: z.array(transactionItemSchema),
    droppedDuplicates: z.number(),
    flaggedItemsCount: z.number(),
    summaryMessage: z.string(),
  }),
  execute: async ({ inputData }) => {
    console.log(`[Mastra Workflow] Step 2: Validating ${inputData.rawItems.length} transactions...`);

    const result = await callBackend<{
      valid_items: any[];
      dropped_duplicates: number;
      flagged_items_count: number;
      summary_message: string;
    }>('validate', {
      method: 'POST',
      body: JSON.stringify(inputData.rawItems),
    });

    console.log(`[Mastra Workflow] Step 2 complete: ${result.valid_items.length} valid items, ${result.dropped_duplicates} dropped duplicates, ${result.flagged_items_count} flagged.`);

    return {
      imageName: inputData.imageName,
      validItems: result.valid_items,
      droppedDuplicates: result.dropped_duplicates,
      flaggedItemsCount: result.flagged_items_count,
      summaryMessage: result.summary_message,
    };
  },
});
