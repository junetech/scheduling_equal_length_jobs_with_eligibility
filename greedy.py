'''
Solves the scheduling problem by Algorithm Greedy
Created in Feb 13th. 2019 by JuneTech
'''
import math

from tct_parallel_mc import Problem


def sort_job_idx(job_dict: dict):
    '''
    Return list index of jobs sorted by
    1) ERD rule
    2) LFJ rule
    '''
    copy_key_list = list(job_dict.keys())
    sort_key_list = []
    
    while(len(copy_key_list) != 0):
        ## Make list of key of jobs with ERD
        min_value = math.inf
        min_job_key_list = []
        for key in copy_key_list:
            value = job_dict[key]
            if value.rj == min_value:
                min_job_key_list.append(key)
            elif value.rj < min_value:
                min_value = value.rj
                min_job_key_list = [key]
        
        ## add key of jobs with LFJ rule
        ## into return key list
        if len(min_job_key_list) == 1:
            sort_key_list.append(min_job_key_list[0])
            copy_key_list.remove(min_job_key_list[0])
        else:
            job_cardinality_dict = {}
            for job_id in min_job_key_list:
                job_cardinality_dict[job_id] = job_dict[job_id].el_degree()
            while(len(job_cardinality_dict) != 0):
                min_eligible_cardinality_key = min(job_cardinality_dict,
                                                   key=job_cardinality_dict.get)
                sort_key_list.append(min_eligible_cardinality_key)
                del job_cardinality_dict[min_eligible_cardinality_key]
                copy_key_list.remove(min_eligible_cardinality_key)
        
    return sort_key_list

def choose_target_mc(mc_dict: dict, jobdata):
    '''
    Choose the machine with the earliest available starting time
    among the eligible machines of the chosen job.
    If tie occurs, choose the machine such that
    the number of unscheduled jobs eligible to that machine is minimum.
    '''
    ## Find the machine with earliest starting time & add them to the dictionary
    min_value = math.inf
    eligible_est_mc_dict = {}
    for mc_id in jobdata.mc_el:
        if mc_dict[mc_id]["available_starting_time"] == min_value:
            eligible_est_mc_dict[mc_id] = mc_dict[mc_id]["eligible_unscheduled_count"]
        elif mc_dict[mc_id]["available_starting_time"] < min_value:
            min_value = mc_dict[mc_id]["available_starting_time"]
            eligible_est_mc_dict = {mc_id: mc_dict[mc_id]["eligible_unscheduled_count"]}
    
    ## Choose the machine with smallest eligible_unscheduled_count
    target_mc_key = min(eligible_est_mc_dict,
                        key=eligible_est_mc_dict.get)
    return target_mc_key

def greedy_solver(job_dict, prob: Problem, disp_flag=False):
    '''
    solve scheduling problem by Algorithm Greedy
    and return the objective value(= total completion time)
    '''
    mc_dict = {i:{"available_starting_time": 0, "eligible_unscheduled_count": 0}
               for i in range(1, prob.m+1)}

    for job in job_dict.values():
        for mc_id in job.mc_el:
            mc_dict[mc_id]["eligible_unscheduled_count"] += 1

    job_key_list = sort_job_idx(job_dict)

    mc_time_job_dict = {i:{} for i in range(1, prob.m+1)}
    total_completion_time = 0

    for job_key in job_key_list:
        target_mc_key = choose_target_mc(mc_dict, job_dict[job_key])

        ## Assign the job to the time to the machine
        starting_time = max(job_dict[job_key].rj,
                            mc_dict[target_mc_key]["available_starting_time"])
        completion_time = starting_time + prob.p
        mc_time_job_dict[target_mc_key][completion_time] = job_key

        total_completion_time += completion_time

        mc_dict[target_mc_key]["available_starting_time"] = completion_time
        for mc_id in job_dict[job_key].mc_el:
            mc_dict[mc_id]["eligible_unscheduled_count"] -= 1

    if disp_flag:
        from result_display import print_schedule_info
        print_schedule_info(mc_time_job_dict, prob.p, is_tqdm=True)

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
        greedy_solver(info, prob, disp_flag=True)

if __name__ == '__main__':
    main()
