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

from raire_utils import NENAssertion, NEBAssertion, Contest, vote_for_cand,\
    ranking, load_contests_from_raire

from sample_estimator import cp_estimate

from raire import compute_raire_assertions

import sys
import argparse
import numpy as np


# Make sure shangrla is in your PYTHONPATH
from shangrla.NonnegMean import NonnegMean

def sample_size(margin, args, N, test, upper_bound=1, reps=2000):
    # over: (1 - o/u)/(2 - v/u)
    # where o is the overstatement, u is the upper bound on the value
    # assorter assigns to any ballot, v is the assorter margin.
    big = 1.0/(2-margin/upper_bound) # o=0
    small = 0.5/(2-margin/upper_bound) # o=0.5

    samples = [0]*reps

    r1 = args.erate1
    r2 = args.erate2

    x = big*np.ones(N)
    rate_1_i = np.arange(0, N, step=int(1/r1), dtype=int) if r1 else []
    rate_2_i = np.arange(0, N, step=int(1/r2), dtype=int) if r2 else []

    x[rate_1_i] = small
    x[rate_2_i] = 0

    return test.sample_size(x, alpha=args.rlimit, reps=reps, seed=args.seed,\
       random_order=False, t=0.5, g=0.1)


def simple_IRV_assertions(contest, cvrs, winner, runner_up):
    """
        If Alice is the apparent winner, with Bob the apparent last-
        eliminated candidate, write the following assertions:
        1 (IRV): When everyone other than Alice and Bob are eliminated, Alice
        wins. 
        2 (Alice-not-eliminated-before): For all other candidates C, Alice
        cannot be eliminated before C. (We test this by comparing Alice's first
        preferences with all mentions of C that don't follow Alice.)
        3 (Bob-not-eliminated-before): For all other candidates C, Bob cannot
        be eliminated before C.
    """
    cname = contest.name
    
    assertions = []
    failed_to_assert = []

    ballots = [b[contest.name] for _,b in cvrs.items() if contest.name in b]
    others = [c for c in contest.candidates if c != winner and c != runner_up]

    # 1. Assertion indicating that 'winner' wins when everyone except 
    # 'winner' and 'runner_up' are eliminated.
    w_tally_1, r_tally_1 = 0,0


    # 2. 'winner' NEB any candidate in others
    # 3. 'runner_up' NEB any candidate in others
    min_w_2 = 0
    min_r_3 = 0
    max_c_w_2 = {o : 0 for o in others}
    max_c_r_3 = {o : 0 for o in others}
    
    for blt in ballots:
        w_tally_1 += vote_for_cand(winner, others, blt)
        r_tally_1 += vote_for_cand(runner_up, others, blt)

        widx = ranking(winner, blt)
        ridx = ranking(runner_up, blt)

        if widx == 0:
            min_w_2 += 1

        elif ridx == 0:
            min_r_3 += 1

        else:
            for c in others:
                cidx = ranking(c, blt)

                if cidx != -1 and (widx == -1 or cidx < widx):
                    max_c_w_2[c] += 1

                if cidx != -1 and (ridx == -1 or cidx < ridx):
                    max_c_r_3[c] += 1



    if w_tally_1 > r_tally_1:
        nen = NENAssertion(cname, winner, runner_up, others)
        nen.votes_for_winner = w_tally_1
        nen.votes_for_loser = r_tally_1
        assertions.append(nen)

    else:
        failed_to_assert.append("{} NEN over {} when {} eliminated".format(\
            winner, runner_up, others))


    for c in others:
        if min_w_2 > max_c_w_2[c]:
            neb = NEBAssertion(cname, winner, c)
            neb.votes_for_winner = min_w_2
            neb.votes_for_loser = max_c_w_2[c]

            assertions.append(neb)
        else:
            failed_to_assert.append("{} NEB {}".format(winner, c))

        if min_r_3 > max_c_r_3[c]:     
            neb = NEBAssertion(cname, runner_up, c)
            neb.votes_for_winner = min_r_3
            neb.votes_for_loser = max_c_r_3[c]

            assertions.append(neb)
        else:
            failed_to_assert.append("{} NEB {}".format(runner_up, c))
            
   
    return assertions, failed_to_assert 


