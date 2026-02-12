import fs from 'node:fs/promises';
import path from 'node:path';

const HISTORY_PATH = path.resolve('data/analysis-history.json');

const model = process.env.OPENAI_MODEL || 'gpt-4.1';
const apiKey = process.env.OPENAI_API_KEY;
const context = process.env.ANALYSIS_CONTEXT || 'Aucun contexte fourni via workflow_dispatch.';
const tag = process.env.ANALYSIS_TAG || `Run-${new Date().toISOString().slice(0, 10)}`;

if (!apiKey) {
  throw new Error('OPENAI_API_KEY is missing. Configure it in repository secrets.');
}

function safeJsonParse(content) {
  try {
    return JSON.parse(content);
  } catch {
    const fenced = content.match(/```json\s*([\s\S]*?)\s*```/i) || content.match(/```\s*([\s\S]*?)\s*```/i);
    if (!fenced) throw new Error(`OpenAI did not return valid JSON: ${content}`);
    return JSON.parse(fenced[1]);
  }
}

function fallbackDifferences(currentAnalysis, previousAnalysis) {
  if (!previousAnalysis) return ['Première version IA générée dans le repository.'];
  if (currentAnalysis === previousAnalysis) return ['Aucune évolution majeure détectée dans ce run.'];

  const prevLines = new Set(previousAnalysis.split('\n').map((line) => line.trim()).filter(Boolean));
  const currentLines = currentAnalysis.split('\n').map((line) => line.trim()).filter(Boolean);
  const newLines = currentLines.filter((line) => !prevLines.has(line));

  if (!newLines.length) return ['Évolution textuelle détectée sans changement de points clés.'];
  return newLines.slice(0, 5).map((line) => `Nouveau point: ${line.slice(0, 180)}`);
}

async function loadHistory() {
  try {
    const content = await fs.readFile(HISTORY_PATH, 'utf8');
    const parsed = JSON.parse(content);
    if (!Array.isArray(parsed.versions)) throw new Error('Invalid history schema: versions must be an array');
    return parsed;
  } catch {
    return { updatedAt: new Date().toISOString(), versions: [] };
  }
}

async function saveHistory(history) {
  await fs.writeFile(HISTORY_PATH, `${JSON.stringify(history, null, 2)}\n`, 'utf8');
}

async function generateAnalysis(previousAnalysis) {
  const systemPrompt = [
    'Tu es un analyste macro + crypto institutionnel expert Bitcoin.',
    'Tu produis une mise à jour hebdomadaire en français, claire, actionnable et structurée.',
    'Retourne uniquement un JSON strict: {"headline":"...","analysis":"...","differences":["...","..."]}.',
    'analysis doit contenir: Macro, On-chain, Institutionnels/ETF, Régulation, Scénarios 3-6 mois.',
    'differences doit lister les changements majeurs versus la version précédente.'
  ].join(' ');

  const userPrompt = [
    `Tag demandé: ${tag}`,
    `Contexte utilisateur: ${context}`,
    'Analyse précédente:',
    previousAnalysis || 'Aucune analyse précédente.'
  ].join('\n\n');

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model,
      temperature: 0.2,
      max_tokens: 1800,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ]
    })
  });

  if (!response.ok) {
    const errBody = await response.text();
    throw new Error(`OpenAI error ${response.status}: ${errBody}`);
  }

  const data = await response.json();
  const content = data?.choices?.[0]?.message?.content?.trim();
  if (!content) {
    throw new Error('OpenAI returned empty content.');
  }

  const parsed = safeJsonParse(content);
  const analysis = typeof parsed.analysis === 'string' && parsed.analysis.trim()
    ? parsed.analysis.trim()
    : content;

  const differences = Array.isArray(parsed.differences) && parsed.differences.length
    ? parsed.differences
    : fallbackDifferences(analysis, previousAnalysis);

  return {
    headline: parsed.headline || 'Mise à jour BTC',
    analysis,
    differences
  };
}

async function main() {
  const history = await loadHistory();
  const previous = history.versions[history.versions.length - 1];

  const generated = await generateAnalysis(previous?.analysis || '');

  const nextVersion = {
    version: history.versions.length + 1,
    tag,
    model,
    createdAt: new Date().toISOString(),
    headline: generated.headline,
    analysis: generated.analysis,
    differences: generated.differences
  };

  history.versions.push(nextVersion);
  history.updatedAt = new Date().toISOString();
  history.latestHeadline = nextVersion.headline;

  await saveHistory(history);
  console.log(`Added version ${nextVersion.version} (${nextVersion.headline}).`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
