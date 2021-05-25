import json
import os
import pandas as pd

import pkg_resources

import numpy as np
from eppy.modeleditor import IDF

import matplotlib.pyplot as plt


class Setpoint_Schedule:
    def __init__(self,
                 schedule_params,
                 fig_dir = '../figures/',
                 idd_file=None,
                 **kwargs):
        """
        Constructs necessary attributes for a setpoint schedule object

        Parameters
        :param schedule_params: dict -> see .json for input

        You can add eplus_param as an additional argument eplus_param
        """

        # get arguments
        self.fig_dir = fig_dir

        # create fig directory if not exists
        if not os.path.exists(self.fig_dir):
            os.makedirs(self.fig_dir)

        # set eplus_config if specified.
        if "eplus_param" in kwargs:
            self.eplus_param = kwargs["eplus_param"]
        else:
            self.set_eplus_config()

        # set  IDD
        if idd_file is None:
            self.idd_file = pkg_resources.resource_filename('tempset', 'data/eplus/Energy+.idd')
        else:
            self.idd_file = idd_file
        # self.idd_file = self.eplus_param["idd_file"]
        IDF.setiddname(self.idd_file)

        # import IDF and extract all the scedules
        idf_1 = IDF(idfname=pkg_resources.resource_filename('tempset', 'data/idf/gas.idf'))
        # idf_1 = IDF(idfname=self.eplus_param["idf_file"])
        AllSchedComapcts = idf_1.idfobjects["Schedule:Compact"]

        # get params from json'
        self.get_schparams_from_json(schedule_params=schedule_params)
        # change SETP schedule'
        self.mod_schedule = self.change_SETP(
            AllSchedCompacts=AllSchedComapcts, schedule_name=self.schedule_name
        )
        # write new schedule to file'
        self.write_to_idf(
            edited_schedule=self.mod_schedule,
            idf_file=pkg_resources.resource_filename('tempset', 'data/idf/gas.idf'),
            new_file=self.eplus_param["mod_file"],
        )

    def get_schparams_from_json(self, schedule_params):
        """
        Method to extract data from dict (schedule_params)

        :param schedule_params: dict -> contains params needed to generate setback schedules
        """

        # get schedule name and other schedule info
        # days in week for which the schedule needs to be changed
        self.days_list = schedule_params["days_in_week"]
        # name of schedule, as specified in .json
        self.schedule_name = schedule_params["schedule_name"]
        self.schedule_name_edited = (
            "EDITED_" + self.schedule_name
        )  # new name, as it will appear in IDF
        self.schedule_type = schedule_params["schedule_type"]

        # assigning probability related parameters
        # threshold probability corresponding to the max setback
        self.p_threshSetback = schedule_params["p_threshSetback"]
        # probability threshold for rampup rate
        self.p_threshRamp = schedule_params["p_threshRamp"]
        # obtained from data_utils: fraction of CBECS office with setback
        self.setback_p = schedule_params["setback_p"]

        # Assert schedule setpoint is valid.
        assert self.schedule_type == "CLGSETP" or self.schedule_type == "HTGSETP"

        # assigning time related parameters
        self.timeRes = schedule_params["timeRes"]
        self.hourSteps = int(60 / self.timeRes)

        # Parameters for pre-heating/pre-cooling
        self.setback_tol = schedule_params["max_setbackhour"]
        self.occupied_times = schedule_params["occupied_times"]

        # parameters for ramp-up rate
        # maximum hours over which ramping can take place
        self.max_rampHour = schedule_params["max_ramphour"]
        # time resolution at which ramping can occur. recommended = 15 mins
        self.rampRes = schedule_params["rampRes"]
        # minimum rampup rate, as defined in json
        self.rampup_min = schedule_params["rampRate_min"]
        self.roundOff_temp = 0.5  # rounding of temperatures to the nearest 1 C

        # get plotting preferences
        self.plot_base_schedule = schedule_params["plot_base_schedule"]
        self.plot_mod_schedule = schedule_params["plot_mod_schedule"]

        # specify cooling setpoint during occcupied and unoccupied times'
        if self.schedule_type == "CLGSETP":
            self.coolingSETP_occ = schedule_params["coolingSETP_occ"]
            self.coolingSETP_unocc = schedule_params["coolingSETP_unocc"]
        elif self.schedule_type == "HTGSETP":
            self.heatingSETP_occ = schedule_params["heatingSETP_occ"]
            self.heatingSETP_unocc = schedule_params["heatingSETP_unocc"]

        else:
            print("Enter Valid Setpoint Schedule")

        return None

    def set_eplus_config(self):
        """
        method to automatically set default eplus configs if not provided by the user
        """

        with open('../json/eplus_params.json') as j:
            eplus_param = json.load(j)
        eplus_param['mod_file'] = '../test_idf/test.idf'

        self.eplus_param = eplus_param

        return None

    def change_SETP(self, AllSchedCompacts, schedule_name):
        """
        method to modify the temperature schedule
        :param AllSchedCompacts: list of schedule objects, imported from IDF
        :param schedule_name: str - corresponding to the schedulee name we want to use as base schedule
        """

        for schedule in AllSchedCompacts:

            # loop through all schedules, only perform operations when schedule
            # name matches base sch name
            if schedule.Name == schedule_name:
                list_of_lines = [
                    i
                    for i, x in enumerate(schedule["obj"])
                    if (x.startswith("For") or (x == ";"))
                ]  # We assume our schedules are bound by 'For:' and
                list_of_names = [
                    idx for idx in schedule["obj"] if idx.startswith("For")
                ]  # Get names
                list_of_names = [e[5:] for e in list_of_names]  # Remove "For:"

                schedule_out = ""  # iniitialize empty string
                final_string_bool = (
                    False  # string to indicate id this is the final string
                )

                # extract original schedules from the base schedule specified
                # in the IDF
                for j in range(0, len(list_of_lines)):

                    if j < len(list_of_lines) - 1:
                        sched = schedule["obj"][
                            list_of_lines[j] + 1: list_of_lines[j + 1]
                        ]
                    elif j == len(list_of_lines) - 1:
                        sched = schedule["obj"][list_of_lines[j] + 1:]
                    else:
                        sched = None

                    # perform string operations so we can process the schedule
                    # as a dataframe
                    list_of_times = [
                        idx for idx in sched if idx.startswith("Until:")]
                    list_of_times = [e[7:]
                                     for e in list_of_times]  # Remove "For:"
                    list_of_times = [
                        "23:59" if x == "24:00" else x for x in list_of_times
                    ]
                    list_of_times = ["00:00"] + list_of_times
                    list_of_temps = [
                        idx for idx in sched if not idx.startswith("Until:")
                    ]
                    list_of_temps = [list_of_temps[0]] + list_of_temps

                    # process the schedule into a dataframe
                    df_sched = pd.DataFrame()
                    df_sched["Times"] = list_of_times
                    df_sched["Times"] = pd.to_datetime(
                        df_sched["Times"], format="%H:%M"
                    )  # .dt.time
                    time_init = df_sched["Times"].iloc[0]
                    df_sched["Times"] = (
                        df_sched["Times"] - time_init
                    ).dt.total_seconds() / 60
                    df_sched["Temps"] = pd.to_numeric(list_of_temps)

                    # We have an hourly schedule. we can
                    temp_TimeSeries = self.convert_to_TimeSeries(df=df_sched)

                    # chec
                    if str(list_of_names[j]) in self.days_list:
                        self.OG_timeSeries = temp_TimeSeries

                        # get unique values in the original time series
                        _unique_temps = np.unique(self.OG_timeSeries)

                        # plotting the original time series
                        if self.plot_base_schedule is True:
                            self.plot_ts(
                                ts=self.OG_timeSeries,
                                colors={"ts": "black"},
                                fig_name=self.fig_dir+"ts_setp.eps",
                            )

                        # stochastically change schedule for multiple cases'
                        randChoice = (
                            np.random.choice(
                                [0, 1], p=[1 - self.setback_p, self.setback_p]
                            )
                        ).astype(int)

                        # when randChoice == 0, or if the original schedule
                        # does not have a setback, randChoice = 0
                        if randChoice == 0 or len(_unique_temps) == 1:
                            temp_TimeSeries = self.create_constant_sch(
                                timeSeries=self.OG_timeSeries
                            )

                        else:
                            temp_TimeSeries = self.generate_stochastic_schedules(
                                og_timeSeries=self.OG_timeSeries)

                        "Fixing extreme values in timeseries"
                        # temp_TimeSeries = self.fix_extreme_temp(
                        #     ts=temp_TimeSeries)

                        self.df = pd.DataFrame(
                            self.param_dict
                        )  # converting to a dataframe
                        self.mod_timeSeries = temp_TimeSeries

                        if self.plot_mod_schedule is True:
                            self.plot_ts(
                                ts=self.mod_timeSeries,
                                colors={"ts": "blue"},
                                fig_name=self.fig_dir+"plot_schema.svg",
                                trim_graph=True,
                            )

                    if j == len(list_of_lines) - 1:
                        final_string_bool = True

                    schedule_str = self.get_sch_str(
                        setpoint_array_mins=temp_TimeSeries,
                        days_to_pick=list_of_names[j],
                        final_str_bool=final_string_bool,
                    )

                    schedule_out += schedule_str

                "Now get the main string"
                schedule_out = self.get_header(schedule_string=schedule_out)

        return schedule_out

    def convert_to_TimeSeries(self, df):
        """
        method to convert df (at hourly interval) to a timeseries at 1-min resolution
        :param df - input dataframe
        """

        # initializing empty time series at one-minute resolution
        temp_TimeSeries = np.zeros((24 * self.hourSteps,))

        for i in range(0, len(df) - 1):
            # setting for the first n-1 setpoint temp
            temp_TimeSeries[
                int(df["Times"].iloc[i]): int(df["Times"].iloc[i + 1])
            ] = df["Temps"].iloc[i + 1]
        # setting the final setpoint temperature
        temp_TimeSeries[int(df["Times"].iloc[-1]):] = df["Temps"].iloc[0]

        return temp_TimeSeries

    def plot_ts(
        self,
        ts,
        colors=None,
        fig_name=None,
        old_ts=None,
        label_1=None,
        label_2=None,
        trim_graph=False,
    ):
        font = {"size": 20}
        plt.rcParams.update({"font.size": 20})

        t = np.arange(
            start=0, stop=24, step=self.timeRes / 60
        )  # step -> converted to hours

        if trim_graph is not False:
            plt.plot(t[t < 9], ts[t < 9], color=colors["ts"], linewidth=3)
            # plt.legend()
        elif old_ts is not None and colors is not None:
            plt.plot(
                t,
                old_ts,
                linewidth=3,
                color=colors["old_ts"],
                label=label_1)
            plt.plot(
                t,
                ts,
                color=colors["ts"],
                linewidth=3,
                linestyle="--",
                label=label_2)
            plt.legend()
        elif label_1 is not None:
            plt.plot(t, ts, color=colors["ts"], linewidth=3, label=label_1)
            plt.legend()
        else:
            plt.plot(t, ts, color=colors["ts"], linewidth=3)

        if trim_graph is False:
            plt.xlim([0, 24])
            plt.xticks(ticks=np.arange(0, 24, 6))
            plt.yticks(ticks=np.arange(14, 24, 1))
        else:
            plt.xlim([4, 7])
            plt.xticks(ticks=np.arange(4, 7, 2))
            plt.yticks(ticks=np.arange(23, 30, 1))
        plt.xlabel("Hour of Day", fontdict=font)
        plt.ylabel("Temperature (C)", fontdict=font)

        # plt.ylim([15, 23])
        plt.tight_layout()
        # plt.show()

        if fig_name is not None:
            plt.tight_layout()
            plt.savefig(fig_name)
            # plt.show()
            plt.clf()

        return None

    def change_ts(self, temp_TimeSeries):
        """
        method to change the setback profile
        :param temp_TimeSeries: np array on which operations are gpoing to be performed
        """
        # step (a) -> start with base schedule
        newTemp_TimeSeries = temp_TimeSeries.copy()

        # get the parameters from the dict
        if self.schedule_type == "CLGSETP":
            Tc_min_unocc, Tc_max_unocc = (
                self.coolingSETP_unocc["min"],
                self.coolingSETP_unocc["max"],
            )
            Tc_min_occ, Tc_max_occ = (
                self.coolingSETP_occ["min"],
                self.coolingSETP_occ["max"],
            )
            T_sc, T_oc = np.max(temp_TimeSeries), np.min(temp_TimeSeries)
        elif self.schedule_type == "HTGSETP":
            Th_min_unocc, Th_max_unocc = (
                self.heatingSETP_unocc["min"],
                self.heatingSETP_unocc["max"],
            )
            Th_min_occ, Th_max_occ = (
                self.heatingSETP_occ["min"],
                self.heatingSETP_unocc["max"],
            )
            T_sh, T_oh = np.min(temp_TimeSeries), np.max(temp_TimeSeries)

        else:
            print("Please Enter a Valid setpoint ID")

        # step (b) -> change maximum and minimum temperatures
        if self.schedule_type == "HTGSETP":
            sigma_h = np.min(
                [(Th_max_occ - T_oh) / 3, (T_sh - Th_min_unocc) / 3])
            # sigma_Tmax = (Tc_max_unocc - np.max(temp_TimeSeries))/3
            deltaT_max = np.random.normal(loc=0, scale=sigma_h)
            deltaT_min = np.random.normal(loc=0, scale=sigma_h)
        elif self.schedule_type == "CLGSETP":
            sigma_c = np.min(
                [(Tc_max_unocc - T_sc) / 3, (T_oc - Tc_min_occ) / 3])
            deltaT_max = np.random.normal(loc=0, scale=sigma_c)
            deltaT_min = np.random.normal(loc=0, scale=sigma_c)
        else:
            print("Enter valid setpoint ID")

        # hard-set for outlier schedules with extreme temepratures
        deltaT_max, deltaT_min = (
            self.clamp_deltaT(deltaT=deltaT_max),
            self.clamp_deltaT(deltaT=deltaT_min),
        )

        newTemp_TimeSeries = self.distort_schedule(
            temp_TimeSeries=newTemp_TimeSeries,
            delta_max_temp=deltaT_max,
            delta_min_temp=deltaT_min,
        )

        # step (c) -> changing the pre-heating or pre-cooling period
        l_1 = -np.log(self.p_threshSetback) / self.setback_tol
        delta_t = -np.random.exponential(scale=l_1)
        delta_t = (
            float(
                self.roundoff(
                    num=(
                        delta_t *
                        self.hourSteps))) /
            self.hourSteps)  # delta_t in hours

        # removing outliers
        delta_t = (-self.setback_tol if np.absolute(delta_t)
                   > self.setback_tol else delta_t)
        old_ts = newTemp_TimeSeries.copy()
        newTemp_TimeSeries = self.prehtg_preclg_change(
            main_sch=newTemp_TimeSeries, delta_t=int(delta_t * self.hourSteps)
        )

        t_setback = delta_t

        # step (d) -> change the morning rampup/rampdown
        # first get the time steps and the temp. differences in the base
        # schedule
        t_diff, lim_mins, temp_diff = self.rampup_limits(
            temp_TimeSeries=newTemp_TimeSeries
        )

        # compute the time period corresponding to p = 0.99
        t_max = temp_diff / self.rampup_min
        l_2 = -np.log(self.p_threshRamp) / np.absolute(t_max)

        ramp_time = []
        ramp_delta_t = []

        for i in range(len(lim_mins) - 1):
            # compute time period for morning rampup
            delta_t = np.random.exponential(scale=l_2[i])
            # roundoff to the timesteps to the nearest
            delta_t = (
                float(
                    self.roundoff(
                        num=(
                            delta_t *
                            self.hourSteps))) /
                self.hourSteps)  # in hours

            # fixing outlier values of morning rampup
            delta_t = self.max_rampHour if delta_t > self.max_rampHour else delta_t

            # we compute the start and end time for morning rampup
            # note -> we are computing both morning rampup and evening rampdown in the block below
            # as the code stands now, we will NOT use the evening rampdown. but
            # it is a possible extension
            if self.schedule_type == "CLGSETP":
                if temp_diff[i] < 0:
                    start_time = t_diff[i] - 1
                    end_time = int(t_diff[i] + self.hourSteps * delta_t) % (
                        24 * self.hourSteps
                    )
                else:
                    # t_diff > 0 -> fix end_time first
                    end_time = int(self.hourSteps * self.occupied_times["max"])
                    start_time = int(end_time - self.hourSteps * delta_t) - 1
                    # start_time = end_time
            elif self.schedule_type == "HTGSETP":
                if temp_diff[i] > 0:
                    start_time = t_diff[i] - 1  # trying out this block
                    end_time = int(t_diff[i] + self.hourSteps * delta_t) % (
                        24 * self.hourSteps
                    )
                else:
                    # t_diff > 0 -> fix end_time first
                    end_time = int(self.hourSteps * self.occupied_times["max"])
                    start_time = int(end_time - self.hourSteps * delta_t) - 1
                    # start_time = end_time
            else:
                print("invalid schedule type")

            ramp_time.append(start_time / self.hourSteps)
            ramp_delta_t.append(delta_t)

            try:
                newTemp_TimeSeries = self.schedule_rampup(
                    sch=newTemp_TimeSeries, start_time=start_time, end_time=end_time)
            except AssertionError:
                print("AssertionError -- gradient rampup did not work")
                pass

        newTemp_TimeSeries = self.roundOff_temp * np.round(
            newTemp_TimeSeries / self.roundOff_temp
        )
        newTemp_TimeSeries = np.round(
            newTemp_TimeSeries, 1)  # trim out exces deci

        # package as a dict, will be written to csv
        self.param_dict = {
            "T_max": [np.amax(newTemp_TimeSeries)],
            "T_min": [np.amin(newTemp_TimeSeries)],
            "t_p": [t_setback],
            "t_start": [ramp_time[0]],
            "t_ramp": [ramp_delta_t[0]],
            "setback": [True],
            "const_temp": [-1],
        }

        # constant temperature set to -1 because this profile has a setback

        return newTemp_TimeSeries

    def distort_schedule(self, temp_TimeSeries, **kwargs):
        """
        method to change maximum and minimum temperature (step [b] in paper)
        :param temp_TimeSeries: np.array describing setback schedule
        :return distorted_timeSeries: np array of schedule with max and min temp changed
        """

        distorted_timeSeries = temp_TimeSeries.copy()

        if "delta_max_temp" in kwargs:
            delta_max = kwargs["delta_max_temp"]
            max_temp = temp_TimeSeries.max()
            distorted_timeSeries[distorted_timeSeries == max_temp] = (
                max_temp + delta_max
            )
        if "delta_min_temp" in kwargs:
            delta_min = kwargs["delta_min_temp"]
            min_temp = temp_TimeSeries.min()
            distorted_timeSeries[distorted_timeSeries == min_temp] = (
                min_temp + delta_min
            )

        return distorted_timeSeries

    def prehtg_preclg_change(self, main_sch, delta_t, **kwargs):
        """
        method to allow for pre-heating or pre-cooling change
        :param main_sch: np.array -> time series of setback schedule on which prehtg/preclg will be added
        :param delta_t: float -> time period for prehtg/preclg in mins
        :param t (optional): float -> where the gradeint change occurs.
        :return dist_sch: np. array -> setback schedule after prehtg/preclg has been added
        """
        if "t" in kwargs:
            t = kwargs["t"]
            tSteps = int(t / self.timeRes)
        else:
            diffSeries = pd.Series(main_sch).diff()

            if self.schedule_type == "CLGSETP":
                idx_to_change = np.where(np.nan_to_num(diffSeries.values) < 0)[0]
            elif self.schedule_type == "HTGSETP":
                idx_to_change = np.where(np.nan_to_num(diffSeries.values) > 0)[0]
            tSteps = idx_to_change[0]

        # note: originally the code block below was developed to allow the extension for evening heating/cooling extension/curtailment
        # we will not apply that for this work, but that extension is possible
        # - hence the if/else statements

        T = 24 * self.hourSteps  # total number of timesteps in a day
        delta_tSteps = int(delta_t / self.timeRes)
        # translate profile
        # extract the first 24 hours if repeating
        dist_sch = main_sch.copy()[0:T]
        # extract out the boundary of the profile
        if tSteps + delta_tSteps < 0:  # delt
            # recall the extrasteps that's less than zero:
            alpha_t = int(np.absolute(tSteps + delta_tSteps))
            dist_sch[0:tSteps] = main_sch[tSteps + 1]
            dist_sch[T - alpha_t: T] = main_sch[tSteps + 1]
        elif tSteps + delta_tSteps > T:
            alpha_t = tSteps + delta_tSteps - T
            dist_sch[tSteps:] = main_sch[tSteps - 1]
            dist_sch[0:alpha_t] = main_sch[tSteps - 1]
        else:
            if delta_tSteps < 0:
                # take a small step in the postive dir.
                dist_sch[tSteps + delta_tSteps: tSteps] = main_sch[tSteps + 1]
            else:
                dist_sch[tSteps: tSteps + delta_tSteps] = main_sch[tSteps - 1]

        return dist_sch

    def rampup_limits(self, temp_TimeSeries):
        """ "
        method to determine the time period corresponding to probability = 0.99
        :param temp_TimeSeries: np.array(float) for schedule before rampup implemented
        :return t_diff: np.array(int) -> timesteps where gradients exist in schedule
        :return limit_mins: np.array(int) -> time in mins where gradients exist. = t_diff when self.timeRes = 1 min
        :return temp_diff: np.array(float) -> temp. differences corresponding to t_diff and limit_mins
        """

        idx_diff = np.where(pd.Series(temp_TimeSeries).diff() != 0)[0]
        temp_diff = temp_TimeSeries[idx_diff] - temp_TimeSeries[idx_diff - 1]
        idx_diff = idx_diff - 1  # one timestep-1 to make sure there is a gradient
        limitSteps_list = []

        for i, idx in enumerate(idx_diff):
            if i < len(idx_diff) - 1:
                time_diff = idx_diff[i + 1] - idx_diff[i]
                # number of timesteps to go in the positive dir.
                limit_steps = np.min(
                    [time_diff, self.max_rampHour * self.hourSteps])
            else:
                # 'Case corresponding to the case where the next gradient exists overnight.
                # won't be used in our work, but extension possible
                time_diff = (24 * self.hourSteps - idx_diff[i]) + idx_diff[0]
                limit_steps = np.min(
                    [time_diff, self.max_rampHour * self.hourSteps])

            limitSteps_list.append(limit_steps)

        # getting rid of the first datapoint (it's an artifact of diff function
        # and is meaningless)
        t_diff = 1 + idx_diff[1:] * self.timeRes
        limit_mins = np.asarray(limitSteps_list)[1:] * self.timeRes
        temp_diff = temp_diff[1:]

        return t_diff.astype(int), limit_mins.astype(int), temp_diff

    def schedule_rampup(self, sch, start_time, end_time):
        """
        method to add rampup to a schedule
        :param sch: np.array (flaot) -> time series  before rampup
        :param start_time: float -> start time for rampup
        :param end_time: float -> end_time for rampup
        """

        def is_valid(t1, t2):
            "This function validtes that we can actually ramp up the temperature at the specified timesteps"
            val = False if sch[t1] == sch[t2] else True

            return val

        def fix_ramped_array(X, t_res, timeRes):
            """
            method to make sure that the portion that is ramped is "uniformly" distributed
            note that the ramp occurs at every timestep (=self.rampRes_mmin. in our work, we have used 15 mins)
            :param X: np.array (float) - portion of the schedule being ramped
            :t_res: int/float -> time interval at which ramping ocuurs (=self.rampres_min)
            :timeRes: int/float -> time resolution of the generated schedule (=self.timeRes)
            :return ramp_sch: np.array (float) - setback schedule after ramping
            """

            tSteps = int(t_res / timeRes)
            N = int(np.ceil(len(X) / tSteps))
            X_out = np.zeros_like(X)

            for n in range(N):
                if n < N - 1:
                    # pick value at beginning of timesteps
                    X_out[n * tSteps: (n + 1) * tSteps] = X[n * tSteps]
                else:
                    X_out[n * tSteps:] = X[n * tSteps]

            return X_out

        tStep_start = int(start_time / self.timeRes)
        tStep_end = int(end_time / self.timeRes)  # add one here

        assert is_valid(tStep_start, tStep_end)
        ramp_sch = sch.copy()

        # need to account for the periodicity

        if tStep_start < tStep_end:
            ramped_temp = np.linspace(
                start=sch[tStep_start],
                stop=sch[tStep_end],
                num=(tStep_end - tStep_start),
                endpoint=False,
            )  # setting up linearly spaced schedules
            ramped_temp = fix_ramped_array(
                X=ramped_temp, t_res=self.rampRes, timeRes=self.timeRes
            )
            ramp_sch[tStep_start:tStep_end] = ramped_temp
        else:
            T = 24 * self.hourSteps

            ramped_temp = np.linspace(
                start=sch[tStep_start],
                stop=sch[tStep_end],
                num=(T + tStep_end - tStep_start),
                endpoint=False,
            )  # setting up linearly spaced schedules
            ramped_temp = fix_ramped_array(
                X=ramped_temp, t_res=self.rampRes, timeRes=self.timeRes
            )
            ramp_sch[tStep_start:T] = ramped_temp[: T - tStep_start]
            ramp_sch[0:tStep_end] = ramped_temp[T - tStep_start:]

        return ramp_sch

    def create_constant_sch(self, timeSeries):
        """
        method to create no setback schedules. stochastically selects a constant parameter
        :param timeSeries: np.array(float)
        original schedule - could be setback or no setback. we only need it to get the size of array
        :return new_timeSeries: time series with no-setback, same size and resolution as timeSeries
        """

        if self.schedule_type == "CLGSETP":
            meanTemp = self.coolingSETP_occ["mean"]
            # set limit to 3-sigma values
            std = (meanTemp - self.coolingSETP_occ["min"]) / 3
        elif self.schedule_type == "HTGSETP":
            meanTemp = self.heatingSETP_occ["mean"]
            # set limit to 3-sigma values
            std = (meanTemp - self.heatingSETP_occ["min"]) / 3
        else:
            print("Enter valid setpoints")

        "Drawwing temperature from a normal distribution"
        sampledTemp = np.random.normal(loc=meanTemp, scale=std)
        new_timeSeries = sampledTemp * np.ones_like(timeSeries)

        # rounding off the time series.
        newTemp_TimeSeries = self.roundOff_temp * np.round(
            new_timeSeries / self.roundOff_temp
        )
        newTemp_TimeSeries = np.round(
            newTemp_TimeSeries, 1)  # trim out exces deci
        new_timeSeries = newTemp_TimeSeries

        self.param_dict = {
            "T_max": [-1],
            "T_min": [-1],
            "t_p": [-1],
            "t_start": [-1],
            "t_ramp": [-1],
            "setback": False,
            "const_temp": [sampledTemp],
        }

        return new_timeSeries

    def roundoff(self, num):
        """
        method to round off the time to the nearest 15 minute resolution (or whatever resolution specified in self.ramRes
        :param num: float -> time period in minutes
        :return valout: int -> time priod rounded off to the nearest resolution specified in self.ramRes
        """
        valout = int(num / float(self.rampRes)) * int(self.rampRes)

        return valout

    def generate_stochastic_schedules(self, og_timeSeries):
        """
        method to run setback schedules.
        :param og_timeSeries: np.array(float) original setback schedule
        :return new_timeSeries: np.array(float) new time series
        """

        new_timeSeries = self.change_ts(temp_TimeSeries=og_timeSeries)

        return new_timeSeries

    def get_header(self, schedule_string):
        """
        method to add the header and format the string written to IDF
        :param schedule_string: str -> contns part of the schedule that is edited based on new setback schedule
        :param header_out: str ->
        """

        header_string = """
       Schedule:Compact,
           {name},  !- Name
           Temperature,             !- Schedule Type Limits Name
           Through: 12/31,          !- Field 1
           {rest_of_schedule}"""

        to_substitute = {
            "name": self.schedule_name_edited,
            "rest_of_schedule": schedule_string.lstrip(),
        }
        header_out = header_string.lstrip().format(**to_substitute)

        return header_out

    # file to clamp delta T if it is too large

    def clamp_deltaT(self, deltaT, thresh_high=3.0, thresh_low=-3.0):
        """
        this function clamps deltaT in case for a stochasticc sample it gets unrealistically large or low
        :param deltaT: change in temperature deltaT
        :return: deltaT -> float
        """
        if deltaT > thresh_high:
            deltaT = thresh_high
        elif deltaT < thresh_low:
            deltaT = thresh_low
        else:
            pass

        return deltaT

    def write_to_idf(self, edited_schedule, idf_file, new_file):
        """
        method to write schedule to IDF
        :param edited_schedule: str -> schedule that is edited
        :param idf_file: original IDF from which base schedule is extracted
        :param new_file: name of new file to which the schedule is written
        """

        idf_0 = IDF(idfname=idf_file)
        idf_0.saveas(new_file)

        with open(new_file, "a") as file:
            file.write("\n\n")
            file.write(edited_schedule)

        idf = IDF(idfname=new_file)
        # IDF.setiddname(self.idd_file)
        DualSetpoints = idf.idfobjects["ThermostatSetpoint:DualSetpoint"]

        if self.schedule_type == "CLGSETP":
            for DualSetpoint in DualSetpoints:
                DualSetpoint[
                    "Cooling_Setpoint_Temperature_Schedule_Name"
                ] = self.schedule_name_edited
        elif self.schedule_type == "HTGSETP":
            for DualSetpoint in DualSetpoints:
                DualSetpoint[
                    "Heating_Setpoint_Temperature_Schedule_Name"
                ] = self.schedule_name_edited
        else:
            print("Enter Valid SETP")

        idf.saveas(new_file)

        return None

    # ---------------------------------------------------------------
    def get_sch_str(
            self,
            setpoint_array_mins,
            days_to_pick,
            final_str_bool=True):
        """
        method to convert the numpy array to a schedule string that can be written to IDF file
        :param setpoint_array_mins: np.array (float) - time series array in mins
        :param days_to_pick: str -> coorresponds to the days in week for which schedule is being written
        (e.g. weekdays/weekends, etc.)
        :final_str_bool: bool -> indicates whether or not it is the last line to be written
        """

        # find where the gradients lie
        mins = np.where(setpoint_array_mins[:-1] != setpoint_array_mins[1:])[0]

        time = []
        temperature = []

        for element in mins:
            hour = (int(element) + 1) / 60
            minutes = (int(element) + 1) % 60
            formatted_time = "%02d" % (int(hour)) + ":" + "%02d" % minutes
            time.append(formatted_time)
            temperature.append(setpoint_array_mins[element])

        dict_of_time_temp = dict(zip(time, temperature))

        # Creating the schedule as a string

        s = ""  # the string
        schedule_string = """
                Until: {time},{temperature},"""  # Template for the string

        for key, value in sorted(dict_of_time_temp.items()):
            to_substitute = {"time": key, "temperature": value}
            s += schedule_string.format(**to_substitute)

        if final_str_bool:
            s += (  # The last peice
                """
                Until: 24:00,{};"""
            ).format(setpoint_array_mins[-1])
        else:
            s += (  # The last peice
                """
                Until: 24:00,{},"""
            ).format(setpoint_array_mins[-1])

        to_substitute = {"for": "For: " +
                         days_to_pick, "rest_of_schedule": s[7:]}

        schedule_string = """
                {for},    !- Field 2
               {rest_of_schedule}"""

        edited_schedule = schedule_string.format(**to_substitute)

        return edited_schedule


def test_schedule():
    """
    function to test if the generated schedules are working
    """

    param_file = "../json/htgsetp_params.json"
    with open(param_file) as j:
        sch_params = json.load(j)

    np.random.seed(80)
    setp_sch = Setpoint_Schedule(schedule_params=sch_params)

    return None


if __name__ == "__main__":
    test_schedule()
