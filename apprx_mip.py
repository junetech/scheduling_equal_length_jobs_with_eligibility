'''
Re-writing of approximation MIP solver using Gurobi
Created in Feb 14th. 2019 by JuneTech
'''
from typing import Dict

from gurobipy import *

from problem import JobData, Problem


def solve_assignment_mip(job_dict: Dict[int, JobData], prob: Problem, ul_flag, offset=0, disp_flag=False):
    n = prob.job_num()
    rj_set = set()
    cj_set = set()
    rj_max = -1

    if ul_flag == 'u':
        for job in job_dict.values():
            rj_set.add(job.rdate_mod(prob.p, offset=offset))
        for rj in rj_set:
            for a in range(1, n+1):
                cj_set.add(rj + a * prob.p)
    elif ul_flag == 'l':
        for job in job_dict.values():
            rj_max = max(rj_max, job.rdate_mod(prob.p, ul_flag=ul_flag))
    
    if ul_flag == 'u':
        comp_time = sorted(list(cj_set))
    elif ul_flag == 'l':
        slot_count = n + int(rj_max/prob.p) + 1
        comp_time = [(i+1)*prob.p for i in range(slot_count)]
    job_idx = list(job_dict.keys())
    mc_id = {i+1 for i in range(prob.m)}

    model = Model("MIP with %c flag and %d offset" % (ul_flag, offset))
    model.setParam("OutputFlag", disp_flag)
    x = model.addVars(mc_id, comp_time, job_idx, lb=0, ub=1,
                      name="i-t-j schedule")

    max_timeslot = max(comp_time)
    epsilon = 1/max_timeslot

    ## perturbated cost in assignment problem
    c = {}
    for i in mc_id:
        empty_timedict = {}
        for t in comp_time:
            empty_jobdict = {}
            for j in job_idx:
                empty_jobdict[j] = t
            empty_timedict[t] = empty_jobdict
        c[i] = empty_timedict
    
    big_M = max_timeslot * n + (prob.p * (n+1)*n/2)
    for i in mc_id:
        for t in comp_time:
            for j in job_idx:
                multiplier = 1 + epsilon*(job_dict[j].rdate_margin(prob.p, offset=offset)
                                          - (job_dict[j].el_degree()/prob.m)) ##TODO: 이거 빼고도 한번 돌려보기
                c[i][t][j] = multiplier * c[i][t][j]
                ## jobs can not be assigned to uneligible machines
                if i not in job_dict[j].mc_el:
                    c[i][t][j] = big_M
                ## jobs can not be assigned to timeslot before release time
                if job_dict[j].rdate_mod(prob.p, offset=offset) + prob.p > t:
                    c[i][t][j] = big_M

    model.setObjective(quicksum(quicksum(quicksum(x[i, t, j]*c[i][t][j]
                                                  for i in mc_id)
                                         for t in comp_time)
                                for j in job_idx),
                       GRB.MINIMIZE)

    ## Each job must be scheduled to one machine and one completion time
    model.addConstrs((quicksum(quicksum(x[i,t,j] for i in mc_id)
                               for t in comp_time) == 1)
                     for j in job_idx)

    ## Each timeslot can have at maximum one job
    for i in mc_id:
        for t in comp_time:
            model.addConstr(quicksum(x[i,t,j] for j in job_idx) <= 1)

    model.update()
    model.optimize()

    mc_time_job_dict = {i:{} for i in range(1, prob.m+1)}
    solution = model.getAttr('x', x)
    for i in mc_id:
        for t in comp_time:
            for j in job_idx:
                if round(solution[i,t,j]) == 1:
                    mc_time_job_dict[i][t] = j

    return mc_time_job_dict
