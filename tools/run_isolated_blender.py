"""Run development tests without reading/writing the user's Blender profile."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--blender', required=True)
    parser.add_argument('--ui', action='store_true')
    parser.add_argument('script')
    parser.add_argument('arguments', nargs='*')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='node-console-isolated-',
                                     dir='/private/tmp' if sys.platform=='darwin' else None) as directory:
        env = dict(os.environ)
        for variable, name in [('BLENDER_USER_CONFIG', 'test-config'),
                               ('BLENDER_USER_SCRIPTS', 'scripts'),
                               ('BLENDER_USER_DATAFILES', 'datafiles'), ('TMPDIR', 'temp')]:
            path = Path(directory) / name
            path.mkdir()
            env[variable] = str(path)
        command = [args.blender, '--factory-startup']
        command += ['--enable-event-simulate'] if args.ui else ['--background']
        command += ['--python-exit-code', '1', '--python', str(Path(args.script).resolve())]
        if args.arguments:
            command += ['--'] + args.arguments
        raise SystemExit(subprocess.run(command, env=env).returncode)


if __name__ == '__main__':
    main()
