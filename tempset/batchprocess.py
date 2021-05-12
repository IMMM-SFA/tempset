import pandas as pd
import json
import os
import time

import pkg_resources
import logging

from joblib import Parallel, delayed

from tempset.logger import Logger
from tempset.schedules import Setpoint_Schedule


class BatchIdf(Logger):
    def __init__(self, eplus_config, param_json, batch_param, htgsetpoint_params_csv_output=None, output_dir=None,
                 write_logfile=False, idf_file=None, idd_file=None):
        """
        :param eplus_config: str-> json file containing eplus config info (idd_name, idf_name, name for new_idf
        :param param_json: str-> json file containing arams needed to generate stochastic schedules
        :param batch_param: str-> json file containing params associated with generating batches of IDFs
        """
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
        super(BatchIdf, self).__init__(self.write_logfile, self.logfile)

        self.csv_file = htgsetpoint_params_csv_output
        self.new_dir = output_dir

        with open(eplus_config) as j1, open(param_json) as j2, open(batch_param) as j3:
            self.eplus_param = json.load(j1)
            self.param_json = json.load(j2)
            self.batch_param = json.load(j3)

        if idf_file is None:
            self.idf_file = pkg_resources.resource_filename('tempset', 'data/idf/gas.idf')
        else:
            self.idf_file = idf_file

        # self.idf_file = self.eplus_param["idf_file"]

        self.idd_file = idd_file

        # get batch param'
        self.get_batch_param(batch_param=self.batch_param)

        # create directory'
        self.create_new_dir()

        # create idfs in parallel'
        self.execute_in_parallel()

    def get_batch_param(self, batch_param):
        """
        method to extract values from batch_param
        :batch_param: dict -> containing relevant params needed to generate IDFs in batch
        """

        self.max_iter = batch_param["max_iter"]
        # self.csv_file = batch_param["csv_file"]

        # self.new_dir = batch_param[
        #     "new_dir"
        # ]  # name of directory where the idfs will be moved

        self.n_jobs = batch_param["n_jobs"]

        return None

    def create_new_dir(self):
        """ "
        method to create new dir with name self.new_dir
        """
        if not os.path.exists(self.new_dir):
            os.makedirs(self.new_dir)

        return None

    def create_filename(self, i):
        """
        Creates a filename for each new IDF in the batch
        :param i: int -> index corresponding to file ID in batch
        :return file_str_new: str -> string name for file
        """
        _idfname = self.idf_file

        # changing the init
        init_str = _idfname.split("/")[:-1]  # separating out the main_str
        init_str = "/".join(init_str)
        file_str = _idfname.split("/")[-1]
        file_str = file_str.split(".")[0]  # removing .idf at the end

        # modify this line to make sure the directory is outside the tempset
        # dir
        file_str_new = init_str + "/" + file_str + "_" + str(i) + ".idf"

        return file_str_new

    def create_new_idfs(self, i):
        """
        method to generate a new IDF and maintaining a dataframe to keep track of simulation parameters
        :param i: int -> id of filename
        :return df: dataframe -> contains details of all simulations
        """
        new_file = self.create_filename(i)

        df = self.generate_schedules(new_filename=new_file)

        # adding simulation ID to dataframe'
        df["sim_id"] = i
        df["file_name"] = new_file

        "Move file to directory -> self.new_dir"
        new_str = new_file.split("/")[-1]  # get the last string

        new_path = os.path.join(self.new_dir, new_str)
        # new_path = "./" + self.new_dir + "/" + new_str
        os.replace(new_file, new_path)

        logging.info(f"Created file:  {new_path}")

        return df

    def generate_schedules(self, new_filename):
        """
        method generate new schedules by calling Setpoint Schedule
        :param new_filename: str -> name of new file being generated
        :return Sch_obj.df: dataframe corresponding containing schedule parameter for one single schedule
        """
        self.eplus_param['mod_file'] = new_filename
        Sch_obj = Setpoint_Schedule(schedule_params=self.param_json, eplus_param=self.eplus_param, idd_file=self.idd_file)

        return Sch_obj.df

    def execute_in_parallel(self):
        """
        method to create IDFs in parallel, and tally all the schedule info into a single csv
        """

        df_list = Parallel(n_jobs=self.n_jobs)(
            delayed(self.create_new_idfs)(i) for i in range(self.max_iter)
        )
        # df_schParam keeps track of all the parameters associated with the
        # schedule name
        df_schParam = pd.concat(df_list)
        df_schParam.to_csv(self.csv_file)

        return None


def batch_process_idf(eplus_config, param_json, batch_param, htgsetpoint_params_csv_output=None, output_dir=None,
                      write_logfile=False, idf_file=None):
    """Batch process IDF files.

    :param eplus_config: str-> json file containing eplus config info (idd_name, idf_name, name for new_idf
    :param param_json: str-> json file containing arams needed to generate stochastic schedules
    :param batch_param: str-> json file containing params associated with generating batches of IDFs

    """

    BatchIdf(eplus_config=eplus_config,
             param_json=param_json,
             batch_param=batch_param,
             htgsetpoint_params_csv_output=htgsetpoint_params_csv_output,
             output_dir=output_dir,
             write_logfile=write_logfile,
             idf_file=idf_file)


if __name__ == "__main__":
    eplus_file = "../json/eplus_params.json"
    batch_file = "../json/batch_params.json"
    param_file = "../json/htgsetp_params.json"

    BatchIdf(eplus_config=eplus_file, param_json=param_file, batch_param=batch_file)
