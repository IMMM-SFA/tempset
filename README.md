# tempset
BEND temperature set point SA study

## Getting Started Using the `im3py` Package
The `im3py` package uses only **Python 3.6** and up.

### Step 1:
You can install `im3py` by running the following from your cloned directory (NOTE: ensure that you are using the desired `pip` instance that matches your Python3 distribution):

`pip3 install git+https://github.com/IMMM-SFA/im3py.git --user`

### Step 2:
Confirm that the module and its dependencies have been installed by running from your prompt:

```python
from im3py import Model
```

If no error is returned then you are ready to go!

## Setting up a run

### Expected arguments
See examples below for how to pass into the `Model` class

| Argument | Type | Description |
|----|----|----|
| `config_file` | str | Full path to configuration YAML file with file name and extension. If not provided by the user, the code will default to the expectation of alternate arguments. |
| `output_directory` | string | Full path with file name and extension to the output directory where outputs and the log file will be written. |
| `start_step` | int | Start time step value. |
| `through_step` | int | Through time step value. |
| `time_step` | int | Number of steps (e.g. number of years or minutes between projections) |
| `alpha_param` | float | Alpha parameter for model.  Acceptable range:  -2.0 to 2.0 |
| `beta_param` | float | Beta parameter for model.  Acceptable range:  -2.0 to 2.0 |
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