def sim_irv(contest, cvrs):
    standing = [c for c in contest.candidates]

    tallies = {c : 0 for c in contest.candidates}
    ballots = [b[contest.name] for _,b in cvrs.items() if contest.name in b]

    eliminated = []

    while len(standing) > 1:
        tallies = {c : 0 for c in standing}

        for blt in ballots:
            for c in standing:
                if vote_for_cand(c, eliminated, blt):
                    tallies[c] += 1

        toelim = None
        elimtally = None
        for c in standing:
            ctally = tallies[c]
            if elimtally == None or (ctally < elimtally):
                toelim = c
                elimtally = ctally
       
        eliminated.append(toelim)
        standing.remove(toelim)

    return standing[0], eliminated[-1], len(ballots)
        

if __name__ == "__main__":    

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', dest='input', required=True)
    parser.add_argument('-r', dest='rlimit', type=float, default=0.05)
    parser.add_argument('-e1', dest='erate1', type=float, default=0.002)
    parser.add_argument('-e2', dest='erate2', type=float, default=0)
    parser.add_argument('-seed', dest='seed', type=int, default=1234567)
    parser.add_argument('-reps', dest='reps', type=int, default=100)
    parser.add_argument('-agap', dest='agap', type=float, default=0)

    args = parser.parse_args()

    contests, cvrs = load_contests_from_raire(args.input)


    np.seterr(all="ignore")

    for contest in contests:
        winner, runner_up, tot_ballots = sim_irv(contest, cvrs)

        # Create test for estimating sample sizes (use default settings)
        nnm = NonnegMean(test=NonnegMean.kaplan_kolmogorov, \
            estim=NonnegMean.optimal_comparison, N=tot_ballots, t=0.5, g=0.1)

        assertions, failures = simple_IRV_assertions(contest, cvrs, winner, \
            runner_up)

        raire_audit = compute_raire_assertions(contest, cvrs, winner, 
            cp_estimate, False, agap=args.agap)

        raire_est = 0
        raire_assertions = []
        for asrtn in raire_audit:
            amean = (asrtn.votes_for_winner + 0.5*(tot_ballots - \
                asrtn.votes_for_winner - asrtn.votes_for_loser))/tot_ballots

            est = sample_size(2*amean-1,args,tot_ballots,nnm,reps=args.reps)
            raire_est = max(est, raire_est)
            raire_assertions.append((asrtn, 2*amean-1, est))

        if failures != []:
            print("{},contest {}, no simple audit,, RAIRE,{}".format(\
                args.input, contest.name, raire_est))
        else:
            max_cost = 0
            simple_assertions = []
            for asrtn in assertions:
                amean = (asrtn.votes_for_winner + 0.5*(tot_ballots - \
                    asrtn.votes_for_winner-asrtn.votes_for_loser))/tot_ballots

                est = sample_size(2*amean-1,args,tot_ballots,nnm,reps=args.reps)
                max_cost = max(est, max_cost)
                simple_assertions.append((asrtn, 2*amean-1, est))

            if max_cost < raire_est:
                print("Simple:")
                for asrtn,amargin,cost in simple_assertions:
                    print("{}, margin, {}, cost {}".format(asrtn.to_str(), \
                        amargin, cost))

                print("RAIRE:")
                for asrtn,amargin,cost in raire_assertions:
                    print("{}, margin, {}, cost {}".format(asrtn.to_str(), \
                        amargin, cost))

            print("{},contest {},simple audit,{},RAIRE,{}".format(args.input,\
                contest.name, max_cost, raire_est))
                 