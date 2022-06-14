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
  

def kapkol_er_cp(contest, assertion, params):
    '''
        This code is adapted from an earlier version of kaplan
        kolmogorov sample size estimation from Philip Stark's SHANGRLA at 
        the repo link: SHANGRLA/Code/assertion_audit_utils.py.

        This code only works for comparison audits. 
    '''
    seed = params['seed']
    rlimit = params['risk_limit']

    error_rate = params['error_rate']
    t = params['t'] if 't' in params else 1/2
    g = params['g'] if 'g' in params else 0.1
    quantile = params['quantile'] if 'quantile' in params else 0.5
    reps = params['reps'] if 'reps' in params else 20
    upper_bound = 1
    
    tally_winner = assertion.votes_for_winner
    tally_loser = assertion.votes_for_loser

    N = contest.tot_ballots

    amean = (tally_winner + 0.5*(N - (tally_winner+tally_loser)))/N

    margin = 2*amean - 1

    prng = np.random.RandomState(seed) 

    clean = 1.0/(2 - margin/upper_bound)
    one_vote_over = (1-0.5)/(2-margin/upper_bound) 

    samples = [0]*reps

    for i in range(reps):
        pop = clean*np.ones(N)
        inx = (prng.random(size=N) <= error_rate)  # randomly allocate errors
        pop[inx] = one_vote_over

        sample_total = 0
        mart = (pop[0]+g)/(t+g) if t > 0 else  1
        p = min(1.0/mart,1.0)
        j = 1

        while p > rlimit and j < N:
            mart *= (pop[j]+g)*(1-j/N)/(t+g - (1/N)*sample_total)
    
            if mart < 0:
                break
            else:
                sample_total += pop[j] + g

            
            p = min(1.0/mart,1.0) if mart > 1.0 else 1.0

            j += 1;

        if p <= rlimit:
            samples[i] = j
        else:
            return np.inf 

    return np.quantile(samples, quantile)

