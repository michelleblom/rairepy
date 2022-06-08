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


import numpy as np
import statistics
import math

def bp_estimate(winner, loser, total):
    p = (winner+loser)/total
    q = (winner-loser)/(winner+loser)

    margin = p * (q*q)

    return math.ceil(1.0/margin)


def cp_estimate(winner, loser, total):
    margin = (winner-loser)/total

    return math.ceil(1.0/margin)



def estimator(contest, assertion, params, polling=False):
    tally_winner = assertion.votes_for_winner
    tally_loser = assertion.votes_for_loser
        
    rlimit = params["risk_limit"]

    if polling:
        # Use closed form formula from BRAVO, assume no errors
        pl = tally_loser/contest.tot_ballots
        pw = tally_winner/contest.tot_ballots
        if(pl + pw == 0):
            return contest.tot_ballots+1

        swl = 0 if pw == 0 else pw / (pl + pw);

        log2swl = math.log(2*swl);
        logrlimit = math.log(1.0/rlimit)

        return math.ceil((logrlimit+0.5*log2swl)/
            (pw*log2swl+pl*math.log(2-2*swl)));

    else:
        gamma = params["gamma"]
        lamda = params["lambda"]

        # Use closed form formula for MACRO, assume no errors
        margin = (tally_winner - tally_loser)/contest.tot_ballots

        if margin == 0:
            return contest.tot_ballots + 1

        od2g = 1.0/(2 * gamma);
        row = -math.log(rlimit)/(od2g+lamda*math.log(1-od2g));
        return math.ceil(row/margin);
   
