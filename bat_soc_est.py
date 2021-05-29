# ===============================================================================
# @file:    bat_soc_est.py
# @note:    Battery SOC estimation based on voltage
# @author:  Ziga Miklosic
# @date:    27.02.2021
# @brief:   This scripts read cell voltage measurement during CC disharge and
#           visualise it 
# ===============================================================================

# ===============================================================================
#       IMPORTS  
# ===============================================================================
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import csv
import argparse
import copy
import random

# ===============================================================================
#       CONSTANTS
# ===============================================================================

# SAMPLE TIME OF MEASUREMENT
# Unit: second
SAMPLE_TIME = 1.0

# DISCHARGE CURRENT
# Unit: ampers
DISCHARGE_CUR = 0.200

## NORMAL CURRENT CONSUMPTION
# Unit: ampers
NORMAL_CUR = 0.020

# Find points at certain voltage
# NOTE: In decending value as acquire by measurement
VOLT_POINT = [ 4.13, 3.66, 3.40, 3.25, 2.5 ]
VOLT_POINT_EPS = 0.005

# ===============================================================================
#       CLASSES
# ===============================================================================


# ===============================================================================
#       MAIN ENTRY
# ===============================================================================
if __name__ == "__main__":

    # Arg parser
    parser = argparse.ArgumentParser()

    # File to plot
    parser.add_argument("-f", "--file", help="File for analysis")

    # Get args
    args = parser.parse_args()

    # Convert namespace to dict
    args = vars(args)

    # Data files
    csv_file = 0
    
    # Signals
    _meas_time = []
    _cell_volt = []
    _cell_cur = []
    _cell_soc = []
    _cell_soc_per = []

    # Check for file
    if args["file"] != None:
		
        # Get file name
        _file = args["file"]

        # Print status
        print("Parsing... (%s)" % _file)

        # Open file for reading
        with open(_file, "r") as csvfile:
            
            # Read row
            spamreader = csv.reader(csvfile, delimiter=";")

            # ===================================================================
            # 	Walk thru file
            # ===================================================================
            for idx, row in enumerate(spamreader):

                if idx == 0:
                    _meas_time.append( SAMPLE_TIME )
                else:
                    _meas_time.append( _meas_time[-1] + SAMPLE_TIME )

                _cell_volt.append( float( row[0] ))

                if _meas_time[-1] > 65.0:
                    _cell_cur.append( DISCHARGE_CUR + NORMAL_CUR )
                else:
                    _cell_cur.append( NORMAL_CUR )

                if idx == 0:
                    _cell_soc.append( 0.0 )
                else:
                    soc = _cell_cur[-1] / 3600
                    _cell_soc.append( _cell_soc[-1] + soc )

    # End SOC value
    _total_soc = _cell_soc[-1]

    # SOC&voltage points for linear interpolation
    soc_point_idx = 0
    soc_point = []

    # Calculate SOC percentage
    for idx, soc in enumerate( _cell_soc ):
        _cell_soc_per.append(( _total_soc - soc ) / _total_soc )

        # Get cell voltage
        vol = _cell_volt[ idx ]

        if soc_point_idx < len( VOLT_POINT ):

            # Find SOC level at certain voltage point
            if      ( vol <= ( VOLT_POINT[ soc_point_idx ] + VOLT_POINT_EPS )) \
                and ( vol >= ( VOLT_POINT[ soc_point_idx ] - VOLT_POINT_EPS )):

                soc_point.append( _cell_soc_per[ -1 ] )
                soc_point_idx += 1

    # Linera coefficient and zero point
    soc_inter_k = []
    soc_inter_n = []
    for idx, soc_p in enumerate( soc_point ):
        if idx > 0:
            k = ( soc_point[idx - 1] - soc_point[idx] ) / ( VOLT_POINT[idx-1] - VOLT_POINT[idx] )
            n = soc_point[idx] - k * VOLT_POINT[idx]

            soc_inter_k.append(k)
            soc_inter_n.append(n)

    # Print coefficients
    print( "k: %s" % soc_inter_k )
    print( "n: %s" % soc_inter_n )

    # Linear interpolation curves
    soc_lin_est = []
    soc_point_idx = 0
    for idx, soc in enumerate( _cell_soc ):

        # Get voltage
        vol = _cell_volt[idx]

        # Sections of linear function
        if vol <= VOLT_POINT[soc_point_idx+1]:
            if soc_point_idx < len( VOLT_POINT )-2:
                soc_point_idx += 1

        # Linear function
        lin_est = soc_inter_k[soc_point_idx] * vol + soc_inter_n[soc_point_idx]
        #lin_est = 0

        soc_lin_est.append( lin_est )


    # =============================================================================================
    ## PLOT CONFIGURATIONS
    # =============================================================================================
    plt.style.use(['dark_background'])
    PLOT_MAIN_TITLE_SIZE    = 18
    PLOT_MAIN_TITLE         = "BATTERY SOC ESTIMATION\nfile: " + str(_file)
    PLOT_TITLE_SIZE         = 16
    PLOT_AXIS_LABEL_SIZE    = 12

    PLOT_ADJUST_LEFT        = 0.06
    PLOT_ADJUST_RIGHT       = 0.957
    PLOT_ADJUST_TOP         = 0.883
    PLOT_ADJUST_BOTTOM      = 0.064
    PLOT_ADJUST_WSPACE		= 0.171
    PLOT_ADJUST_HSPACE		= 0.24

    ## ================================================================================
    ## PLOT DATA
    ## ================================================================================
    fig, ax = plt.subplots(2, 1, sharex=False)

    fig.suptitle( PLOT_MAIN_TITLE , fontsize=PLOT_MAIN_TITLE_SIZE )

    # Plot 1
    ax[0].set_title("Cell voltage & current", fontsize=PLOT_TITLE_SIZE)
    ax[0].plot( _meas_time, _cell_volt, "r", label="voltage" )

    ax[0].grid(alpha=0.25)
    ax[0].set_ylabel("Voltage [V]")
    ax[0].set_xlabel("Time [sec]")

    ax_11 = ax[0].twinx()
    ax_11.plot( _meas_time, _cell_cur, "y", label="current" )
    ax_11.set_ylabel("Current [A]")

    ax[0].legend(loc="upper left")
    ax_11.legend(loc="upper right")
    ax_11.set_ylim(0,1)

    # Plot 2
    ax[1].set_title("Battery SOC", fontsize=PLOT_TITLE_SIZE)
    ax[1].plot( _cell_volt, _cell_soc, "g", label="SOC"  	)

    ax[1].grid(alpha=0.25)
    ax[1].set_ylabel("SOC [mAh]")
    ax[1].set_xlabel("Voltage [V]")

    ax_22 = ax[1].twinx()
    ax_22.plot( _cell_volt, _cell_soc_per, "r", label="current" )
    ax_22.plot( VOLT_POINT, soc_point, "yo", label="current" )
    ax_22.plot( _cell_volt, soc_lin_est, "y--", label="current" )
    ax_22.set_ylabel("Relative SOC[%]")

    plt.subplots_adjust(left=PLOT_ADJUST_LEFT, right=PLOT_ADJUST_RIGHT, top=PLOT_ADJUST_TOP, bottom=PLOT_ADJUST_BOTTOM, wspace=PLOT_ADJUST_WSPACE, hspace=PLOT_ADJUST_HSPACE)	
    plt.show()

# ===============================================================================
#       END OF FILE
# ===============================================================================
