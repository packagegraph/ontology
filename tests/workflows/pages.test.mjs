import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { Evaluator, Lexer, Parser, data } from '@actions/expressions';
import { parse } from 'yaml';

const workflow = parse(readFileSync(
  new URL('../../.github/workflows/deploy-ontology.yml', import.meta.url), 'utf8',
));
const jobs = Object.entries(workflow.jobs);
const uses = (job, action) => job.steps?.some(step => step.uses?.startsWith(`${action}@`));
const [buildId, build] = jobs.find(([, job]) => uses(job, 'actions/upload-pages-artifact'));
const [, deploy] = jobs.find(([, job]) => uses(job, 'actions/deploy-pages'));

// Evaluate the actual workflow expressions, not a JavaScript translation of its guard.
function evaluate(expression, context) {
  const source = String(expression).trim().replace(/^\$\{\{\s*|\s*\}\}$/g, '');
  const parsed = new Parser(new Lexer(source).lex().tokens, Object.keys(context), []).parse();
  return new Evaluator(parsed, JSON.parse(JSON.stringify(context), data.reviver)).evaluate();
}

function interpolate(template, context) {
  return template.replace(/\$\{\{(.*?)\}\}/g, (_, expr) => evaluate(expr, context).coerceString());
}

test('PR build has no write token, OIDC token, or Pages configuration', () => {
  assert.notEqual(build, deploy, 'publishing must not execute in the build job');
  assert.deepEqual(workflow.permissions, { contents: 'read' });
  assert.deepEqual(build.permissions ?? workflow.permissions, { contents: 'read' });
  assert.equal(uses(build, 'actions/configure-pages'), false);
  for (const [, job] of jobs) {
    if (job !== deploy) {
      assert.deepEqual(job.permissions ?? workflow.permissions, { contents: 'read' });
    }
  }
});

test('deployment consumes a successful build without checking out repository code', () => {
  assert.ok([deploy.needs].flat().includes(buildId), 'deployment must depend on the artifact producer');
  assert.equal(deploy.permissions.pages, 'write');
  assert.equal(deploy.permissions['id-token'], 'write');
  assert.equal(uses(deploy, 'actions/checkout'), false);
  assert.equal(deploy.steps.some(step => step.run !== undefined), false);
});

// Include PR-target's main ref as defense against accidentally broadening the trigger.
for (const [event, ref, result, expected] of [
  ['pull_request', 'refs/pull/14/merge', 'success', false],
  ['pull_request_target', 'refs/heads/main', 'success', false],
  ['push', 'refs/heads/feature', 'success', false],
  ['push', 'refs/tags/main', 'success', false],
  ['workflow_dispatch', 'refs/heads/feature', 'success', false],
  ['push', 'refs/heads/main', 'failure', false],
  ['push', 'refs/heads/main', 'cancelled', false],
  ['push', 'refs/heads/main', 'skipped', false],
  ['push', 'refs/heads/main', 'success', true],
  ['workflow_dispatch', 'refs/heads/main', 'success', true],
]) {
  test(`deployment guard: ${event}, ${ref}, build ${result} => ${expected}`, () => {
    assert.equal(evaluate(deploy.if ?? 'true', {
      github: { event_name: event, ref },
      needs: { [buildId]: { result } },
    }).value, expected);
  });
}

test('Pages environment receives the actual deployment URL', () => {
  assert.equal(deploy.environment?.name, 'github-pages');
  const step = deploy.steps.find(step => step.uses?.startsWith('actions/deploy-pages@'));
  assert.ok(step.id, 'deployment action needs an output-producing id');
  assert.equal(evaluate(deploy.environment.url, {
    steps: { [step.id]: { outputs: { page_url: 'https://example.test/ontology/' } } },
  }).value, 'https://example.test/ontology/');
});

test('PR builds cannot cancel or displace production deployments', () => {
  assert.equal(deploy.concurrency['cancel-in-progress'], false);
  const groups = ['refs/pull/14/merge', 'refs/pull/15/merge', 'refs/heads/main'].map(ref => {
    const context = { github: { workflow: workflow.name, ref } };
    const buildGroup = interpolate(build.concurrency.group, context);
    const deployGroup = interpolate(deploy.concurrency.group, context);
    assert.notEqual(buildGroup.toLowerCase(), deployGroup.toLowerCase());
    return buildGroup.toLowerCase();
  });
  assert.equal(new Set(groups).size, 3, 'independent refs need independent build queues');
});
