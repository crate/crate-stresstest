#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to launch two different crate nodes, run a spec against both nodes and
compare the results
"""

import argparse
from functools import partial
from uuid import uuid4

from cr8.run_crate import get_crate, CrateNode
from cr8.run_spec import do_run_spec
from cr8.log import Logger
from compare_measures import Diff, print_diff


def compare_results(results_v1, results_v2):
    print('')
    print('')
    print('# Results (server side duration in ms)')
    v1 = results_v1[0].version_info
    v2 = results_v2[0].version_info
    print(f"V1: {v1['number']}-{v1['hash']}")
    print(f"V2: {v2['number']}-{v2['hash']}")
    print('')

    results_v1 = {(r.statement, r.concurrency): r for r in results_v1}
    results_v2 = {(r.statement, r.concurrency): r for r in results_v2}
    for k, result_v1 in results_v1.items():
        result_v2 = results_v2[k]
        print(f'Q: {k[0]}')
        print(f'C: {k[1]}')
        print_diff(Diff(result_v1.runtime_stats, result_v2.runtime_stats))


def _run_spec(version, spec, result_hosts, env, settings):
    crate_dir = get_crate(version)
    settings.setdefault('cluster.name', str(uuid4()))
    results = []
    with Logger() as log, CrateNode(crate_dir=crate_dir, settings=settings, env=env) as n:
        n.start()
        log.result = results.append
        do_run_spec(
            spec=spec,
            benchmark_hosts=n.http_url,
            log=log,
            result_hosts=result_hosts,
            sample_mode='reservoir'
        )
    return results


def run_compare(v1,
                v2,
                spec,
                result_hosts,
                forks,
                env_v1,
                env_v2,
                settings_v1,
                settings_v2):
    run_v1 = partial(_run_spec, v1, spec, result_hosts, env_v1, settings_v1)
    run_v2 = partial(_run_spec, v2, spec, result_hosts, env_v2, settings_v2)
    for _ in range(forks):
        results_v1 = run_v1()
        results_v2 = run_v2()
        compare_results(results_v1, results_v2)


def _dict_from_kw_args(args):
    if args:
        return dict(i.split('=') for i in args)
    else:
        return {}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        '--v1',
        help='cr8 version identifier or path to tarball (tar.gz)',
        required=True
    )
    p.add_argument(
        '--v2',
        help='cr8 version identifier or path to tarball (tar.gz)',
        required=True
    )
    p.add_argument('--spec', help='path to spec file', required=True)
    p.add_argument('--result-hosts', type=str)
    p.add_argument('--forks', type=int, default=5,
                   help='Number of times the nodes are launched and the spec re-run')
    p.add_argument('--env', action='append',
                   help='Environment variable for crate nodes. E.g. --env CRATE_HEAP_SIZE=2g')
    p.add_argument('--env-v1', action='append',
                   help='Like --env but only applied to v1')
    p.add_argument('--env-v2', action='append',
                   help='Like --env but only applied to v2')
    p.add_argument('-s', '--setting', action='append',
                   help='Crate setting. E.g. -s path.data=/tmp/c1/')
    p.add_argument('--setting-v1', action='append',
                   help='Crate setting. Only applied to v1')
    p.add_argument('--setting-v2', action='append',
                   help='Crate setting. Only applied to v2')
    args = p.parse_args()
    env = _dict_from_kw_args(args.env)
    env_v1 = env.copy()
    env_v1.update(_dict_from_kw_args(args.env_v1))
    env_v2 = env.copy()
    env_v2.update(_dict_from_kw_args(args.env_v2))
    settings = _dict_from_kw_args(args.setting)
    settings_v1 = settings.copy()
    settings_v1.update(_dict_from_kw_args(args.setting_v1))
    settings_v2 = settings.copy()
    settings_v2.update(_dict_from_kw_args(args.setting_v2))
    try:
        run_compare(
            args.v1,
            args.v2,
            args.spec,
            args.result_hosts,
            forks=max(1, args.forks),
            env_v1=env_v1,
            env_v2=env_v2,
            settings_v1=settings_v1,
            settings_v2=settings_v2
        )
    except KeyboardInterrupt:
        print('Exiting..')


if __name__ == "__main__":
    main()
