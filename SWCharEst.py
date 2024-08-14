#!/usr/bin/env python3
#-------------------------------------------------------------------------------------------------------------
# @file		SWCharEst.py
#
# @brief	class SWCharEst:
#		Estimate values for wilting point, field capacity,
#		saturated water content, and saturated hydraulic conductivity
#		from soil texture and organic matter.
#		Output units are, respectively,
#		volume fraction, volume fraction, volume fraction, cm/sec.
#		Uses the equations from Saxton & Rawls, 2006.
#		Spreadsheet available at:
#		http://hydrolab.arsusda.gov/soilwater/Index.htm
#
# @author	Thomas E. Hilinski <https://github.com/tehilinski>
# @copyright	Copyright 2020 Thomas E. Hilinski. All rights reserved.
#		This software library, including source code and documentation,
#		is licensed under the Apache License version 2.0.
#		See the file "LICENSE.md" for more information.
#-------------------------------------------------------------------------------------------------------------
# Usage:
#	exec(open("SWCharEst.py").read())       # load this file
#	swc = SWCharEst()
#	swc.Get( sandFraction, clayFraction, somPercent )
#
# Example - sand:
#   swc.Get( 0.85, 0.04, 2.08 )
#   {'WP': 0.039999, 'FC': 0.097846, 'thetaS': 0.454455, 'Ks': 0.003096}
#
# Example - silt loam:
#   swc.Get( 0.15, 0.18, 3.05 )
#   {'WP': 0.1286, 'FC': 0.33148, 'thetaS': 0.50503, 'Ks': 0.00043}
#-------------------------------------------------------------------------------------------------------------

import math

class SWCharEst:

    @staticmethod
    def Usage ():
        """ Displays the use of the class. """
        print( "\nUsage:\n  swc = SWCharEst()" )
        print( "  swc.Get( sandFraction, clayFraction, somPercent )" )
        print( "Arguments:" )
        print( "  sand-fraction = sand weight fraction (0-1)" )
        print( "  clay-fraction = clay weight fraction (0-1)" )
        print( "  SOM-percent   = soil organic matter (weight %)" )
        print( "Results:" )
        print( "  WP     = wilting point (volume %)" )
        print( "  FC     = field capacity (volume %)" )
        print( "  thetaS = saturated water content (volume %)" )
        print( "  Ks     = Saturated hydraulic conductivity (cm/sec)" )

    def Get ( self, sand, clay, ompc, DEBUG = False ):
        """ Calculates an estimate of WP, FC, thetaS, Ks from
            the soil texture and organic matter content.

        :param sand:	sand fraction (float: 0-1)
        :param clay:	clay fraction (float: 0-1)
        :param ompc:	organic matter wt % (float: 0-70)
        :return:	list of WP, FC, thetaS, Ks, or None if failed
        """

        om = min ( 70.0, ompc ) 				# upper limit OM%
        if ( not self.__CheckArgs(sand, clay, om) ):
            return None

        theta1500t = -0.024 * sand + 0.487 * clay + 0.006 * om \
                     + 0.005 * sand * om \
                     - 0.013 * clay * om \
                     + 0.068 * sand * clay \
                     + 0.031

        theta1500 = max( 0.01, 					# constrain
                         theta1500t + 0.14 * theta1500t - 0.02 )

        theta33t = -0.251 * sand + 0.195 * clay + 0.011 * om \
                   + 0.006 * sand * om \
                   - 0.027 * clay * om \
                   + 0.452 * sand * clay \
                   + 0.299

        theta33 = min(
                    0.80, 					# constrain
                    theta33t + 1.283 * theta33t * theta33t - 0.374 * theta33t - 0.015 )

        theta1500 = min( theta1500,
                         0.80 * theta33 ) 		# constrain

        thetaS33t = 0.278 * sand + 0.034 * clay + 0.022 * om \
                    - 0.018 * sand * om \
                    - 0.027 * clay * om \
                    - 0.584 * sand * clay \
                    + 0.078

        thetaS33 = thetaS33t + 0.636 * thetaS33t - 0.107

        thetaS = theta33 + thetaS33 - 0.097 * sand + 0.043

        B = 3.816713 / ( math.log(theta33) - math.log(theta1500) )

        lamda = 1.0 / B

        Ks = 1930.0 * math.pow( ( thetaS - theta33 ), (3.0 - lamda) ) / 36000.0

        if ( DEBUG ):
            NL = '\n'
            print( "sand, clay, om = ", sand, " ", clay, " ", om, NL,
                   "theta1500t     = ", theta1500t, NL,
                   "theta1500      = ", theta1500, NL,
                   "theta33t       = ", theta33t, NL,
                   "theta33        = ", theta33, NL,
                   "thetaS33t      = ", thetaS33t, NL,
                   "thetaS33       = ", thetaS33, NL,
                   "thetaS         = ", thetaS, NL,
                   "B              = ", B, NL,
                   "lamda          = ", lamda, NL,
                   "Ks             = ", Ks, NL )

        results = { "WP":     round( theta1500, 6 ),
                    "FC":     round( theta33, 6 ),
                    "thetaS": round( thetaS, 6 ),
                    "Ks":     round( Ks, 6 ) }
        return results


    def __CheckArgs ( self, sand, clay, ompc ):
        """ Checks that the input values within an acceptable range.

        :param sand:	sand fraction (float: 0-1)
        :param clay:	clay fraction (float: 0-1)
        :param ompc:	organic matter wt % (float: 0-70)
        :return:	boolean: True if values are acceptable,
                        or False if one or more are out of range.
        """
        ok = True
        if ( sand < 0.0 or sand > 1.0 ):
            ok = False
        if ( clay < 0.0 or clay > 1.0 ):
            ok = False
        if ( ompc < 0.0 or ompc > 70.0 ):
            ok = False
        if ( sand + clay > 1.0 ):
            ok = False
        return ok
