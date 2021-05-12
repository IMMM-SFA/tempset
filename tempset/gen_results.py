import pandas as pd
import numpy as np
import os
import calendar

import holidays

import statutils


import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 16})


YEAR = 2017
convert_kwh_to_kBtu = 3.412
convert_J_to_kWh = 2.777e-7


class results:
    def __init__(
        self,
        summary_file="../data/electric/summary.csv",
        param_file="../data/electric/htgsetp_params_electric.csv",
        case_study="I",
        fig_dir="../figures/prob_dist",
        fig_ext=".svg",
    ):

        # get values from arguments
        self.summary_file = summary_file
        self.param_file = param_file
        self.case_study = case_study
        self.fig_dir = fig_dir
        self.fig_ext = fig_ext

        if case_study == "I":
            self.months_to_simulate = [
                "January",
                "February",
                "March",
                "April",
                "November",
                "December",
            ]
            self.labels = ["Setback", "No setback"]
        elif case_study == "IIA":
            self.months_to_simulate = [
                "January",
                "February",
                "March",
                "April",
                "November",
                "December",
            ]
            self.labels = ["$T_{op,heat} \\leq 21~C$", "$T_{op,heat} > 21~C$"]
        elif case_study == "IIB":
            self.months_to_simulate = [
                "January",
                "February",
                "March",
                "April",
                "November",
                "December",
            ]
            self.labels = ["$t_{p} > 0$", "$t_{p} = 0$"]
        elif case_study == "III":
            self.months_to_simulate = [
                "May", "June", "July", "August", "September"]
            self.labels = ["Setback", "No setback"]
        else:
            print("Enter valid case study. Valid entries")

        if not os.path.exists(self.fig_dir):
            os.makedirs(self.fig_dir)

        self.df, self.df_month, self.df_param = self.read_csv()
        self.prob_distributions()

    def prob_distributions(self):
        """
        method to compute and plot probability distributions
        """

        def set_foldername(fig_dir, m):
            """
            function to create directories by month, in which monthly probability plots will be saved
            """
            month = calendar.month_name[m + 1]
            path_name = fig_dir + "/" + str(month)

            os.chdir(path=fig_dir)

            if not os.path.exists(month):
                os.makedirs(month)
                print(os.getcwd())

            os.chdir("..")

            return path_name, str(month)

        def plotter(
            data,
            labels,
            bin_size,
            xlabel,
            fig_name,
            ylim=None,
            title=None,
            package="matplotlib",
        ):
            """
            function to plot probability distributions
            :param labels: list of str -> corresponding to baseline and modified case (=self.labels)
            :param data: list of dataframe (length = 2) -> corresponding to baseline and modified for a given month
            :param bin_size: int -> bin size for histogram
            :param xlabel: x axis label
            :param fig_name: str
            :param ylim: list -> ylim of y axis
            :param title: str
            :param package: str -> 'matplotlib', don't try anything else!
            """

            if package == "matplotlib":
                plt.rcParams.update({"font.size": 20})
                plt.hist(
                    data[0],
                    density=True,
                    bins=bin_size,
                    alpha=0.5,
                    histtype="bar",
                    color="tab:blue",
                    stacked=True,
                    label=labels[0],
                )
                plt.axvline(
                    x=data[0].median(),
                    color="darkblue",
                    linestyle="--",
                    linewidth=1.5)
                plt.hist(
                    data[1],
                    density=True,
                    bins=bin_size,
                    alpha=0.5,
                    histtype="bar",
                    color="tab:orange",
                    stacked=True,
                    label=labels[1],
                )
                plt.axvline(
                    x=data[1].median(),
                    color="darkred",
                    linestyle="--",
                    linewidth=1.5)
                plt.xlabel(xlabel=xlabel)
                plt.ylabel(ylabel="PDF")
                if ylim is not None:
                    plt.ylim(ylim)
                if title is not None:
                    plt.title(title)
                plt.legend()
                plt.tight_layout()
                plt.savefig(fig_name)
                plt.clf()

            return None

        # parse data
        df_list_1, df_list_2 = self.parse_data()

        # for each month, we can compute a probability distribution
        for m, (df_1, df_2) in enumerate(zip(df_list_1, df_list_2)):

            df_1, df_2 = remove_holidays(df=df_1), remove_holidays(
                df=df_2
            )  # removes weekends
            df_1, df_2 = remove_federal_holidays(
                df=df_1), remove_federal_holidays(
                df=df_2)  # removes federal holidays

            df_e1, df_p1, df_tc1 = (
                (df_1["daily_elec_total"]),
                (df_1["daily_elec_peak"]),
                (df_1["daily_tc_mean"]),
            )

            df_e2, df_p2, df_tc2 = (
                (df_2["daily_elec_total"]),
                (df_2["daily_elec_peak"]),
                (df_2["daily_tc_mean"]),
            )
            data_e, data_p, data_tc = [
                df_e1, df_e2], [
                df_p1, df_p2], [
                df_tc1, df_tc2]

            path_name, month = set_foldername(fig_dir=self.fig_dir, m=m)
            if month in self.months_to_simulate:

                "Step 03: Use Plotter"
                fig_name = path_name + "/" + "elec_consumption" + self.fig_ext
                plotter(
                    data=data_e,
                    labels=self.labels,
                    bin_size=75,
                    xlabel="$y_1$ (kWh)",
                    fig_name=fig_name,
                )

                fig_name = path_name + "/" + "daily_peak" + self.fig_ext
                plotter(
                    data=data_p,
                    labels=self.labels,
                    bin_size=75,
                    xlabel="$y_2$ (kWh)",
                    fig_name=fig_name,
                    title=month,
                    ylim=[0, 0.40],
                )  # lim = [0, 0.40]

                fig_name = path_name + "/" + "daily_tc" + self.fig_ext
                plotter(
                    data=data_tc,
                    labels=self.labels,
                    bin_size=75,
                    xlabel="$y_3$(%)",
                    fig_name=fig_name,
                    title=month,
                )  # ylim = [0, 1.30]

                "Get Results of statistical Tests"
                print("-----------------------NEW MONTH---------------------- ")
                print("month: {}".format(month))
                print(
                    "The p-value (Total Electricity) for {} is {}".format(
                        calendar.month_name[m + 1],
                        statutils.non_parametric(df_e1, df_e2),
                    )
                )
                print(
                    "The p-value (Peak Demand) for {} is {}".format(
                        calendar.month_name[m + 1],
                        statutils.non_parametric(df_p1, df_p2),
                    )
                )
                print(
                    "The p-value (TC) for {} is {}".format(
                        calendar.month_name[m + 1],
                        statutils.non_parametric(df_tc1, df_tc2),
                    )
                )

                print(
                    "The median values (Total Electricity) for {} are {}, {}".format(
                        calendar.month_name[m + 1], df_e1.median(), df_e2.median()
                    )
                )
                print("The median values(Peak Demand) for {} are {}, {}".format(
                    calendar.month_name[m + 1], df_p1.median(), df_p2.median()))
                print(
                    "The median values (thermal comfort) are {} is {}, {}".format(
                        calendar.month_name[m + 1], df_tc1.median(), df_tc2.median()
                    )
                )

                print("----CHange in medians-----")
                print(
                    "Total Daily: ",
                    (df_e1.median() - df_e2.median()) / (df_e2.median()),
                )
                print("Peak Daily: ",
                      (df_p1.median() - df_p2.median()) / (df_p2.median()))
                print("TC mean: ", df_tc1.median() - df_tc2.median())

        return None

    def parse_data(self):
        """
        method to call self.set_query, and then partition data by month
        :return
        """

        df_p1, df_p2 = self.set_query(df=self.df_param)
        simid_1, simid_2 = df_p1["sim_id"].values, df_p2["sim_id"].values

        list_1, list_2 = [], []

        for df in self.df_month:
            df_1, df_2 = df[df["sim_id"].isin(
                simid_1)], df[df["sim_id"].isin(simid_2)]
            list_1.append(df_1)
            list_2.append(df_2)

        return list_1, list_2

    def set_query(self, df):
        """
        method to identify two sets of data for proobability distribution based on self.case study
        :return df_1: dataframe corresponding to Modified case
        :return df_2: dataframe corresponding to Baseline case
        """
        gamma = (df["T_max"] - df["T_min"]) / df["t_ramp"]
        gamma[gamma == np.inf] = 0

        if self.case_study == "I" or self.case_study == "III":
            bool_1 = df["setback"]
            bool_2 = df["setback"] == False
        elif self.case_study == "IIA":
            bool_1 = (df["setback"]) & (df["T_max"] <= 21)
            bool_2 = (df["setback"]) & (df["T_max"] > 21)
        elif self.case_study == "IIB":
            bool_1 = df["t_p"].abs() > 0
            bool_2 = df["t_p"].abs() <= 0
        else:
            print("Please Enter Valid Case Study. Valid Entries: I, IIA, IIB, III")

            return None

        df_1, df_2 = df[bool_1], df[bool_2]

        return df_1, df_2

    def read_csv(self):
        """
        method to read summary files (from simulations) and parameter files
        :return df: dataframe -> entire summary file (from e+ simulations)
        :return df_month: list of dataframes -> grouped by month
        :return df_param: dataframe -> parameter file created in batchprocess.py
        """

        df = pd.read_csv(self.summary_file)
        df.index = pd.to_datetime(df["date"])
        df_list = df.groupby(pd.Grouper(freq="M"))

        df_month = [grp for _, grp in df_list]

        "Read the param file"
        df_param = pd.read_csv(self.param_file)

        return df, df_month, df_param


