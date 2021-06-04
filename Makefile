# Dummy target...
nothing:
	@ echo "No action performed...(you must give an explicit makefile target)"

# add the tools/bin directry of the cloned repository into the execution path in order to restrict using script defined in tools/bin
# be sure not to switch out from the current directory in the process
#export PATH:=tools/bin:$(PATH)

# define energy plus versions
ENERGYPLUS_VERSION := 9.0

# directory definition
# ----------------------------------------------------------
DIR_HERE    	:= .
DIR_BIN		:= tools/bin
DIR_WEATHER	:= tools/epw
#DIR_INPUT	:= $(DIR_HERE)/created_idfs
DIR_INPUT	:=$(DIR_HERE)/prototype_elec
DIR_OUTPUT	:=$(DIR_HERE)/output


IDF_FILES    	:= $(notdir $(wildcard $(DIR_INPUT)/*.idf))	
OUT_FILES   	:= $(subst .idf,.table.csv.gz,$(IDF_FILES))
#OUT_FILES       := $(subst .table.csv.gzi,$(IDF_FILES))

# ADDIBNBBBG IN WEATHER
#WEATHER_FILE	:= USA_CO_Golden-NREL.724666_TMY3.epw
WEATHER_FILE	:= $(DIR_WEATHER)/USA_CO_Golden-NREL.724666_TMY3.epw
# ----------------------------------------------------------
# executible definition
# ----------------------------------------------------------
QWAIT		:= ${DIR_BIN}/qwait
#GPARM		:= ${DIR_BIN}/gparm
RUNEPLUS	:= ${DIR_BIN}/runeplus

# ----------------------------------------------------------
# executible parameter definition
# ----------------------------------------------------------
QWAIT_OPTS	:= -A im3 -t '8:00:00'	# Todd think even 20 min might be enough for any individual E+ run
NCPU		:= 20 # Applies only to the E+ runs...
#EPLUS_OPTS	:= -w $(DIR_WEATHER) -v $(ENERGYPLUS_VERSION) -z -r /tmp -l	# Version, gzip outputs, temp dir, logfile
EPLUS_OPTS	:= -w $(WEATHER_FILE) -v $(ENERGYPLUS_VERSION) -z -r /tmp -l
EPLUS_EXCLUDES	:= 'expidf,eio,mdd,mtd,rdd,bnd,GHTIn.idf,TXT,ssz.csv,zsz.csv'

# ----------------------------------------------------------
# Define the major steps and their associated targets/dependencies...
# ----------------------------------------------------------
# main simulation
#source /projects/bigsim/bin/localtools.csh


$(DIR_OUTPUT)/%.table.csv.gz: $(DIR_INPUT)/%.idf
	@$(QWAIT) $(QWAIT_OPTS) $(RUNEPLUS) $(EPLUS_OPTS) -x $(EPLUS_EXCLUDES) -i $(DIR_INPUT) -p $(DIR_OUTPUT) -o $* $*.idf $(WEATHER_FILE)

	  

# Convenience targets...
# TO-DO: do not have to define .PHONY any more.  Check most recent MAKE anyway.
.PHONY: out 
out: $(addprefix $(DIR_OUTPUT)/,$(OUT_FILES))



.PHONY: all
all:
	$(MAKE)    -j $(NCPU) out               # Do E+ runs
