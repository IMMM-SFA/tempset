# tempset

BEND temperature set point SA study

## Getting Started Using the `tempset` Package

The `tempset` package has been verified for **Python 3.7** and up.

### Step 1:

You can install `tempset` by running the following from your cloned directory (NOTE: ensure that you are using the
desired `pip` instance that matches your Python3 distribution):

`pip3 install git+https://github.com/IMMM-SFA/tempset --user`

### Step 2:

Confirm that the module and its dependencies have been installed by running from your prompt:

```python
import tempset
```

If no error is returned then you are ready to go!

## Functionality
There are three main functions provided in this package:

1. **`batch_process_idf()`**: generating a distribution of temperature setpont schedules, with each schedule written to
a separate IDF:

```python
import tempset

eplus_file = tempset.get_example_eplus_file()
batch_file = tempset.get_example_batch_file()
param_file = tempset.get_example_htgsetp_file()
output_dir = "<your desired output directory>"

tempset.batch_process_idf(eplus_config=eplus_file,
                          param_json=param_file,
                          batch_param=batch_file,
                          htgsetpoint_params_csv_output=None,
                          output_dir=output_dir,
                          write_logfile=False,
                          idf_file=None)
```

2. **`aggregate_data()`**: aggregating EnergyPlus outputs at an hourly/sub-hourly resolution per day.

    After the IDFs are generated, you can run E+ simulations to get the outputs. `Makefile` to run the simulations is provided here. `tempset` expects the outputs in a `.csv.gz` format. These can be created from EnergyPlus outputs by the `Makefile` provided in this repository after changing the `DIR_INPUT` and `DIR_OUTPUT` in the to reflect your local directory. Then run `make all` to compile the files.

    For user convenience, we provide a preprocessed subset of these outputs that you can retrieve like the following:

```python 
import tempset

my_local_dir = '<directory where you want the data to be downloaded and unpacked>'

tempset.get_package_data(my_local_dir)
```

Then you can run the following function to build the `summary.csv` file:

```python
gz_dir = '<directory where you downloaded and unpacked the EnergyPlus data to>'
summary_file = '<full path and filename to summary CSV file that you will write>'

tempset.aggregate_data(gz_dir=gz_dir, summary_file=summary_file)
```

3. **`gen_results()`**: analyzing and plotting probability distributions based on EnergyPlus (E+) simulations using
temperature setpoint schedules specified in (i):

```python
import tempset

summary_file = tempset.get_example_summary_file()
param_file = tempset.get_example_htgsetp_params_file()
case_study = 'I'  # just means input in this case
fig_dir = '<your desired figure directory>'
fig_ext = '.svg'
output_dir = "<your desired output directory>"

tempset.analyze_results(summary_file=summary_file,
                        param_file=param_file,
                        case_study=case_study,
                        fig_dir=fig_dir,
                        fig_ext=fig_ext,
                        out_dir=output_dir)
```

### `batch_process_idf`: Expected arguments

| Argument | Type | Description |
|----|----|----|
| `eplus_config` | str | Full path to configuration JSON file with file name and extension. The user needs to specify the IDD file corresponding to the IDF. An example that comes with the package can be obtained using the function `get_example_eplus_file()`, (`eplus_file = get_example_eplus_file()`) |
| `param_json` | str| Full path with file name and extension to the JSON file where the parameters associated with the heating or cooling setpoint are specified. Examples of `param_json` for heating and cooling setpoint can be obtained using the functions `get_example_htgsetp_file()` and `get_example_clgsetp_file()`.
| `batch_param` | str | Full path with file name and extension to the JSON file where the parameters associated with getting a batch of setpoint schedules. `max_iter` indicates the number of samples to generate, and `n_jobs` indicate the number of jobs to run in parallel (recommended `n_jobs=1` for now). Example of `batch_param` can be obtained using the function  `get_example_batch_file()`|
| `htgsetpoint_params_csv_output` | str | Full path with fie name and extension where the output CSV keeping track of the schedule parameters are going to be stored. One example of this CSV can be obtained by calling the function `get_example_htgsetp_params_file()` |
| `output_dir` | str | Full path to directory where the generated IDFs with stochastic schedules are going to be stored |
| `idf_file` | str | Full path with filename and extension to a single source IDF from which new IDFs are to be generated. The following examples can be obtained using the packagev: (i) electric resistance heating -> `get_example_electric_idf_file()` (ii) gas furnace heating -> `get_example_gas_idf_file()` (iii) heat pump  `get_example_main_idf_file()`|
| `write_logfile` | bool | Optional, choose to write log as file. |


#### `param_json`: Expected keys

