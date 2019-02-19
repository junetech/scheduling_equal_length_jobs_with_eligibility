'''
Visualizes result of scheduling,
format of result being {i: {t : j}}, t representing time of job completion
Created in Jun. 24. 2018 by JuneTech
'''

from tqdm import tqdm

def print_schedule_info(machine_job_sequence, p, is_tqdm=False):
    '''
    Visualizes result of scheduling,
    format of result being {i: {t : j}}
    '''

    # Calculating makespan of the schedule
    Cmax = 0
    for time_job_dict in machine_job_sequence.values():
        for time in time_job_dict.keys():
            Cmax = max(Cmax, time)
    cmax_string = "Cmax: " + str(Cmax)
    if is_tqdm:
        tqdm.write(cmax_string)
    else:
        print(cmax_string)

    # assigning characters for each machines
    machine_job_characters = {}
    for mc_id, time_job_dict in machine_job_sequence.items():
        machine_job_characters[mc_id] = {t:"  " for t in range(1, Cmax+1)}
        for time, job in time_job_dict.items():
            for dt in range(1, p):
                if machine_job_characters[mc_id][time-dt] != "  ":
                    print("Overlap error!")
                    raise SyntaxError
                machine_job_characters[mc_id][time-dt] = "##"
            machine_job_characters[mc_id][time] = str(job).zfill(2)

    # Writing headers
    header_string = " t |"
    bar_string = "---+"
    for mc_id in machine_job_sequence.keys():
        header_string += str(mc_id).zfill(2)
        header_string += '|'
        bar_string += "--+"
    if is_tqdm:
        tqdm.write(header_string)
        tqdm.write(bar_string)
    else:
        print(header_string)
        print(bar_string)

    # Filling time rows
    for t in range(1, Cmax+1):
        time_string = str(t).zfill(3) + '|'
        for time_str_dict in machine_job_characters.values():
            time_string += time_str_dict[t]
            time_string += '|'
        if is_tqdm:
            tqdm.write(time_string)
        else:
            print(time_string)

def check_end_schedule_feasibility(mc_time_job_dict, job_dict, p):
    '''
    return False if machine eligibility or release date constraint is not kept
    return True otherwise
    '''
    return_bool = True
    for i, time_job_dict in mc_time_job_dict.items():
        for t, j in time_job_dict.items():
            if i not in job_dict[j].mc_el:
                print("Machine", i,
                      "\tdoes not belong to job", job_dict[j].idx,
                      "\twith eligibility:", job_dict[j].mc_el)
                return_bool = False
            if job_dict[j].rj + p > t:
                print("Job", job_dict[j].idx,
                      "\tbegins at", t - p,
                      "\tand have release date:", job_dict[j].rj)
                return_bool = False
    
    if return_bool:
        return return_bool
    else:
        raise SyntaxError

def main():
    print("Result display starts")
    machine_job_sequence = {}
    machine_job_sequence[1] = {4 : 1, 7 : 2, 10 : 3}
    machine_job_sequence[2] = {3 : 4, 6 : 5, 11 : 6}
    machine_job_sequence[3] = {5 : 7, 9 : 8}
    print_schedule_info(machine_job_sequence, 3)

if __name__ == '__main__':
    main()
