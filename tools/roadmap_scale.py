"""Reproducible bounded document/graph observations, not compiler/PERF qualification."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import time
import tracemalloc
from roadmap import Limits, parse_documents, render, validate


def observe(text: str) -> dict:
    tracemalloc.start()
    started = time.perf_counter()
    parsed = parse_documents({'synthetic.md': text})
    validate(parsed, require_evidence=False)
    output = render(parsed)
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    repeated = render(parse_documents({'synthetic.md': text}))
    if repeated != output:
        raise AssertionError('bounded synthetic output was not deterministic')
    return {'input_bytes':len(text.encode()), 'nodes':len(parsed.nodes),
            'increments':len(parsed.increments), 'elapsed_seconds_traced':elapsed,
            'peak_python_traced_bytes':peak, 'output_bytes':len(output.encode()),
            'output_sha256':hashlib.sha256(output.encode()).hexdigest(), 'identical_repeats':2}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--increments',type=int,default=2000)
    parser.add_argument('--depth',type=int,default=192)
    args = parser.parse_args()
    if not 1 <= args.increments <= 10_000 or not 1 <= args.depth <= 256:
        parser.error('bounded workload: 1..10000 increments, 1..256 depth')
    chain=[]
    for index in range(1,args.increments+1):
        item=f'FND-{index:02}'
        dependency=f'FND-{index-1:02}' if index>1 else 'none'
        chain.extend([f'- [ ] {item} Synthetic document.', f'  Depends on: {dependency}.',
                      f'  - [ ] {item}.a Work.', f'  - [ ] {item}.e Close.'])
    nested=['- [ ] FND-01 Nested document.','  Depends on: none.']
    item='FND-01'
    for depth in range(1,args.depth+1):
        item+='.'+('a' if depth==1 else '1')
        nested.append('  '*depth+f'- [ ] {item} Nested work.')
    nested.append('  - [ ] FND-01.e Close.')
    print(json.dumps({'scope':'roadmap structure only; no execution or hardware credit',
                      'python':platform.python_version(),'platform':platform.platform(),
                      'validator_sha256':hashlib.sha256(Path(__file__).with_name('roadmap.py').read_bytes()).hexdigest(),
                      'limits':vars(Limits()), 'many_increments':observe('\n'.join(chain)+'\n'),
                      'nested':observe('\n'.join(nested)+'\n')},sort_keys=True,indent=2))


if __name__=='__main__':
    main()
