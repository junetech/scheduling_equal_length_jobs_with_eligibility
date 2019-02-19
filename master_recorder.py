'''
Re-writing of solver for identical parallel machine
with release dates, equal processing times and eligibility constraints
Created in Feb 2nd. 2019 by JuneTech
'''
import csv
import datetime
import os
import timeit

from tqdm import tqdm

import greedy as grs
import imr
import lower_bound as lb
import reader
import optimal_mip as opt
from tct_parallel_mc import ParameterLists, Problem, Result

RUN_OPTION_FILENAME = "run_option_small.json"

def set_result_filename(basename):
    now = datetime.datetime.now()
    nowDatetime = now.strftime('%Y%m%d-%H%M%S')
    result_filename = nowDatetime + '_' + basename

    return result_filename

def write_header(filename, header_list):
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', lineterminator='\n')
        writer.writerow(header_list)

def row_maker(prob: Problem, data_location):
    '''
    returns list of one successful run of the solvers
    '''
    row_timer = timeit.default_timer()
    job_dict = reader.jobinfo_feeder(prob, data_location)
    a_result = Result()

    a_result.set_time("Grd")
    a_result.set_UB("Grd", grs.greedy_solver(job_dict, prob))
    a_result.set_time("Grd")

    a_result.set_time("IMR")
    a_result.set_UB("IMR", imr.imr_solver(job_dict, prob))
    a_result.set_time("IMR")

    tqdm.write("Algorithm GIMR finished")

    a_result.set_LB("Z_L", lb.floor_crude(job_dict, prob))
    a_result.set_LB("no_el", lb.no_eligibility(job_dict, prob))
    a_result.update_most_UB_LB()

    if a_result.ratio["GIMR-LB"] < 1:
        print("Lower bound is greater")
        print("than upper bound -")
        print("something serious is wrong")
    elif a_result.ratio["GIMR-LB"] == 1:
        a_result.set_opt(a_result.UB["GIMR"])
        a_result.opt_time = '-'
        tqdm.write("Skipping optimal MIP")
    else:
        tqdm.write("Starting optimal MIP")
        a_result.set_time("opt")
        a_result.set_opt(opt.solve_optimal_mip(job_dict, prob))
        a_result.set_time("opt")
        tqdm.write("Optimal MIP finished")
    
    a_result.update_UB_ratio()

    return prob.info_list() + a_result.return_result_figures_list(), timeit.default_timer() - row_timer

def main():
    start_timer = timeit.default_timer()

    ## read run option file
    run_option = reader.json_return_dict(RUN_OPTION_FILENAME)

    ## read Slack key info from JSON
    if run_option["do_slack"]:
        try:
            from slackclient import SlackClient
            import sendslack
            slack_json_filename = run_option["slack_json_filename"]
            sc, slack_data = sendslack.return_slackclient(slack_json_filename)
        except:
            run_option["do_slack"] = False

    ## read parameter data filename info
    param_filename_data_filename = run_option["param_json_filename"]
    param_filename_data = reader.json_return_dict(param_filename_data_filename)

    ## data folder info
    if os.name == "nt":
        param_filename_data["data_location"] = param_filename_data["win_data_location"]
    elif os.name == "posix":
        param_filename_data["data_location"] = param_filename_data["linux_data_location"]

    ## create parameter data instance
    param_data = ParameterLists(param_filename_data["number_of_machines"],
                                param_filename_data["mn_ratios"],
                                param_filename_data["processing_times"],
                                param_filename_data["drs"],
                                param_filename_data["dMs"],
                                param_filename_data["number_of_copy"])
    param_data.add_from_runoption(run_option)

    tqdm.write(param_data.total_ins_string())

    ## result filename set
    result_filename = set_result_filename(param_filename_data["result_filename"])

    ## write header first for result file
    header_list = run_option["header_info"] + run_option["header_UB"] + run_option["header_LB"] + \
                  run_option["header_opt"] + run_option["header_ratio"] + run_option["header_comp"]
    write_header(result_filename, header_list)

    ## send Slack message right before beginning of iterations
    if run_option["do_slack"]:
        try:
            sendslack.message(sc, slack_data, "\n**** batch solving begins! ****\n")
            setting_string = "with option file: " + RUN_OPTION_FILENAME
            sendslack.message(sc, slack_data, setting_string)
        except:
            run_option["do_slack"] = False

    ## begin iteration
    if run_option["do_slack"]:
        pbar = tqdm(param_data.option_iterator(run_option["do_slack"], sc, slack_data),
                    total=param_data.total_ins_count,
                    ascii=True)
    else:
        pbar = tqdm(param_data.option_iterator(run_option["do_slack"], 0, 0),
                    total=param_data.total_ins_count,
                    ascii=True)

    for prob in pbar:
        prob.set_ins_idx(param_data.solved_ins_count)
        with open(result_filename, 'a') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', lineterminator='\n')
            result_row, solving_time = row_maker(prob, param_filename_data["data_location"])
            writer.writerow(result_row)
            if run_option["do_slack"] and run_option["report_individual_run"]:
                message_text = "Instance "+str(prob.info_list())+" took "+str(solving_time)+" seconds"
                try:
                    sendslack.message(sc, slack_data, message_text)
                except:
                    tqdm.write("Slack error-disabling messages")
                    run_option["do_slack"] = False
        param_data.solved_ins_count += 1

    ## iteration ended; terminating
    end_timer = timeit.default_timer()
    time_string = str(datetime.timedelta(seconds=(end_timer-start_timer)))
    message_text = "\nBatch solving ended, total time: "+ time_string
    print(message_text)
    if run_option["do_slack"]:
        try:
            sendslack.message(sc, slack_data, message_text)
        except:
            print("Slack message error at the end of the run")

    return

if __name__ == '__main__':
    main()
