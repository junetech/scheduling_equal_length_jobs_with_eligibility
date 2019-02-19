'''
Containts classes: ParameterLists, Result
Created on Feb 2nd, 2019 by JuneTech
'''
import math

from problem import JobData, Problem


class ParameterLists:
    '''
    Program environment option parameters
    '''
    def __init__(self, machine_number_list, mn_ratio_list, processing_time_list,
                 dr_list, dM_list, _number_of_copy):
        self.number_of_machines = machine_number_list
        self.mn_ratios = mn_ratio_list
        self.processing_times = processing_time_list
        self.drs = dr_list
        self.dMs = dM_list
        self.number_of_copy = _number_of_copy
        self.total_ins_count = -1   ## Total instances in this run
        self.optimal_timelimit = -1     ## Time limit for optimal MIP model

        self.set_total_ins_count()
        self.solved_ins_count = 0

    def set_total_ins_count(self):
        self.total_ins_count = len(self.number_of_machines) *\
                               len(self.mn_ratios) *\
                               len(self.processing_times) *\
                               len(self.drs) *\
                               len(self.dMs) *\
                               self.number_of_copy
    
    def total_ins_string(self):
        return_string = "Total " + str(self.total_ins_count) + " instances in this parameter dataset"
        return return_string

    def add_from_runoption(self, runoption):
        self.optimal_timelimit = runoption["optimal_timelimit"]

    def option_iterator(self, message_flag, sc, slack_data):
        from tqdm import tqdm
        if message_flag:
            import sendslack
        for m in self.number_of_machines:
            machine_text = str(m)+" machines, "
            for n_over_m in self.mn_ratios:
                job_text = str(n_over_m*m)+" jobs, "
                for p in self.processing_times:
                    p_text = "p="+str(p)+' '
                    if message_flag:
                        message_text = "Start processing " + machine_text + job_text + p_text
                        tqdm.write(message_text)
                        try:
                            sendslack.message(sc, slack_data, message_text)
                        except:
                            print("Slack error-disabling messages")
                            message_flag = False
                    for dr in self.drs:
                        for dM in self.dMs:
                            for dup in range(self.number_of_copy):
                                yield Problem(m, n_over_m, p, dr, dM, dup)

class Result:
    '''
    Figures for a result
    '''
    def __init__(self):
        # Approximation objective value & time
        self.UB = {"Grd": -1, "IMR": -1, "GIMR": -1}
        self.UB_time = {"Grd": -1, "IMR": -1, "GIMR": -1}

        # Lower bound objective value
        self.LB = {"Z_L": -1, "no_el": -1, "LB": -1}

        # Optimal value & time
        self.opt = -1
        self.opt_time = -1.0
        
        # Ratios
        self.ratio = {"Grd": -1.0, "IMR": -1.0, "GIMR": -1.0, "GIMR-LB": -1.0}

        # Approximation objective comparisons
        self.both_same = 0
        self.IMR_better = 0
        self.Grd_better = 0

    def set_time(self, key):
        '''
        When called for the first time for the key, start timer
        When called for the second time, record time
        '''
        import timeit
        if key == "opt":
            if self.opt_time == -1:
                self.opt_time = timeit.default_timer()
            else:
                self.opt_time = round(timeit.default_timer() - self.opt_time, 4)
        else:
            if self.UB_time[key] == -1:
                self.UB_time[key] = timeit.default_timer()
            else:
                self.UB_time[key] = round(timeit.default_timer() - self.UB_time[key], 4)
    
    def set_UB(self, key, obj):
        '''
        Record objective value of upper bounds
        '''
        self.UB[key] = obj
    
    def set_LB(self, key, obj):
        '''
        Record objective value of lower bounds
        '''
        self.LB[key] = obj

    def set_opt(self, obj):
        '''
        Record objective value of optimal solution
        '''
        self.opt = obj

    def update_most_UB_LB(self):
        '''
        Calcualte results for GIMR & LB
        '''
        if self.UB["Grd"] < self.UB["IMR"]:
            self.UB["GIMR"] = self.UB["Grd"]
            self.Grd_better = 1
        elif self.UB["Grd"] > self.UB["IMR"]:
            self.UB["GIMR"] = self.UB["IMR"]
            self.IMR_better = 1
        else:
            self.UB["GIMR"] = self.UB["Grd"]
            self.both_same = 1

        self.UB_time["GIMR"] = self.UB_time["Grd"] + self.UB_time["IMR"]

        self.LB["LB"] = min(self.LB["Z_L"], self.LB["no_el"])

        self.ratio["GIMR-LB"] = self.UB["GIMR"] / self.LB["LB"]

    def update_UB_ratio(self):
        '''
        Calcualte UB/opt ratios
        '''       
        self.ratio["GIMR"] = self.UB["GIMR"] / self.opt
        self.ratio["Grd"] = self.UB["Grd"] / self.opt
        self.ratio["IMR"] = self.UB["IMR"] / self.opt

    def return_result_figures_list(self):
        '''
        Return list of values
        - objective values
        - times spent
        - ratios
        - comparisons
        '''
        UB_list = []
        LB_list = []
        opt_list = [self.opt, self.opt_time]
        ratio_list = []
        comp_list = [self.both_same, self.IMR_better, self.Grd_better]

        UB_key_list = ["Grd", "IMR", "GIMR"]
        for key in UB_key_list:
            UB_list.append(self.UB[key])
            UB_list.append(self.UB_time[key])
            ratio_list.append(self.ratio[key])
        
        ratio_list.append(self.ratio["GIMR-LB"])

        LB_key_list = ["Z_L", "no_el", "LB"]
        for key in LB_key_list:
            LB_list.append(self.LB[key])
        
        return UB_list + LB_list + opt_list + ratio_list + comp_list
