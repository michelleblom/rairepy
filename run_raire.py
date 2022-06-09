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
from sample_estimator import estimator, bp_estimate, cp_estimate

import numpy as np

import sys
import argparse
import math


parser = argparse.ArgumentParser()
parser.add_argument('-i', dest='input', required=True)
parser.add_argument('-bp', dest='bp', action='store_true')
parser.add_argument('-e', dest='evaluate', action='store_true')

parser.add_argument('-agap', dest='agap', type=float, default=0)

# Used for estimating sample size for assertions if desired.
parser.add_argument('-r', dest='risklimit', type=float, default=0.05)


args = parser.parse_args()


params = {"risk_limit" : args.risklimit, "lambda" : 0, "gamma" : 1.1}
                    
contests, cvrs = load_contests_from_raire(args.input)

est_fn = bp_estimate if args.bp else cp_estimate

for contest in contests:
    audit = compute_raire_assertions(contest, cvrs, contest.winner, 
        est_fn, False, agap=args.agap)

    asrtns = []
    for assertion in audit:
        asrtns.append(assertion)

    sorted_asrtns = sorted(asrtns)

    print(f"Contest {contest.name}")
    max_est = 0
    if asrtns == []:
        print("No audit possible")
    else:
        for asrt in sorted_asrtns:
            est = None
            if args.evaluate:
                est = estimator(contest, asrt, params, args.bp)
            elif args.bp:  
                est = bp_estimate(asrt.votes_for_winner, asrt.votes_for_loser,\
                    contest.tot_ballots)
            else:
                est = cp_estimate(asrt.votes_for_winner, asrt.votes_for_loser,\
                    contest.tot_ballots)

            max_est = max(max_est, est)

            est_p = 100*(est/contest.tot_ballots)

            print("{} : {}, {:.2f}%".format(asrt.to_str(), est, est_p))

    if max_est != 0:
        max_est_p = 100*(max_est/contest.tot_ballots)
        print(f"Expected sample size required: {max_est}, {max_est_p:.2f}%")
