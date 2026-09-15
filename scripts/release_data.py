"""Load the public numeric export and check its narrow data schema."""
from collections import Counter
from decimal import Decimal
from pathlib import Path
import csv
import json
import re

ROOT = Path(__file__).resolve().parent.parent
TOKEN_FIELDS = ['input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens']
COUNT_FIELDS = ['review_rounds', 'compilations', 'submissions', 'actor_turns',
                'continuation_requests', 'elapsed_seconds']
COUNT_FIELDS += [role + '_' + field for role in ['actor', 'reviewer'] for field in TOKEN_FIELDS]
COUNT_FIELDS += ['input_tokens', 'output_tokens']
COST_FIELDS = ['actor_cost_usd', 'reviewer_cost_usd', 'total_cost_usd']
COLUMNS = ['problem_id', 'year', 'outcome', 'actor_model', 'reviewer_model', 'effort']
COLUMNS += COUNT_FIELDS[:6] + COST_FIELDS + COUNT_FIELDS[6:]
TASK_KEYS = {'problem_id', 'outcome', 'proof_sha256', 'verifier_status',
             'reviewer_verdict', 'retained_artifact_hash_matches'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(root=ROOT):
    with (root / 'results.csv').open(newline='') as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == COLUMNS, 'Unexpected results.csv columns')
        rows = list(reader)
    ids = set()
    for row in rows:
        require(set(row) == set(COLUMNS) and None not in row.values(), 'Malformed CSV row')
        name = row['problem_id']
        match = re.fullmatch(r'putnam_(\d{4})_[ab][1-6]', name)
        require(match is not None and name not in ids, 'Invalid or duplicate problem ID')
        ids.add(name)
        require(row['year'] == match[1], 'Year does not match the problem ID')
        require(row['actor_model'] == 'Opus 5' and row['effort'] == 'xhigh', 'Unexpected configuration')
        accepted = row['outcome'] == 'reviewed_accepted'
        require(accepted or (name == 'putnam_1974_b1' and row['outcome'] == 'statement_false'),
                'Unexpected outcome')
        require(row['reviewer_model'] == ('Opus 5' if accepted else ''), 'Unexpected reviewer model')
        for field in COUNT_FIELDS:
            value = row[field]
            if not accepted:
                require(value == '', 'Resource field outside the accepted-task scope')
                row[field] = None
            else:
                require(re.fullmatch(r'\d+', value) is not None, 'Invalid count in ' + field)
                row[field] = int(value)
        for field in COST_FIELDS:
            value = row[field]
            if not value:
                require(not accepted and field != 'actor_cost_usd', 'Missing cost')
                row[field] = None
            else:
                require(re.fullmatch(r'\d+\.\d{9}', value) is not None, 'Invalid cost')
                row[field] = Decimal(value)
        if accepted:
            require(row['review_rounds'] >= 1 and row['submissions'] >= 1, 'Missing accepted-task checks')
            require(row['total_cost_usd'] == row['actor_cost_usd'] + row['reviewer_cost_usd'], 'Cost sum mismatch')
            expected_input = sum(row[role + '_' + field] for role in ['actor', 'reviewer'] for field in TOKEN_FIELDS[:3])
            require(row['input_tokens'] == expected_input, 'Input token sum mismatch')
            require(row['output_tokens'] == row['actor_output_tokens'] + row['reviewer_output_tokens'], 'Output token sum mismatch')
    require(len(rows) == 672, 'Expected the complete 672-task snapshot')
    require(Counter(row['outcome'] for row in rows) == {'reviewed_accepted': 671, 'statement_false': 1},
            'Unexpected snapshot counts')
    evidence = json.loads((root / 'verification.json').read_text())
    require(set(evidence) == {'schema_version', 'snapshot_date', 'evidence_source', 'benchmark_commit',
                              'proof_text_included', 'checks_at_export', 'tasks'}, 'Unexpected verification fields')
    require(evidence['schema_version'] == 1 and evidence['snapshot_date'] == '2026-09-15', 'Unexpected snapshot')
    require(evidence['evidence_source'] == 'author_retained_evaluation_records', 'Unexpected evidence source')
    require(evidence['proof_text_included'] is False, 'Proof-text flag must be false')
    require(evidence['checks_at_export'] == dict(accepted_proof_hash_matches=671, final_reviewer_approvals=671,
                                                recorded_verifier_successes=671, frozen_benchmark_matches=672),
            'Unexpected export checks')
    require(len(evidence['tasks']) == len(rows), 'Verification count mismatch')
    records = {row['problem_id']: row for row in rows}
    seen = set()
    for task in evidence['tasks']:
        require(set(task) == TASK_KEYS, 'Unexpected verification task fields')
        name = task['problem_id']
        require(name in records and name not in seen, 'Invalid verification problem ID')
        seen.add(name)
        require(task['outcome'] == records[name]['outcome'], 'Outcome mismatch')
        if task['outcome'] == 'reviewed_accepted':
            require(isinstance(task['proof_sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', task['proof_sha256']), 'Invalid artifact hash')
            require(task['verifier_status'] == 'solved' and task['reviewer_verdict'] == 'APPROVE', 'Invalid recorded verdict')
            require(task['retained_artifact_hash_matches'] is True, 'Missing export hash check')
        else:
            require(task['proof_sha256'] is None and task['reviewer_verdict'] is None and
                    task['retained_artifact_hash_matches'] is None and task['verifier_status'] == 'not_accepted',
                    'Non-accepted task must not claim a passing proof')
    config = json.loads((root / 'environment/evaluation.json').read_text())
    require(set(config) == {'schema_version', 'system', 'benchmark', 'benchmark_repository', 'benchmark_commit',
                            'variant', 'problem_count', 'model', 'model_identifier', 'effort', 'snapshot_date',
                            'result_source', 'resource_scope', 'summary_population', 'runtime_unit', 'currency', 'token_unit'},
            'Unexpected environment fields')
    require(config['benchmark_commit'] == evidence['benchmark_commit'] == 'b3e08943b1728842194fe2df693f02c763da4294', 'Benchmark pin mismatch')
    expected_config = dict(schema_version=1, system='Forall-Lean-Agent', benchmark='PutnamBench',
                           benchmark_repository='https://github.com/trishullab/PutnamBench',
                           benchmark_commit=evidence['benchmark_commit'], variant='wsolution', problem_count=672,
                           model='Opus 5', model_identifier='claude-opus-5', effort='xhigh', snapshot_date='2026-09-15',
                           result_source='author_retained_evaluation_records', resource_scope='retained_final_task_records',
                           summary_population='reviewed_accepted', runtime_unit='seconds', currency='USD', token_unit='tokens')
    require(config == expected_config, 'Unexpected evaluation configuration')
    deps = json.loads((root / 'environment/dependencies.json').read_text())
    require(set(deps) == {'schema_version', 'packages'} and deps['schema_version'] == 1, 'Unexpected dependency fields')
    for package in deps['packages']:
        require(set(package) == {'name', 'url', 'rev'}, 'Unexpected package fields')
        require(re.fullmatch(r'[A-Za-z0-9_-]+', package['name']), 'Invalid package name')
        require(re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?', package['url']), 'Unexpected dependency URL')
        require(re.fullmatch(r'[0-9a-f]{40}', package['rev']), 'Invalid dependency pin')
    return rows
