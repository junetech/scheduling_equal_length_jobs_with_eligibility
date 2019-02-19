'''
Containts classes: Problem, Jobdata
Created on Feb 14th, 2019 by JuneTech
'''
import math
from typing import Dict, List


class Problem:
    '''
    Problem parameters to solve and results
    '''
    def __init__(self, m, n_over_m, p, dr, dM, dup):
        self.idx: int = -1 # position of this instance among all batch instances
        self.m: int = m # number of machines
        self.mn_ratio: float = n_over_m # ratio between jobs & machines
        self.p: int = p # (equal) processing time
        self.dr: float = dr # release date density
        self.dM: float = dM # eligibility density
        self.dup: int = dup # number for duplicates, starting wiht 0

        self.offset_set = set() # list of offsets for optimal MIP and IMR algorithm

        self.approx_schedule: Dict = {} # i-t-j dictionary representing schedule
        self.approx_value: int = -1 # objective value of the approx_schedule member
        self.time_obj_dict: Dict = {} # dictionary for exact time keeping of MIP
        self.solving_time: float = -1 # time it took to solve
        self.lower_bound: int = -1 # LB calculated by algorithm

    def job_num(self):
        '''
        return number of jobs
        '''
        return int(self.m * self.mn_ratio)

    def csv_filename(self):
        '''
        return filename of problem information, including file extension
        '''
        csv_filename = 'm'+str(self.m) + 'n'+str(self.job_num())
        csv_filename += 'p'+str(self.p)
        csv_filename += 'dr'+str(self.dr)
        csv_filename += 'dM'+str(self.dM)
        csv_filename += '_'+str(self.dup) + '.csv'
        return csv_filename

    def info_list(self):
        '''
        return list of problem parameters
        '''
        return [self.m,
                self.job_num(),
                self.mn_ratio,
                self.p,
                self.dr,
                self.dM,
                self.dup]

    def set_ins_idx(self, _idx):
        self.idx = _idx

    def set_solving_time(self, seconds):
        self.solving_time = seconds
    
    def set_lower_bound(self, _lower_bound):
        self.lower_bound = _lower_bound

    def set_approx_schedule(self, mc_time_job_dict):
        '''
        Save current machine_job_sequence on approx_schedule member
        '''
        self.approx_schedule = mc_time_job_dict

    def set_approx_value(self, total_completion_time):
        '''
        Save current total completion time on approx_value member
        '''
        self.approx_value = total_completion_time

    def set_schedule_endtime_to_starttime(self):
        '''
        Make approx_schedule's time epoch
        from completion time to starting time
        '''
        if len(self.approx_schedule) == 0:
            print("Approx schedule member is empty - terminating")
            raise SyntaxError
        
        machine_id_list = list(self.approx_schedule.keys())

        for mc_id in machine_id_list:
            new_timejob_dict = {}
            for t, j in self.approx_schedule[mc_id].items():
                if t - self.p < 0:
                    print("Jobs cannot start at negative time!")
                    print(" - maybe dictionary is already about starting time")
                    raise SyntaxError
                new_timejob_dict[t - self.p] = j
            self.approx_schedule[mc_id] = new_timejob_dict
    
    def update_offset_set(self, job_dict):
        for job in job_dict.values():
            self.offset_set.add(-job.rdate_margin(self.p, ul_flag="l"))

class JobData:
    '''
    Parameters of a job
    '''
    def __init__(self, rawrow, mc_no, process_time):
        self.idx = int(rawrow['job_no'])
        self.rj = int(rawrow['release_date'])
        self.mc_el = []
        for i in range(1, mc_no+1):
            if int(rawrow[str(i)]) == 1:
                self.mc_el.append(i)
            elif int(rawrow[str(i)]) == 0:
                pass
            else:
                print("Invalid value(neither 0 nor 1) for machine eligibility")
                raise ValueError
        self.cj = -1 ## completion time

    def rdate_mod(self, p, ul_flag="u", offset=0):
        if ul_flag == "l":
            return p * (math.floor((self.rj - offset) / p)) + offset
        elif ul_flag == "u":
            return p * (math.ceil((self.rj - offset) / p)) + offset

    def rdate_margin(self, p, ul_flag="u", offset=0):
        if ul_flag == "l":
            return p * (math.floor((self.rj - offset) / p)) + offset - self.rj
            # by this, return value will be negative
        elif ul_flag == "u":
            return p * (math.ceil((self.rj - offset) / p)) + offset - self.rj
            # by this, return value will be positive

    def el_degree(self):
        return len(self.mc_el)

    def show_info(self):
        return [self.idx, self.rj, self.mc_el]
    
    def is_availabie_on(self, p, mc_id, time, ul_flag="u", offset=0):
        '''
        Return True if the job is available to be produced on a certain machine,
            and time based on modified release date
        Return False otherwise
        '''
        if mc_id in self.mc_el:
            if self.rdate_mod(p, ul_flag, offset) < time:
                return True
        return False