The user inputs to define parameters for generating stochastic schedules need to be provided in a JSON file. 


| Key | Type | Description |
|----|----|----|
| `schedule_name` | str | Name of base schedule in source IDF  |
| `schedule_type` | str| Type of schedule. Must be HTGSETP (for heating setpoint) or CLGSETP (cooling setpoint)|
| `days in week` | list | Days in week for which schedules need to be changed. |
| `t_pthresh` | int | Threshold duration in hours for pre-heating or pre-cooling of generated schedules [(t_p,thres) in paper]|
| `max_ramphour` | int | Threshold duration in hours for morning rampup. (t_{ramp,thresh} in paper)|
| `rampRes` | int | time interval in minutes over which temperatures are incremented. Suggested: 15 mins. |
| `gamma_thresh` | float | Threshold morning ramp-up rate, in C/min for morning rampup. |
| `htgsSETP_op`| dict | Temperature parameters when heating is in "operation", i.e. when the daily temperature is at the maximum value during 24 hours. Keys "min", "max" and "mean" temperatures correspond to minimum, maximum  and mean temperratures from which the operative temperature T_{op} will be generated. Only valid when `schedule_type == HTGSETP`|
| `htgSETP_setbacl`| dict | Temperature parameters when heating is in "setback", i.e. when the daily temperature is at the maximum value during 24 hours. Only valid when `schedule_type == HTGSETP`|
| `clgSETP_op`| dict | Similar to `htgSETP_op`, but for cooling setpoints. Only valid when `schedule_type == CLGSETP`|
| `clgSETP_setback`| dict | Similar to `htgSETP_setback`, but for cooling setpoints. Only valid when `schedule_type == CLGSETP`|
| `p_tp`| float | Confidence interval assocated with `t_pthresh`. For instance, a value of 0.01 corresponds to 99% of generated scheduules having t_p <= t_{p,thresh}|
| `p_threshRamp`| float | Confidence interval assocated with `max_ramohour`|
| `setback_p`| float | Probability with which a given schedule will have a setback. |
| `plot_base_schedule`| bool | Bool indicating whether to plot the base (i.e. source) schedule |
| `plot_mod_schedule`| bool | Bool indicating whether to plot the stochastically-generated schedule. Use it for troubleshooting when running `schedules.py` as standalone|

#### `batch_process_idf`: Expected Outputs

IDFs generated in `output_dir`. The number of IDFs will be equal to `max_iter`. Each IDF will contain a different
stochastic sample of `HTGSETP` or `CLGSETP`.


### `aggregate_data`: Expected arguments

| Argument | Type | Description |
|----|----|----|
| `gz_dir` | str | Full path to the directory where the outputs from e+ simulations (using the IDFs generated from `batch_process_idf`) are located. `gz_dir` must contain outputs in `.csv.gz` |
| `summary_file` | str| Full path and filename ending in `.csv` where the aggregated results are written.


### `aggregate_data`: Expected Output

A summary file with file path and name specified in the argument `summary_file`.


### `analyze_results`: Expected arguments

See examples below for how to pass into the `Model` class

| Argument | Type | Description |
|----|----|----|
| `summary_file` | str | Full path to CSV file with file name and extension. This file contains the total daily weekday electricity consumption, maximum hourly consumption per day and mean PPD during occupied hours for all simulations (corresponding to IDFs generated using batch_process_idf, as generated by `aggregate_data`). Example of a summary file can be obtained by calling the function `get_example_summary_file()` |
| `param_file` | str| Full path with file name and extension to the CSV file containing the parameters associated with each stochastic schedule generated in `batch_process_idf`. Example of this CSV can be obtained by calling the function `get_example_htgsetp_params_file()`|
| `case_study` | str | Case study being performed. See paper for more details on each case study. Valid entries are `I`, `IIA`, `IIB` and `III`. Default: `I`.|
| `fig_dir` | str | Full path to directory where generated figures of probability distributions will be saved. Default: `figures/prob_dist/` |
| `fig_ext` | str | Extension indicating format in which generated figures are going to be saved. Recommended: `.svg` or `.eps`.|
| `output_dir` | str | Full path to directory where the generated IDFs with stochastic schedules are going to be stored |
| `out_dir` | str | Full path with output directory where log file is to be saved (if `write_logfile` is True). |
| `write_logfile` | bool | Optional, choose to write log as file. |

#### `analyze_results`: Expected Outputs

Figures of three probability distributions for each month in year stored in `fig_dir`. The three distributions
correspond to our three output metrics: total daily electricity consumption, maximum hourly consumption computed per day
and mean PPD during occupied hours.
