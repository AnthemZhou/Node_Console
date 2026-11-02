"""Export reviewed native captures as portable, non-personal regression data."""
import argparse
import json
from pathlib import Path


def identity(entry):
    return 'ASSET:' + entry['english'] if entry['kind'] == 'ASSET' else 'ENTRY:' + entry['id']


def export(root, destination):
    report = json.loads((root / 'report.json').read_text())
    audit = json.loads((root / 'analysis.json').read_text())
    assert not report['errors'] and all(case['resolved'] for case in audit['cases'])
    assert len(report['samples']) == len(audit['cases'])
    cases = []
    for sample, result in zip(report['samples'], audit['cases']):
        assert sample['index'] == result['index']
        catalog = {e['id']: e for e in report['catalogs'][sample['context']]}
        portable = {key: identity(e) for key, e in catalog.items()}
        # Bundled factory assets have unique names in each tested tree. Refuse
        # ambiguous identities rather than merging assets from different libraries.
        assert len(set(portable.values())) == len(portable)
        case = {key: sample[key] for key in ('tree', 'engine', 'shader', 'language', 'query', 'group')}
        case.update(native=[portable[key] for key in result['native']],
                    baseline_first=result['first'], baseline_exact=result['visible_exact'],
                    extension_has_results=bool(sample['plugin']))
        cases.append(case)
    output = dict(schema=1, blender=report['version'], build=report['build'],
                  environment='macOS arm64, isolated factory profile, bundled assets, pinned groups, no favorites/history',
                  source='Actual NODE_MT_add search screenshots, reviewed OCR; reproduction documented in PERFORMANCE.md',
                  summary=audit['summary'], cases=cases)
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Exported {len(cases)} native cases to {destination}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    export(args.directory, args.output)
