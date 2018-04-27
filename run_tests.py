import os
import argparse
import glob
from cdat import cdat_climo


parser = argparse.ArgumentParser(description='Climo and time series parser')
parser.add_argument('-i', '--input_dir', help="Input directory with model files.", required=True)
parser.add_argument('-o', '--output_dir', help="Output directory to store results.", required=True)
parser.add_argument('-s', '--start_yrs', type=int, help="Years to start with.", required=True)
parser.add_argument('-e', '--end_yrs', type=int, help="Years to end with.", required=True)
parser.add_argument('-c', '--case', help="Case of the model data.", required=True)
parser.add_argument('-v', '--vars', nargs='+', default=[], help="A list of variables to use. If not defined, all variables will be used.")
parser.add_argument('--cleanup', action='store_const', const=True, help="Delete the generated climo files when done.")
parser.add_argument('--input_files', nargs='*', help="An optional list of input files to use.")

args = parser.parse_args()

# For any dir, account for if the user uses `~``
args.input_dir = os.path.abspath(os.path.expanduser(args.input_dir))
args.output_dir = os.path.abspath(os.path.expanduser(args.output_dir))

# Format start and end years correctly
#args.start_yrs = '{:04d}'.format(args.start_yrs)
#args.end_yrs = '{:04d}'.format(args.end_yrs)

try:
    print('Running climos with CDAT')
    cdat_climo.run(args)
finally:
    if args.cleanup:
        print('Removing generated climos files.')