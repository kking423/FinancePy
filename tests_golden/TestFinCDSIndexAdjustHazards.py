###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

from FinTestCases import FinTestCases, globalTestCaseMode
from financepy.utils.global_types import SwapTypes
from financepy.utils.date import Date
from financepy.utils.day_count import DayCountTypes
from financepy.utils.frequency import FrequencyTypes
from financepy.products.credit.cds_curve import CDSCurve
from financepy.products.rates.ibor_single_curve import IborSingleCurve
from financepy.products.rates.ibor_swap import IborSwap
from financepy.products.credit.cds import CDS
from financepy.products.credit.cds_index_portfolio import CDSIndexPortfolio
from os.path import dirname, join

import sys
sys.path.append("..")


testCases = FinTestCases(__file__, globalTestCaseMode)

##########################################################################
# TO DO
##########################################################################


def build_Ibor_Curve(tradeDate):

    valuation_date = tradeDate.add_days(1)
    dcType = DayCountTypes.ACT_360

    depos = []
    fras = []
    swaps = []

    dcType = DayCountTypes.THIRTY_E_360_ISDA
    fixedFreq = FrequencyTypes.SEMI_ANNUAL
    settlement_date = valuation_date

    maturity_date = settlement_date.add_months(12)
    swap1 = IborSwap(
        settlement_date,
        maturity_date,
        SwapTypes.PAY,
        0.0502,
        fixedFreq,
        dcType)
    swaps.append(swap1)

    maturity_date = settlement_date.add_months(24)
    swap2 = IborSwap(
        settlement_date,
        maturity_date,
        SwapTypes.PAY,
        0.0502,
        fixedFreq,
        dcType)
    swaps.append(swap2)

    maturity_date = settlement_date.add_months(36)
    swap3 = IborSwap(
        settlement_date,
        maturity_date,
        SwapTypes.PAY,
        0.0501,
        fixedFreq,
        dcType)
    swaps.append(swap3)

    maturity_date = settlement_date.add_months(48)
    swap4 = IborSwap(
        settlement_date,
        maturity_date,
        SwapTypes.PAY,
        0.0502,
        fixedFreq,
        dcType)
    swaps.append(swap4)

    maturity_date = settlement_date.add_months(60)
    swap5 = IborSwap(
        settlement_date,
        maturity_date,
        SwapTypes.PAY,
        0.0501,
        fixedFreq,
        dcType)
    swaps.append(swap5)

    libor_curve = IborSingleCurve(valuation_date, depos, fras, swaps)

    return libor_curve

##########################################################################


def buildIssuerCurve(tradeDate, libor_curve):

    valuation_date = tradeDate.add_days(1)

    cdsMarketContracts = []

    cdsCoupon = 0.0048375
    maturity_date = Date(29, 6, 2010)
    cds = CDS(valuation_date, maturity_date, cdsCoupon)
    cdsMarketContracts.append(cds)

    recovery_rate = 0.40

    issuer_curve = CDSCurve(valuation_date,
                            cdsMarketContracts,
                            libor_curve,
                            recovery_rate)

    return issuer_curve

##########################################################################


