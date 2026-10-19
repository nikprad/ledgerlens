/**
 * Standalone CLI runner for LedgerLens Mastra Workflow.
 * Usage: npx tsx workflow/runner.ts [imagePath]
 */

import path from 'path';
import { fileURLToPath } from 'url';
import { ledgerLensWorkflow } from './index.ts';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.dirname(__dirname);

async function runPipeline() {
  const args = process.argv.slice(2);
  const defaultImage = path.join(ROOT_DIR, 'samples', 'sample_1_kiranastore.png');
  const targetImage = args[0] || defaultImage;
  const imageName = path.basename(targetImage);

  console.log('='.repeat(70));
  console.log('  LedgerLens Mastra Orchestrator');
  console.log(`  Processing Image: ${imageName}`);
  console.log('  Pipeline: extract -> validate -> store -> forecast -> summarize');
  console.log('='.repeat(70));

  try {
    const run = await ledgerLensWorkflow.createRun();
    const result = await run.start({
      inputData: {
        imagePath: targetImage,
        imageName: imageName,
      },
    });

    console.log('\n================ WORKFLOW RESULT ================');
    console.log('Result payload:', JSON.stringify(result, null, 2));
    console.log('==================================================\n');
  } catch (error) {
    console.error('Workflow execution error:', error);
    process.exit(1);
  }
}

runPipeline();
