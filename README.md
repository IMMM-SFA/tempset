# tempset
BEND temperature set point SA study

## Getting Started Using the `im3py` Package
The `tempset` package has been verified for **Python 3.7** and up.

### Step 1:
You can install `tempset` by running the following from your cloned directory (NOTE: ensure that you are using the desired `pip` instance that matches your Python3 distribution):

`pip3 install git+https://https://github.com/IMMM-SFA/tempset --user`

### Step 2:
Confirm that the module and its dependencies have been installed by running from your prompt:

```python
from tempset import batch_process_idf
from tempset import analyze_results
```

If no error is returned then you are ready to go!

## Functionalities
There are two functionalities provided in this repo: (i) **batch_process_idf**: generating a distribution of temperature setpont schedules, with each schedule written to a separate IDF and (ii) **gen_results**: analyzing and plotting probability distributions based on EnergyPlus (E+) simulations using temperature setpoint schedules specified in (i)


### `batch_process_idf`: Expected arguments
See examples below for how to pass into the `Model` class

| Argument | Type | Description |
|----|----|----|
| `eplus_config` | str | Full path to configuration JSON file with file name and extension. The user needs to specify the IDD file corresponding to the IDF. Default: `data/eplus/Energy+.idd` |
| `param_json` | str| Full path with file name and extension to the JSON file where the parameters associated with the heating or cooling setpoint are specified. Details on this later in the manual. Example: `/json/htgsetp_params.json`.
| `batch_param` | str | Full path with file name and extension to the JSON file where the parameters associated with getting a batch of setpoint schedules. |
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
| `max_ramphour` | int | Maximum duration in hours for ramping. |
| `rampRes` | int | time interval in minutes over which temperatures are incremented. Suggested: 15 mins. |
| `gamma_thresh` | float | Threshold morning ramp-up rate, in C/min for morning rampup. |
| `htgsSETP_op`| dict | Temperature parameters when heating is in "operation", i.e. when the daily temperature is at the maximum value during 24 hours. Keys "min", "max" and "mean" temperatures correspond to minimum, maximum  and mean temperratures from which the operative temperature T_{op} will be generated. Only valid when `schedule_type == HTGSETP`|
| `htgSETP_setbacl`| dict | Temperature parameters when heating is in "setback", i.e. when the daily temperature is at the maximum value during 24 hours. Only valid when `schedule_type == HTGSETP`|
| `clgSETP_op`| dict | Similar to `htgSETP_op`, but for cooling setpoints. Only valid when `schedule_type == CLGSETP`|
| `clgSETP_setback`| dict | Similar to `htgSETP_setback`, but for cooling setpoints. Only valid when `schedule_type == CLGSETP`|
| `p_threshSetback`| float | Similar to `htgSETP_setback`, but for cooling setpoints. Only valid when `schedule_type == CLGSETP`|

### Variable arguments
Users can update variable argument values after model initialization; this includes updating values between time steps (see **Example 3**).  The following are variable arguments:
- `alpha_param`
- `beta_param`

### YAML configuration file option (e.g., config.yml)
Arguments can be passed into the `Model` class using a YAML configuration file as well (see **Example 1**):

```yaml
# Example configuration file setup
output_directory:  "<Full path to the output directory>"
start_step: 2015
through_step: 2016
time_step: 1
alpha_param: 2.0
beta_param: 1.42
write_logfile: False
```

### Expected outputs
Each time-step processed will generate a TEXT file containing a solution message and have the file name formatted as `output_year_<YYYY>.txt`. These will be written to where the `output_directory` has been assigned.

## Examples

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