def test_performCDSIndexHazardRateAdjustment():

    tradeDate = Date(1, 8, 2007)
    step_in_date = tradeDate.add_days(1)
    valuation_date = step_in_date

    libor_curve = build_Ibor_Curve(tradeDate)

    maturity3Y = tradeDate.next_cds_date(36)
    maturity5Y = tradeDate.next_cds_date(60)
    maturity7Y = tradeDate.next_cds_date(84)
    maturity10Y = tradeDate.next_cds_date(120)

    path = dirname(__file__)
    filename = "CDX_NA_IG_S7_SPREADS.csv"
    full_filename_path = join(path, "data", filename)
    f = open(full_filename_path, 'r')

    data = f.readlines()
    issuer_curves = []

    for row in data[1:]:

        splitRow = row.split(",")
        spd3Y = float(splitRow[1]) / 10000.0
        spd5Y = float(splitRow[2]) / 10000.0
        spd7Y = float(splitRow[3]) / 10000.0
        spd10Y = float(splitRow[4]) / 10000.0
        recovery_rate = float(splitRow[5])

        cds3Y = CDS(step_in_date, maturity3Y, spd3Y)
        cds5Y = CDS(step_in_date, maturity5Y, spd5Y)
        cds7Y = CDS(step_in_date, maturity7Y, spd7Y)
        cds10Y = CDS(step_in_date, maturity10Y, spd10Y)
        cds_contracts = [cds3Y, cds5Y, cds7Y, cds10Y]

        issuer_curve = CDSCurve(valuation_date,
                                cds_contracts,
                                libor_curve,
                                recovery_rate)

        issuer_curves.append(issuer_curve)

    ##########################################################################
    # Now determine the average spread of the index
    ##########################################################################

    cdsIndex = CDSIndexPortfolio()

    averageSpd3Y = cdsIndex.average_spread(valuation_date,
                                           step_in_date,
                                           maturity3Y,
                                           issuer_curves) * 10000.0

    averageSpd5Y = cdsIndex.average_spread(valuation_date,
                                           step_in_date,
                                           maturity5Y,
                                           issuer_curves) * 10000.0

    averageSpd7Y = cdsIndex.average_spread(valuation_date,
                                           step_in_date,
                                           maturity7Y,
                                           issuer_curves) * 10000.0

    averageSpd10Y = cdsIndex.average_spread(valuation_date,
                                            step_in_date,
                                            maturity10Y,
                                            issuer_curves) * 10000.0

    testCases.header("LABEL", "VALUE")
    testCases.print("AVERAGE SPD 3Y", averageSpd3Y)
    testCases.print("AVERAGE SPD 5Y", averageSpd5Y)
    testCases.print("AVERAGE SPD 7Y", averageSpd7Y)
    testCases.print("AVERAGE SPD 10Y", averageSpd10Y)
    testCases.banner(
        "===================================================================")

    ##########################################################################
    # Now determine the intrinsic spread of the index to the same maturity dates
    # As the single name CDS contracts
    ##########################################################################

    cdsIndex = CDSIndexPortfolio()

    intrinsicSpd3Y = cdsIndex.intrinsic_spread(valuation_date,
                                               step_in_date,
                                               maturity3Y,
                                               issuer_curves) * 10000.0

    intrinsicSpd5Y = cdsIndex.intrinsic_spread(valuation_date,
                                               step_in_date,
                                               maturity5Y,
                                               issuer_curves) * 10000.0

    intrinsicSpd7Y = cdsIndex.intrinsic_spread(valuation_date,
                                               step_in_date,
                                               maturity7Y,
                                               issuer_curves) * 10000.0

    intrinsicSpd10Y = cdsIndex.intrinsic_spread(valuation_date,
                                                step_in_date,
                                                maturity10Y,
                                                issuer_curves) * 10000.0

    ##########################################################################
    ##########################################################################

    testCases.header("LABEL", "VALUE")
    testCases.print("INTRINSIC SPD 3Y", intrinsicSpd3Y)
    testCases.print("INTRINSIC SPD 5Y", intrinsicSpd5Y)
    testCases.print("INTRINSIC SPD 7Y", intrinsicSpd7Y)
    testCases.print("INTRINSIC SPD 10Y", intrinsicSpd10Y)
    testCases.banner(
        "===================================================================")

    ##########################################################################
    ##########################################################################

    index_coupons = [0.002, 0.0037, 0.0050, 0.0063]
    indexUpfronts = [0.0, 0.0, 0.0, 0.0]

    indexMaturityDates = [Date(20, 12, 2009),
                          Date(20, 12, 2011),
                          Date(20, 12, 2013),
                          Date(20, 12, 2016)]

    indexRecoveryRate = 0.40

    tolerance = 1e-6

    import time
    start = time.time()

    indexPortfolio = CDSIndexPortfolio()
    adjustedIssuerCurves = indexPortfolio.hazard_rate_adjust_intrinsic(
        valuation_date,
        issuer_curves,
        index_coupons,
        indexUpfronts,
        indexMaturityDates,
        indexRecoveryRate,
        tolerance)

    end = time.time()
    testCases.header("TIME")
    testCases.print(end - start)

#    num_credits = len(issuer_curves)
#    testCases.print("#","MATURITY","CDS_UNADJ","CDS_ADJ")
#    for m in range(0,num_credits):
#        for cds in cds_contracts:
#            unadjustedSpread = cds.par_spread(valuation_date,issuer_curves[m])
#            adjustedSpread = cds.par_spread(valuation_date,adjustedIssuerCurves[m])
#            testCases.print(m,str(cds._maturity_date),"%10.3f"%(unadjustedSpread*10000),"%10.3f" %(adjustedSpread*10000))

    cdsIndex = CDSIndexPortfolio()

    intrinsicSpd3Y = cdsIndex.intrinsic_spread(valuation_date,
                                               step_in_date,
                                               indexMaturityDates[0],
                                               adjustedIssuerCurves) * 10000.0

    intrinsicSpd5Y = cdsIndex.intrinsic_spread(valuation_date,
                                               step_in_date,
                                               indexMaturityDates[1],
                                               adjustedIssuerCurves) * 10000.0

    intrinsicSpd7Y = cdsIndex.intrinsic_spread(valuation_date,
                                               step_in_date,
                                               indexMaturityDates[2],
                                               adjustedIssuerCurves) * 10000.0

    intrinsicSpd10Y = cdsIndex.intrinsic_spread(valuation_date,
                                                step_in_date,
                                                indexMaturityDates[3],
                                                adjustedIssuerCurves) * 10000.0

    # If the adjustment works then this should equal the index spreads
    testCases.header("LABEL", "VALUE")
    testCases.print("ADJUSTED INTRINSIC SPD 3Y", intrinsicSpd3Y)
    testCases.print("ADJUSTED INTRINSIC SPD 5Y", intrinsicSpd5Y)
    testCases.print("ADJUSTED INTRINSIC SPD 7Y", intrinsicSpd7Y)
    testCases.print("ADJUSTED INTRINSIC SPD 10Y", intrinsicSpd10Y)

###############################################################################


test_performCDSIndexHazardRateAdjustment()
testCases.compareTestCases()
