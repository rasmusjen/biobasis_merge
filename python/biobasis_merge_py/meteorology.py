"""Meteorological calculations for WBGT and related parameters."""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def calculate_saturated_vapor_pressure(T):
    """
    Calculate saturated vapor pressure over water using Campbell Scientific equation.
    
    Args:
        T: Air temperature (dry-bulb or ambient air temperature) in °C
    
    Returns:
        esat: Saturated vapor pressure in kPa
    """
    # Coefficients from Campbell Scientific manual
    A0 = 6.107799961
    A1 = 4.436518521E-1
    A2 = 1.428945805E-2
    A3 = 2.650648471E-4
    A4 = 3.031240396E-6
    A5 = 2.034080948E-8
    A6 = 6.136820929E-11
    
    esat = (A0 + A1*T + A2*T**2 + A3*T**3 + A4*T**4 + A5*T**5 + A6*T**6) * 0.1
    
    return esat


def calculate_vapor_pressure(RH, esat):
    """
    Calculate vapor pressure.
    
    Args:
        RH: Relative humidity in %
        esat: Saturated vapor pressure in kPa
    
    Returns:
        ea: Vapor pressure in kPa
    """
    ea = RH * esat / 100
    return ea


def calculate_dewpoint(ea):
    """
    Calculate dewpoint temperature using Teten's equation.
    
    Args:
        ea: Vapor pressure in kPa
    
    Returns:
        Td: Dewpoint temperature in °C
    """
    # Handle edge cases
    if pd.isna(ea) or ea <= 0:
        return np.nan
    
    # Teten's equation (inverse)
    ln_ea = np.log(ea / 0.61078)
    Td = (241.88 * ln_ea) / (17.558 - ln_ea)
    
    return Td


def calculate_wet_bulb_vapor_pressure(T, Tw, SP):
    """
    Calculate vapor pressure at wet-bulb temperature.
    
    Args:
        T: Air temperature (dry-bulb) in °C
        Tw: Wet-bulb temperature in °C
        SP: Standard air pressure in kPa
    
    Returns:
        ewt: Wet-bulb temperature vapor pressure in kPa
    """
    # Calculate saturated vapor pressure at wet-bulb temperature
    eswt = calculate_saturated_vapor_pressure(Tw)
    
    # Campbell Scientific equation
    ewt = eswt - (0.000660 * (1 + 0.00115 * Tw) * (T - Tw) * SP)
    
    return ewt


def calculate_wet_bulb_temperature(T, ea, SP, max_iterations=50, tolerance=0.01):
    """
    Calculate wet-bulb temperature using iterative process.
    
    Args:
        T: Air temperature (dry-bulb) in °C
        ea: Vapor pressure in kPa
        SP: Standard air pressure in kPa
        max_iterations: Maximum number of iterations
        tolerance: Convergence tolerance in °C
    
    Returns:
        Tw: Wet-bulb temperature in °C
    """
    # Handle edge cases
    if pd.isna(T) or pd.isna(ea) or pd.isna(SP):
        return np.nan
    
    # Calculate dewpoint as initial guess
    Td = calculate_dewpoint(ea)
    if pd.isna(Td):
        return np.nan
    
    # Initial guess for wet-bulb temperature
    Tw = Td
    
    for i in range(max_iterations):
        # Calculate vapor pressure at current wet-bulb temperature
        ewt = calculate_wet_bulb_vapor_pressure(T, Tw, SP)
        
        # Calculate difference from actual vapor pressure
        diff = ewt - ea
        
        # Adjust wet-bulb temperature estimate
        # Simple gradient descent approach
        Tw_new = Tw - diff * 0.5  # Adjustment factor
        
        # Check for convergence
        if abs(Tw_new - Tw) < tolerance:
            return Tw_new
        
        Tw = Tw_new
        
        # Ensure wet-bulb temperature stays within reasonable bounds
        if Tw < Td - 5 or Tw > T + 5:
            break
    
    # If no convergence, return best estimate
    logger.debug(f"Wet-bulb calculation did not converge for T={T}, ea={ea}, SP={SP}")
    return Tw


def calculate_wbgt(black_globe_temp, wet_bulb_temp, dry_bulb_temp):
    """
    Calculate Wet-bulb Globe Temperature (WBGT) index.
    
    Args:
        black_globe_temp: Black globe temperature in °C
        wet_bulb_temp: Wet-bulb temperature in °C
        dry_bulb_temp: Dry-bulb (air) temperature in °C
    
    Returns:
        WBGT: Wet-bulb Globe Temperature index in °C
    """
    # Handle edge cases
    if pd.isna(black_globe_temp) or pd.isna(wet_bulb_temp) or pd.isna(dry_bulb_temp):
        return np.nan
    
    # Campbell Scientific equation
    WBGT = (0.2 * black_globe_temp) + (0.7 * wet_bulb_temp) + (0.1 * dry_bulb_temp)
    
    return WBGT


def add_meteorological_calculations(df):
    """
    Add meteorological calculations to the dataframe.
    
    Args:
        df: DataFrame with meteorological data
    
    Returns:
        df: DataFrame with added meteorological parameters
    """
    logger.info("Calculating meteorological parameters (esat, ea, dewpoint, wet-bulb, WBGT)")
    
    # Create copies for calculations
    df = df.copy()
    
    # Extract required columns
    T = df['AirTC_Avg']  # Air temperature (°C)
    RH = df['RH_Avg']    # Relative humidity (%)
    P = df['P_Air_Avg']  # Air pressure (mbar)
    BG = df['BGTemp_C_Avg']  # Black globe temperature (°C)
    
    # Convert pressure from mbar to kPa
    SP = P * 0.1
    
    # Calculate saturated vapor pressure
    df['esat_kPa'] = calculate_saturated_vapor_pressure(T)
    
    # Calculate vapor pressure
    df['ea_kPa'] = calculate_vapor_pressure(RH, df['esat_kPa'])
    
    # Calculate dewpoint
    df['dewpoint_C'] = df['ea_kPa'].apply(calculate_dewpoint)
    
    # Calculate wet-bulb temperature (vectorized)
    logger.info("Calculating wet-bulb temperatures (this may take a moment)...")
    df['wet_bulb_C'] = df.apply(
        lambda row: calculate_wet_bulb_temperature(
            row['AirTC_Avg'], row['ea_kPa'], SP.loc[row.name] if row.name in SP.index else np.nan
        ), axis=1
    )
    
    # Calculate WBGT
    df['WBGT_C'] = df.apply(
        lambda row: calculate_wbgt(
            row['BGTemp_C_Avg'], row['wet_bulb_C'], row['AirTC_Avg']
        ), axis=1
    )
    
    # Count successful calculations
    count_esat = df['esat_kPa'].count()
    count_ea = df['ea_kPa'].count()
    count_dewpoint = df['dewpoint_C'].count()
    count_wet_bulb = df['wet_bulb_C'].count()
    count_wbgt = df['WBGT_C'].count()
    
    logger.info(f"Meteorological calculations completed:")
    logger.info(f"  - Saturated vapor pressure: {count_esat} values")
    logger.info(f"  - Vapor pressure: {count_ea} values")
    logger.info(f"  - Dewpoint: {count_dewpoint} values")
    logger.info(f"  - Wet-bulb temperature: {count_wet_bulb} values")
    logger.info(f"  - WBGT: {count_wbgt} values")
    
    return df
