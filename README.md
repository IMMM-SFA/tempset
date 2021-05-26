# tempset
BEND temperature set point SA study

## Getting Started Using the `tempset` Package
The `tempset` package has been verified for **Python 3.7** and up.

### Step 1:
You can install `tempset` by running the following from your cloned directory (NOTE: ensure that you are using the desired `pip` instance that matches your Python3 distribution):

`pip3 install git+https://github.com/IMMM-SFA/tempset --user`

### Step 2:
Confirm that the module and its dependencies have been installed by running from your prompt:

```python
from tempset import batch_process_idf
from tempset import analyze_results
```

If no error is returned then you are ready to go!

## Functionalities
There are two functionalities provided in this repo: (i) **batch_process_idf**: generating a distribution of temperature setpont schedules, with each schedule written to a separate IDF and (ii) **gen_results**: analyzing and plotting probability distributions based on EnergyPlus (E+) simulations using temperature setpoint schedules specified in (i). `test.py` shows examples of how these functions can be used.


### `batch_process_idf`: Expected arguments
See examples below for how to pass into the `Model` class

| Argument | Type | Description |
|----|----|----|
| `eplus_config` | str | Full path to configuration JSON file with file name and extension. The user needs to specify the IDD file corresponding to the IDF. Default: `data/eplus/Energy+.idd` |
| `param_json` | str| Full path with file name and extension to the JSON file where the parameters associated with the heating or cooling setpoint are specified. Details on this later in the manual. Example: `/json/htgsetp_params.json`.
| `batch_param` | str | Full path with file name and extension to the JSON file where the parameters associated with getting a batch of setpoint schedules. `max_iter` indicates the number of samples to generate, and `n_jobs` indicate the number of jobs to run in parallel (recommended `n_jobs=1` for now).|
| `htgsetpoint_params_csv_output` | str | Full path with fie name and extension where the output CSV keeping track of the schedule parameters are going to be stored. Default set to None. |
| `output_dir` | str | Full path to directory where the generated IDFs with stochastic schedules are going to be stored |
| `idf_file` | str | Full path with filename and extension to a single source IDF from which new IDFs are to be generated. Default: `data\idf\gas.idf`. |
| `write_logfile` | bool | Optional, choose to write log as file. |



#### `param_json`: Expected keys

The user inputs to define parameters for generating stochastic schedules need to be provided in a JSON file. For examples, see `./json/htgsetp_params.json` and `./json/clgsetp_params.json`. Also check tables 1 and 2 in paper for more information.

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

IDFs generated in `output_dir`. The number of IDFs will be equal to `max_iter`. Each IDF will contain a different stochastic sample of `HTGSETP` or `CLGSETP`.

### `analyze_results`: Expected arguments
See examples below for how to pass into the `Model` class

| Argument | Type | Description |
|----|----|----|
| `summary_file` | str | Full path to CSV file with file name and extension. This file contains the total daily weekday electricity consumption, maximum hourly consumption per day and mean PPD during occupied hours for all simulations (corresponding to IDFs generated using batch_process_idf). A sample summary file is provided in `data/electric/summary.csv` |
| `param_file` | str| Full path with file name and extension to the CSV file containing the parameters associated with each stochastic schedule generated in `batch_process_idf`. Default: `data/electric/htgsetp_params_electric.csv`.|
| `case_study` | str | Case study being performed. See paper for more details on each case study. Valid entries are `I`, `IIA`, `IIB` and `III`. Default: `I`.|
| `fig_dir` | str | Full path to directory where generated figures of probability distributions will be saved. Default: `figures/prob_dist/` |
| `fig_ext` | str | Extension indicating format in which generated figures are going to be saved. Recommended: `.svg` or `.eps`.|
| `output_dir` | str | Full path to directory where the generated IDFs with stochastic schedules are going to be stored |
| `out_dir` | str | Full path with output directory where log file is to be saved (if `write_logfile` is True). |
| `write_logfile` | bool | Optional, choose to write log as file. |

<!-- ### Variable arguments
Users can update variable argument values after model initialization; this includes updating values between time steps (see **Example 3**).  The following are variable arguments:
- `alpha_param`
- `beta_param` -->

#### `analyze_results`: Expected Outputs
Figures of three probability distributions for each month in year stored in `fig_dir`. The three distributions correspond to our three output metrics: total daily electricity consumption, maximum hourly consumption computed per day and mean PPD during occupied hours. 

## Examples

See `test.py` for examples of both of these functions.

<!-- 
### Example 1:  Run `im3py` for all years using a configuration file
```python
from im3py.model import Model

run = Model(config_file="<path to your config file with the file name and extension.")

run.run_all_steps()
```

### Example 2:  Run `im3py` for all years by passing argument values
```python
from im3py.model import Model

run = Model(output_directory="<output directory path>",
            start_step=2015,
            through_step=2016,
            time_step=1,
            alpha_param=2.0,
            beta_param=1.42,
            write_logfile=False)

run.run_all_steps()
```
 -->
