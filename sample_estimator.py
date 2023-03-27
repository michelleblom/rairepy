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


import numpy as np
import statistics
import math

# Make sure shangrla is in your PYTHONPATH
from shangrla.NonnegMean import NonnegMean


def sample_size(margin, args, N, test, upper_bound=1, polling=False):
    # over: (1 - o/u)/(2 - v/u)
    # where o is the overstatement, u is the upper bound on the value
    # assorter assigns to any ballot, v is the assorter margin.
    big = 1 if polling else 1.0/(2-margin/upper_bound) # o=0
    small = 0 if polling else 0.5/(2-margin/upper_bound) # o=0.5

    r1 = args.erate1
    r2 = args.erate2

    x = big*np.ones(N)
    rate_1_i = np.arange(0, N, step=int(1/r1), dtype=int) if r1 else []
    rate_2_i = np.arange(0, N, step=int(1/r2), dtype=int) if r2 else []

    x[rate_1_i] = small
    x[rate_2_i] = 0

    return test.sample_size(x, alpha=args.rlimit, reps=args.reps, \
        seed=args.seed, random_order=False, t=0.5, g=0.1)


def bp_estimate(winner, loser, other, total):
    p = (winner+loser)/total
    q = (winner-loser)/(winner+loser)

    margin = p * (q*q)

    return 1.0/margin


def cp_estimate(winner, loser, other, total):
    amargin = 2*((winner+0.5*other)/total) - 1

    return 1.0/amargin


def get_default_test(tot_ballots, polling=False):
    return NonnegMean(test=NonnegMean.kaplan_kolmogorov, \
        estim=NonnegMean.optimal_comparison, N=tot_ballots, t=0.5, g=0.1) if \
        polling else NonnegMean(test=NonnegMean.kaplan_kolmogorov, \
        estim=NonnegMean.shrink_trunc, N=tot_ballots, t=0.5, g=0.1)


