# IN16bMantidreduction
Automatized Reduction Files for IN16b
======

The routines IN16bMantidreduction can be used to reduce data measured on IN16b in an automatized way. They treat full QENS as well as BATS spectra and also the FWS. The diffraction data are also reduced. 

Overview of the files:
----------------------------
-mantid-template-simple.py: main file to be run.

-QensLib.py: contains functions for "mantid-template-simple.py" 

-IN16B_Grouping_Si111.xml: necessary for calibration. Might be updated for new cycles.

-nxs_log.py: creates a table about the different runs performed in the experiment. Not to be changed.

-nxs_log.yml: contains information for nxs_log.py. Not to be changed.

Contact:
--------
christian.beck@uni-tuebingen.de
