"""Check the export schema, report consistency, and public-file inventory."""
from pathlib import Path
import json
import re
import tempfile

from release_data import ROOT, load, require
from summarize import write_reports

FILES = {
    '.gitignore', 'README.md', 'DATA_DICTIONARY.md', 'LICENSE', 'NOTICE', 'CITATION.cff',
    'results.csv', 'verification.json', 'requirements.txt',
    'environment/README.md', 'environment/lean-toolchain', 'environment/dependencies.json',
    'environment/evaluation.json', 'scripts/release_data.py', 'scripts/summarize.py',
    'scripts/validate.py', 'reports/summary.json', 'reports/summary.md', 'reports/by_year.csv',
    'reports/resource-distributions.png',
}


def validate(root=ROOT):
    rows = load(root)
    actual = set()
    for path in root.rglob('*'):
        relative = path.relative_to(root)
        if any(part in {'.git', '__pycache__', '.venv'} for part in relative.parts):
            continue
        require(not path.is_symlink(), 'Symlinks are not release artifacts')
        if not path.is_file():
            continue
        name = relative.as_posix()
        require(name in FILES, 'Unexpected public file ' + name)
        actual.add(name)
        if path.suffix == '.png':
            require(path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'), 'Invalid plot format')
            continue
        text = path.read_text()
        require(not re.search(r'/(?:Users|var/folders)/|github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}'
                              r'|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{24,}', text),
                'Possible private path or credential in ' + name)
        require(not re.search(r'(?m)^\s*(?:theorem|lemma|def|abbrev)\s+putnam_\d{4}_', text),
                'Possible problem-specific Lean source in ' + name)
    require(actual == FILES, 'Missing release files ' + str(sorted(FILES - actual)))
    with tempfile.TemporaryDirectory() as temporary:
        destination = Path(temporary)
        write_reports(rows, destination)
        for name in ['summary.json', 'summary.md', 'by_year.csv']:
            require((destination / name).read_bytes() == (root / 'reports' / name).read_bytes(),
                    'Stale generated report ' + name)
    print('PASS 672 typed result rows and matching verification records')
    print('PASS published tables reproduce exactly from results.csv')
    print('PASS expected public-file inventory and text checks')
    print('This validates the public metadata package. Private proof correctness is not rechecked.')


if __name__ == '__main__':
    validate()
