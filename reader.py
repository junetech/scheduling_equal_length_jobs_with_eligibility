'''
File reading functions
Created in Feb 10th. 2019 by JuneTech
'''

import csv
import math
from tct_parallel_mc import Problem, JobData


def json_return_dict(filename):
    '''
    reads JSON file,
    returns dictionary
    '''
    import json
    try:
        with open(filename) as json_file:
            json_dict = json.load(json_file)
    except FileNotFoundError:
        print("No JSON file named:", filename)
        raise FileNotFoundError
    except ValueError:
        print("Problem with JSON file named:", filename)
        raise ValueError
    except:
        print("Unknown problem reading JSON file named:", filename)
    
    return json_dict

def jobinfo_feeder(run_param: Problem, data_location):
    '''
    gets basic information of job data, returns list of JobData instances
    '''
    filename = data_location + run_param.csv_filename()

    job_ins_dict = {}
    with open(filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', lineterminator='\n')
        for row in reader:
            job = JobData(row, run_param.m, run_param.p)
            job_ins_dict[job.idx] = job

    return job_ins_dict

def main():
    RUN_OPTION_FILENAME = "run_option_small.json"

    run_option = json_return_dict(RUN_OPTION_FILENAME)
    param_filename_data_filename = run_option["param_json_filename"]
    param_filename_data = json_return_dict(param_filename_data_filename)

    import os

    if os.name == "nt":
        param_filename_data["data_location"] = param_filename_data["win_data_location"]
    elif os.name == "posix":
        param_filename_data["data_location"] = param_filename_data["linux_data_location"]

    from tct_parallel_mc import ParameterLists

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
        info = jobinfo_feeder(prob, param_filename_data["data_location"])
        pbar.set_description("Processsing %s" % str(prob.info_list()))
        for item in info.values():
            tqdm.write(str(item.show_info()))

if __name__ == '__main__':
    main()
