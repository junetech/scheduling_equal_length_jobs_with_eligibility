'''
Re-writing of optimal MIP solver using Gurobi
Created in Feb 14th. 2019 by JuneTech
'''
from typing import Dict

from gurobipy import *

from problem import JobData, Problem


def solve_optimal_mip(job_dict: Dict[int, JobData], prob: Problem, disp_flag=False):
    n = prob.job_num()
    rj_list = []
    cj_set = set()
    cj_max = -1

    for job in job_dict.values():
        rj_list.append(job.rj)
    rj_list = sorted(rj_list)
    for rj in rj_list:
        cj_max = max(cj_max + prob.p, rj + prob.p)
    for rj in rj_list:
        for a in range(1, n+1):
            cj = rj + a * prob.p
            if cj > cj_max: break
            cj_set.add(rj + a * prob.p)

    comp_time = sorted(list(cj_set))

    ## Gamma set definition
    gamma_set = {}
    for r in comp_time:
        gamma_set[r] = []
        for h in comp_time:
            if h > r: break
            if h > r - prob.p:
                gamma_set[r].append(h)

    # print(gamma_set)

    job_idx = list(job_dict.keys())
    mc_id = {i+1 for i in range(prob.m)}

    model = Model("optimal MIP")
    model.setParam("OutputFlag", disp_flag)
    x = model.addVars(mc_id, comp_time, job_idx, vtype=GRB.BINARY,
                      name="i-t-j schedule")

    model.setObjective(quicksum(quicksum(quicksum(t * x[i, t, j]
                                                  for i in mc_id)
                                         for t in comp_time)
                                for j in job_idx),
                       GRB.MINIMIZE)

    for i in mc_id:
        for t in comp_time:
            for j in job_idx:
                ## jobs can not be assigned to uneligible machines
                if i not in job_dict[j].mc_el:
                    model.addConstr(x[i,t,j] == 0)
                ## jobs can not be assigned to timeslot before release time
                if job_dict[j].rj + prob.p > t:
                    model.addConstr(x[i,t,j] == 0)

    ## Each job must be scheduled to one machine and one completion time
    model.addConstrs((quicksum(quicksum(x[i,t,j] for i in mc_id)
                               for t in comp_time) == 1)
                     for j in job_idx)

    ## No two jobs can be processed simultaneously
    ## on the same machine
    for j in job_idx:
        no_j_set = []
        for l in job_idx:
            if l != j:
                no_j_set.append(l)

        for i in mc_id:
            for t in comp_time:
                ihl_sum = LinExpr()
                for h in gamma_set[t]:
                    for l in no_j_set:
                        ihl_sum.add(x[i,h,l])
                model.addConstr(x[i,t,j] + ihl_sum <= 1)

    model.update()
    model.optimize()

    total_completion_time = 0
    solution = model.getAttr('x', x)
    for i in mc_id:
        for t in comp_time:
            for j in job_idx:
                if round(solution[i,t,j]) == 1:
                    total_completion_time += t

    return total_completion_time

def main():
    from tct_parallel_mc import ParameterLists
    from reader import jobinfo_feeder, json_return_dict
    RUN_OPTION_FILENAME = "run_option_small.json"

    run_option = json_return_dict(RUN_OPTION_FILENAME)
    param_filename_data_filename = run_option["param_json_filename"]
    param_filename_data = json_return_dict(param_filename_data_filename)

    import os

    if os.name == "nt":
        param_filename_data["data_location"] = param_filename_data["win_data_location"]
    elif os.name == "posix":
        param_filename_data["data_location"] = param_filename_data["linux_data_location"]

    param_data = ParameterLists(param_filename_data["number_of_machines"],
                                param_filename_data["mn_ratios"],
                                param_filename_data["processing_times"],
                                param_filename_data["drs"],
                                param_filename_data["dMs"],
                                param_filename_data["number_of_copy"])
    param_data.add_from_runoption(run_option)

    from tqdm import tqdm
    pbar = tqdm(param_data.option_iterator(False, 0, 0),
                total=param_data.total_ins_count,
                ascii=True)
    for prob in pbar:
        pbar.set_description("Processsing %s" % str(prob.info_list()))
        info = jobinfo_feeder(prob, param_filename_data["data_location"])
        obj_value = solve_optimal_mip(info, prob, disp_flag=False)
        tqdm_string = "Optimal objective value: " + str(obj_value)
        tqdm.write(tqdm_string)

if __name__ == '__main__':
    main()
