'''
Lower bound algorithms for parallel machine scheduling problem
Created in Feb 14th. 2019 by JuneTech
'''
import operator
from typing import Dict

import apprx_mip as am
from problem import JobData, Problem


def floor_crude(job_dict, prob: Problem, disp_flag=False):
    '''
    Crude schedule when release date is floored - maybe infeasible
    '''
    crude_schedule = am.solve_assignment_mip(job_dict, prob,
                                             ul_flag='l', offset=0,
                                             disp_flag=disp_flag)
    floor_obj = 0

    for time_job_dict in crude_schedule.values():
        for time in time_job_dict.keys():
            floor_obj += time

    return floor_obj

def no_eligibility(job_dict: Dict[int, JobData], prob: Problem, disp_flag=False):
    '''
    Exact heuristic algorithm for case when no eligibility
    (Assigning ERD job to EST machine)
    '''
    job_sorted = []
    for job in job_dict.values():
        job_sorted.append((job.idx, job.rj))
    job_sorted = sorted(job_sorted, key=operator.itemgetter(1))

    mc_job_schedule = {i:{} for i in range(1, prob.m+1)}
    mc_timer = {i: 0 for i in range(1, prob.m+1)}

    no_el_obj = 0
    for job_idx, releasedate in job_sorted:
        if disp_flag:
            print(job_idx, releasedate)
        mc_id = min(mc_timer, key=mc_timer.get)
        mc_timer[mc_id] = prob.p + max(mc_timer[mc_id],
                                       job_dict[job_idx].rj)
        mc_job_schedule[mc_id][mc_timer[mc_id]] = job_idx
        no_el_obj += mc_timer[mc_id]

    return no_el_obj
