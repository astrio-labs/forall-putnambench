"""Reproduce numeric reports and optional plots from the public CSV."""
from collections import Counter
from decimal import Decimal
from pathlib import Path
import argparse
import csv
import json
import math
import statistics

from release_data import ROOT, load


def distribution(values):
    values = sorted(Decimal(str(value)) for value in values)
    def number(value):
        return float(round(value, 6))
    return dict(n=len(values), minimum=number(values[0]), median=number(statistics.median(values)),
                mean=number(sum(values) / len(values)), p90=number(values[math.ceil(.9 * len(values)) - 1]),
                maximum=number(values[-1]), total=number(sum(values)))


def summarize(rows):
    accepted = [row for row in rows if row['outcome'] == 'reviewed_accepted']
    metrics = ['compilations', 'submissions', 'review_rounds', 'actor_turns', 'continuation_requests',
               'elapsed_seconds', 'actor_cost_usd', 'reviewer_cost_usd', 'total_cost_usd', 'input_tokens', 'output_tokens']
    return dict(schema_version=1, snapshot_date='2026-09-15', total_problems=len(rows),
                accepted_problems=len(accepted), statement_false_problems=1,
                accepted_fraction_all_tasks=len(accepted) / len(rows),
                accepted_fraction_excluding_statement_false=1.0,
                resource_population='reviewed_accepted', resource_population_size=len(accepted),
                review_round_counts=dict(sorted(Counter(str(row['review_rounds']) for row in accepted).items())),
                tasks_with_continuations=sum(row['continuation_requests'] > 0 for row in accepted),
                resources={metric: distribution([row[metric] for row in accepted]) for metric in metrics})


def write_reports(rows, destination):
    destination.mkdir(parents=True, exist_ok=True)
    summary = summarize(rows)
    (destination / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    years = sorted({int(row['year']) for row in rows})
    with (destination / 'by_year.csv').open('w', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['year', 'evaluated', 'accepted', 'statement_false'])
        for year in years:
            group = [row for row in rows if int(row['year']) == year]
            counts = Counter(row['outcome'] for row in group)
            writer.writerow([year, len(group), counts['reviewed_accepted'], counts['statement_false']])
    lines = ['# Evaluation summary', '',
             'Author-reported outcomes from the September 15, 2026 metadata snapshot.', '',
             '| Outcome | Problems |', '| --- | --- |',
             '| Accepted by local verification and fresh review | 671 |',
             '| Recorded false statement | 1 |', '| Evaluated | 672 |', '',
             'The resource statistics below cover the 671 accepted task records.', '',
             '| Metric | Median | Mean | 90th percentile | Maximum |', '| --- | --- | --- | --- | --- |']
    for field, title, divisor in [
        ('compilations', 'Compilations', 1), ('elapsed_seconds', 'Elapsed time in minutes', 60),
        ('actor_cost_usd', 'Actor cost in USD', 1), ('reviewer_cost_usd', 'Reviewer cost in USD', 1),
        ('total_cost_usd', 'Combined cost in USD', 1), ('input_tokens', 'Input tokens including cache traffic', 1),
        ('output_tokens', 'Output tokens', 1)]:
        stats = summary['resources'][field]
        cells = [f'{stats[key] / divisor:,.2f}' for key in ['median', 'mean', 'p90', 'maximum']]
        lines.append('| ' + ' | '.join([title] + cells) + ' |')
    total = summary['resources']['total_cost_usd']['total']
    lines += ['', f'Total recorded cost for the accepted task records is ${total:,.2f}.', '',
              'These subtotals exclude archived or superseded attempts and the false-statement task. '
              'They are not a measurement of total project expenditure.', '',
              'See [the data dictionary](../DATA_DICTIONARY.md) for field definitions and missing values.', '']
    (destination / 'summary.md').write_text('\n'.join(lines))
    return summary


def plot(rows, destination):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    accepted = [row for row in rows if row['outcome'] == 'reviewed_accepted']
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.edgecolor': '#9BB5D5', 'axes.labelcolor': '#183B65',
                         'xtick.color': '#46617F', 'ytick.color': '#46617F'})
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5), layout='constrained')
    specs = [('compilations', 'Compiler invocations', list(range(0, 61, 5)), 1),
             ('actor_cost_usd', 'Actor cost in USD', list(range(0, 41, 2)), 1),
             ('elapsed_seconds', 'Elapsed time in minutes', list(range(0, 241, 20)), 60)]
    for ax, (field, label, bins, divisor) in zip(axes, specs):
        values = [float(row[field]) / divisor for row in accepted]
        ax.hist(values, bins=bins, color='#367BD0', edgecolor='white', linewidth=1)
        median = statistics.median(values)
        ax.axvline(median, color='#173E71', linewidth=1.8, linestyle='--', label=f'Median {median:.2f}'.rstrip('0').rstrip('.'))
        ax.set_xlabel(label)
        ax.set_ylabel('Problems')
        ax.set_axisbelow(True)
        ax.grid(axis='y', color='#E3EDF9', linewidth=.8)
        ax.legend(frameon=False, fontsize=10)
    fig.suptitle('Resource use across 671 accepted PutnamBench problems\nForall-Lean-Agent with Opus 5 at xhigh effort',
                 fontsize=14, color='#183B65')
    fig.savefig(destination / 'resource-distributions.png', dpi=160, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plots', action='store_true', help='Also regenerate the Matplotlib figure')
    parser.add_argument('--output', type=Path, default=ROOT / 'reports')
    args = parser.parse_args()
    data = load()
    summary = write_reports(data, args.output)
    if args.plots:
        plot(data, args.output)
    print(f'Wrote reports for {summary["accepted_problems"]} accepted tasks out of {summary["total_problems"]}')