def remove_holidays(df):
    """This function is to remove all the weekends from the histogram"""

    # check weekends"
    dayofweek = (
        df.index.dayofweek.values
    ) % 7  # shifting to a sunday start, as in energyplus
    df["weekday"] = dayofweek <= 4
    df = df[df["weekday"]]

    return df


def remove_design_day(df):
    """
    This function removes the design days from the dataframe
    """
    start_date = " 01/01"
    date_stamps = df["Date/Time"]

    idx_all = np.where(date_stamps.str.startswith(start_date))[
        0
    ]  # check where df starts with first of Jan, everything before is DD
    # print('idx all: ', idx_all)
    first_idx = idx_all[0]

    df_o = (df.iloc[first_idx:]).reset_index(drop=True)

    return df_o


def remove_federal_holidays(df, year=YEAR):
    """

    :param df: input dataframe
    :param year: year for which the holiday list needs to be determined. default -> global variable YEAR
    :return: Dataframe without holidays included
    """

    holiday_list = holidays.US(years=year)

    if not str(df["date"].dtype).startswith("datetime64"):
        df["date"] = pd.to_datetime(df["date"])

    # df_date = df['date'].copy()
    df.reset_index(drop=True, inplace=True)

    for holiday in holiday_list:
        df = df[df["date"] != holiday]

    return df


def test_function():
    results(
        summary_file="../data/electric/summary.csv",
        param_file="../data/electric/htgsetp_params_electric.csv",
        case_study="I",
        fig_dir="../figures/prob_dist",
        fig_ext=".svg",
    )

    return None


if __name__ == "__main__":
    # sample_results = results()
    test_function()
