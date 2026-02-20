"""
Single entry point to run both search_retriever and details_retriever in parallel.

Usage:
    python run.py [--login-wait SECONDS]

Options:
    --login-wait    Seconds to wait after submitting LinkedIn credentials before
                    capturing the session. Increase if your connection is slow or
                    if LinkedIn shows extra verification steps. Default: 15.

The two scripts share linkedin_jobs.db and run indefinitely until interrupted (Ctrl+C).
"""

import subprocess
import sys
import os
import argparse

parser = argparse.ArgumentParser(description='Run LinkedIn Job Scraper')
parser.add_argument('--login-wait', type=int, default=15,
                    help='Seconds to wait for login to complete per account (default: 15)')
args = parser.parse_args()

env = os.environ.copy()
env['LOGIN_WAIT_SECONDS'] = str(args.login_wait)

print(f'Starting scraper with {args.login_wait}s login wait...')
print('Press Ctrl+C to stop both processes.\n')

procs = [
    subprocess.Popen([sys.executable, 'search_retriever.py'], env=env),
    subprocess.Popen([sys.executable, 'details_retriever.py'], env=env),
]

try:
    for p in procs:
        p.wait()
except KeyboardInterrupt:
    print('\nStopping...')
    for p in procs:
        p.terminate()
    for p in procs:
        p.wait()
    print('Done.')
