# tempset
BEND temperature set point SA study

## Getting Started Using the `im3py` Package
The `tempset` package has been verified for **Python 3.7** and up.

### Step 1:
You can install `im3py` by running the following from your cloned directory (NOTE: ensure that you are using the desired `pip` instance that matches your Python3 distribution):

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


### batch_process_idf: Expected arguments
See examples below for how to pass into the `Model` class

| Argument | Type | Description |
|----|----|----|
| `eplus_config` | str | Full path to configuration JSON file with file name and extension. The user needs to specify the IDD file corresponding to the IDF. Default: `data/eplus/Energy+.idd` |
| `param_json` | str| Full path with file name and extension to the JSON file where the parameters associated with the heating or cooling setpoint are specified. Details on this later in the manual. Example: `/json/htgsetp_params.json`.
| `batch_param` | str | Full path with file name and extension to the JSON file where the parameters associated with getting a batch of setpoint schedules. |
| `htgsetpoint_params_csv_output` | str | Full path with fie name and extension where the output CSV keeping track of the schedule parameters are going to be stored. Default set to None. |
| `output_dir` | str | Full path to directory where the generated IDFs with stochastic schedules are going to be stored |
| `idf_file` | str | Full path with filename and extension to source IDFs from which new IDFs are to be generated. Default: `data\idf\gas.idf`. |
| `write_logfile` | bool | Optional, choose to write log as file. |

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
