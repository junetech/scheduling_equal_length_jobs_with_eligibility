'''
Solves the scheduling problem by Algorithm IMR
Created in Feb 13th. 2019 by JuneTech
'''
import math

import apprx_mip as am
import result_display as rd
from tct_parallel_mc import Problem


def imr_solver(job_dict, prob: Problem, disp_flag=False):
    '''
    solve scheduling problem by Algorithm IMR
    and return the objective value(= total completion time)
    '''
    prob.update_offset_set(job_dict)
    best_offset_obj = math.inf

    ## calculate offset-iterated ceiling first
    for offset in prob.offset_set:
        crude_schedule = am.solve_assignment_mip(job_dict, prob,
                                 ul_flag='u', offset=offset,
                                 disp_flag=disp_flag)
        offset_obj_value, apprx_schedule = modify_crude(crude_schedule,
                                                        job_dict,
                                                        prob,
                                                        offset,
                                                        disp_flag)
        if best_offset_obj > offset_obj_value:
            best_offset_obj = offset_obj_value
        if (prob.approx_value == -1) or (prob.approx_value > offset_obj_value):
            prob.approx_value = offset_obj_value
            prob.approx_schedule = apprx_schedule

    ## calculate flooring second
    crude_schedule = am.solve_assignment_mip(job_dict, prob,
                             ul_flag='l', offset=0,
                             disp_flag=disp_flag)
    floor_fixed_obj, apprx_schedule = modify_crude(crude_schedule,
                                                   job_dict,
                                                   prob,
                                                   0,
                                                   disp_flag)
    if prob.approx_value > floor_fixed_obj:
        prob.approx_value = floor_fixed_obj
        prob.approx_schedule = apprx_schedule

    return min(best_offset_obj, floor_fixed_obj)

def modify_crude(crude_dict, job_dict, prob: Problem, offset, disp_flag):
    '''
    Make crude_dict efficient
    and return total completion time with modified schedule
    '''
    mc_time_job_dict = {}
    for i in range(1, prob.m+1): ## machine iteration
        joblist = []
        for key, value in crude_dict[i].items():
            joblist.append((key, value))
        mc_time_job_dict[i] = sorted(joblist, key=lambda jobs: jobs[0])

    new_sequence = {i:{} for i in range(1, i+1)}
    for i, joblist in mc_time_job_dict.items():
        time_cursor = 0
        for item in joblist:
            one_completion_time = prob.p + max(time_cursor, 
                                               job_dict[item[1]].rj)
            job_dict[item[1]].cj = one_completion_time
            time_cursor = one_completion_time
            new_sequence[i][one_completion_time] = item[1]

    rd.check_end_schedule_feasibility(new_sequence, job_dict, prob.p)
    if disp_flag: rd.print_schedule_info(new_sequence, prob.p)

    total_completion_time = 0
    for job in job_dict.values():
        total_completion_time += job.cj

    return total_completion_time, new_sequence

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
        imr_solver(info, prob, disp_flag=True)

if __name__ == '__main__':
    main()
