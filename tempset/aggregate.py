import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime, timedelta
import gzip
import time

import pkg_resources
import logging

from joblib import Parallel, delayed
from tempset.logger import Logger

class AggregateOutput(Logger):

    def __init__(self,
                 gz_dir,
                 summary_file='./output_dir/summary.csv',
                 output_dir = './output_dir',
                 write_logfile=False
                 ):

        # start time for model run
        self.start_time = time.time()

        self.logfile = os.path.join(output_dir, f'tempset_logfile_{self.start_time}.log')
        self.write_logfile = write_logfile

        # initialize console handler for logger
        self.console_handler()

        if self.write_logfile:
            self.file_handler()

        logging.info('Starting batch processing of IDF files')

        # inherit logger class attributes
        super(AggregateOutput, self).__init__(self.write_logfile, self.logfile)

        self.gz_dir = gz_dir
        self.summary_file = summary_file
        self.convert_J_to_kWh = 2.777e-7

        #execute aggregation
        self.aggregate_data(gz_dir=self.gz_dir)

    def parse_filelname(self, filename):

        """
        method to parse string name to get simulation id and intiial str name
        :param filename: str -> filename ending with .gz
        :return id: int -> simulation id corresponding to the .gz file
        :return file_init: str -> str corresponding to the initial file
        """
        file_init = filename.split('.')[0]
        id = file_init.split('_')[-1]  # the last digit is the number

        return id, file_init

    def read_gz_files(self, filename):

        """
        method to read gz file to extract DF
        :param filename: file ending with a gz
        :return df: DataFrame -> corresponding to the simulation outputs
        """

        with gzip.open(filename) as f:
            'Read each file'
            df = pd.read_csv(f)

        return df

    def remove_design_day(self, df):
        """
        method to remove design day from simulation output
        :param df: pd.DataFrame -> df containing output simulations including design day
        :return df_o: pd.DataFrame -> df containing output simulations wiihout design day
        """
        start_date = ' 01/01'
        date_stamps = df['Date/Time']

        idx_all = np.where(date_stamps.str.startswith(start_date))[
            0]  # check where df starts with first of Jan, everything before is DD
        # print('idx all: ', idx_all)
        first_idx = idx_all[0]

        df_o = (df.iloc[first_idx:]).reset_index(drop=True)

        return df_o

    def create_df_daily(self, df_mtr, df_out, timeRes=24):
        """
        method to aggregate results at a daily timescale
        :param df_mtr: pd.DataFrame -> df containing outputs from  mtr file in e+ simulations
        :param df_out: pd.DatFrame -> df containing outputs from output file in e+ simulations
        :param timeRes: int -> time resolution over which data is to be aggregated
        :return df_elec_sum:  pd.Series -> outputs aggregating the total electricity consumption
        :return df_elec_peak: pd.Series -> outputs to find the maximum hourly consumption
        :return df_tc_mean: pd.Series -> outputs containing aggregated mean PPD in core zone
        """

        df_elec = df_mtr['Electricity:Facility [J](Hourly)'] * self.convert_J_to_kWh
        df_elec_mean = df_elec.rolling(window=timeRes).sum()
        df_elec_peak = df_elec.rolling(window=timeRes).max()

        df_elec_mean = df_elec_mean.dropna().reset_index(drop=True)  # drop Nan values
        df_elec_sum = df_elec_mean[::timeRes].reset_index(drop=True)
        df_elec_peak = df_elec_peak.dropna().reset_index(drop=True)
        df_elec_peak = df_elec_peak[::timeRes].reset_index(drop=True)

        'Thermal Comfort Mean'
        'Add more zones if necessary'
        hr = df_out.index.values % timeRes + 1
        df_out['hr'] = hr
        # print('hr: ', hr)
        df_tc = df_out['CORE_ZN:Zone Thermal Comfort Fanger Model PPD [%](Hourly)']  # mean across different zonesi
        df_tc[((hr <= 7) | (hr > 18))] = 0
        df_tc_mean = df_tc.rolling(window=timeRes).sum() / 11
        df_tc_mean = df_tc_mean.dropna().reset_index(drop=True)
        df_tc_mean = df_tc_mean[::timeRes].reset_index(drop=True)

        return df_elec_sum, df_elec_peak, df_tc_mean

    'Global functions for plotting'

    def generate_date_axis(self, day_array=np.arange(0, 365), day_start=0, year=2017):
        """
        method to generate a date exis given integer array
        :param day_start: np.array -> containing the number of days for which the date needs to be generated
        :param year: int -> year (2017 in e+ simulations)
        :return df_time: pd.Series: datetime corresponding to day_start + day_array
        """
        dt = datetime(year, 1, 1)
        dtDelta = timedelta(days=day_start)
        init_time = dt + dtDelta

        out_time = [init_time + timedelta(days=int(i)) for i in day_array]
        df_time = pd.to_datetime(out_time).to_series()
        df_time.reset_index(drop=True, inplace=True)

        return df_time

    def aggregate_data(self, gz_dir):

        """
        method to compile all functions to generate summary file
        :param gz_dir:
        :return:
        """

        # Get the data axis'
        days = self.generate_date_axis()
        self.list_of_files = sorted(glob.glob('*.csv.gz'))
        main_dir = os.getcwd()
        os.chdir(gz_dir)


        # initialize empty summary file
        summary = []

        for filename in sorted(glob.glob('*.csv.gz')):

            num_period = filename.count('.')
            file_init = filename.split('.')[0]
            sim_number = file_init.split('_')[-1]

            if num_period == 2:  # only two periods 2 in strings, 2 in decimals or if the string is the reference file

                id, file_str = self.parse_filelname(filename=filename)

                df_out = self.read_gz_files(filename=filename)


                meter_file = file_str + '.meter.csv.gz'
                df_meter = self.read_gz_files(filename=meter_file)

                'Remove design days and append to llist'
                df, df_meter = self.remove_design_day(df_out), self.remove_design_day(df_meter)

                'Get the daily dataframes'
                df_e, df_p, df_tc = self.create_df_daily(df_mtr=df_meter, df_out=df)
                data = {'date': days, 'daily_elec_total': df_e, 'daily_elec_peak': df_p, 'daily_tc_mean': df_tc}

                df = pd.DataFrame(data)
                df['sim_id'] = sim_number

                summary.append(df)

                logging.info(f"Completed read for filename:  {filename}")

        df_summary = pd.concat(summary)
        df_summary.to_csv(self.summary_file)

        'Get back to the main working directory'
        os.chdir(main_dir)

        return None




def aggregate_data(gz_dir,
                   summary_file):
    """
    wrapper to call AggregateOutput class to generate summary file
    :param gz_dir: str -> full path hosting the .gz directory
    :param summary_file: strt -> full path to .csv file where the output summaries are to be written
    :return:
    """

    AggregateOutput(gz_dir=gz_dir, summary_file=summary_file)

    return None


if __name__ == "__main__":
    gz_dir = '/projects/im3/bend/aowabin_test/tbd/output'
    summary_file = '/projects/im3/bend/aowabin_test/tbd/dump/dump.csv'
    aggregate_data(gz_dir=gz_dir, summary_file=summary_file)
