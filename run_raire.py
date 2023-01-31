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
from sample_estimator import estimator, bp_estimate, cp_estimate, kapkol_er_cp

import numpy as np

import sys
import argparse
import math


parser = argparse.ArgumentParser()
parser.add_argument('-i', dest='input', required=True)
parser.add_argument('-bp', dest='bp', action='store_true')
parser.add_argument('-e', dest='evaluate', action='store_true')
parser.add_argument('-v', dest='verbose', action='store_true')

parser.add_argument('-agap', dest='agap', type=float, default=0)

# Used for estimating sample size for assertions if desired.
parser.add_argument('-r', dest='risklimit', type=float, default=0.05)

# Used when estimating sample size given non zero error rate for comparison
# audits. No sample size estimator in sample_estimator.py for ballot polling
# with non-zero error rate.
parser.add_argument('-erate', dest='error_rate', type=float, default=0.002)
parser.add_argument('-seed', dest='seed', type=int, default=1234567)
parser.add_argument('-reps', dest='reps', type=int, default=2000)

args = parser.parse_args()


params = {"risk_limit" : args.risklimit, "lambda" : 0, "gamma" : 1.1, \
    "error_rate" : args.error_rate, "seed" : args.seed, "reps" : args.reps}
                    
contests, cvrs = load_contests_from_raire(args.input)

est_fn = bp_estimate if args.bp else cp_estimate

for contest in contests:
    # In this restricted version, only NEB assertions are created. Instead of 
    # passing raire the set of CVRs, we instead pass a map between candidate 
    # pairs (eg. A,B) and the first preference count for A alongside the number
    # of ballots on which B appears above A or B appears and A does not, 
    # eg. counts[A][B] = (tallyA, tallyB).
    counts = { }
    for c in contest.candidates:
        c_counts = {}

        for d in contest.candidates:
            if c == d: continue

            tally_c = 0
            tally_d = 0
            for _,r in cvrs.items():
                if not contest.name in r:
                    continue

                c_idx = ranking(c, r[contest.name])
                if c_idx == 0:
                    tally_c += 1
                else:
                    d_idx = ranking(d, r[contest.name])
       
                    tally_d += (1 if d_idx != -1 and (c_idx == -1 or \
                        (c_idx != -1 and d_idx < c_idx)) else 0)

            c_counts[d] = (tally_c, tally_d)

        counts[c] = c_counts
 

    audit = compute_raire_assertions(contest, counts, contest.winner, 
        est_fn, args.verbose, agap=args.agap)

    asrtns = []
    for assertion in audit:
        asrtns.append(assertion)

    sorted_asrtns = sorted(asrtns)

    max_est = 0
    if asrtns == []:
        print(f"File {args.input}, Contest {contest.name}, No audit possible")
    else:
        for asrt in sorted_asrtns:
            est = None
            if args.evaluate:
                if not args.bp and args.error_rate > 0:
                    est = kapkol_er_cp(contest, asrt, params)
                else:
                    est = estimator(contest, asrt, params, args.bp)

            elif args.bp:  
                est = bp_estimate(asrt.votes_for_winner, asrt.votes_for_loser,\
                    contest.tot_ballots)
            else:
                est = cp_estimate(asrt.votes_for_winner, asrt.votes_for_loser,\
                    contest.tot_ballots)

            max_est = max(max_est, est)

            est_p = 100*(est/contest.tot_ballots)
            if args.verbose:
                print("{}, est {},{}%".format(asrt.to_str(), est, est_p))

    if max_est != 0:
        max_est = min(max_est, contest.tot_ballots)
        max_est_p = 100*(max_est/contest.tot_ballots)
        print(f"File {args.input}, Contest {contest.name}, asn {max_est}, {max_est_p:.2f}%")
