# Copyright (C) 2022 Michelle Blom
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from raire_utils import *
from raire import compute_raire_assertions
from sample_estimator import *

import numpy as np

import sys
import argparse
import math


parser = argparse.ArgumentParser()
parser.add_argument('-i', dest='input', required=True)
parser.add_argument('-v', dest='verbose', action='store_true')

parser.add_argument('-agap', dest='agap', type=float, default=0)

# Used for estimating sample size for assertions if desired.
parser.add_argument('-r', dest='rlimit', type=float, default=0.10)

# Used when estimating sample size given non zero error rate for comparison
# audits. No sample size estimator in sample_estimator.py for ballot polling
# with non-zero error rate.
parser.add_argument('-e1', dest='erate1', type=float, default=0.002)
parser.add_argument('-e2', dest='erate2', type=float, default=0)
parser.add_argument('-seed', dest='seed', type=int, default=1234567)
parser.add_argument('-reps', dest='reps', type=int, default=100)

args = parser.parse_args()


contests, cvrs = load_contests_from_raire(args.input)

est_fn = cp_estimate

np.seterr(all="ignore")

for contest in contests:
    audit = compute_raire_assertions(contest, cvrs, contest.winner, 
        est_fn, args.verbose, agap=args.agap)

    N = contest.tot_ballots

    max_est = 0

    if audit == []:
        print(f"File {args.input}, Contest {contest.name}, No audit possible")
    else:

        for asrt in audit:
            est = sample_size(asrt.margin, None, None, None, args, N)

            est = min(est, N) # Cut off at a full recount

            max_est = max(max_est, est)

            est_p = 100*(est/N)
            if args.verbose:
                print("{}, est {},{}%".format(asrt.to_str(), est, est_p))

    if max_est != 0:
        max_est = min(max_est, N)
        max_est_p = 100*(max_est/N)
        print(f"File {args.input}, Contest {contest.name}, asn {max_est}, {max_est_p:.2f}%")
