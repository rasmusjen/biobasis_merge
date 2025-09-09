# Meteorological calculations for WBGT and related parameters

source("utils.R")

calculate_saturated_vapor_pressure <- function(T) {
  # Coefficients from Campbell Scientific manual
  A0 <- 6.107799961
  A1 <- 4.436518521E-1
  A2 <- 1.428945805E-2
  A3 <- 2.650648471E-4
  A4 <- 3.031240396E-6
  A5 <- 2.034080948E-8
  A6 <- 6.136820929E-11
  
  esat <- (A0 + A1*T + A2*T^2 + A3*T^3 + A4*T^4 + A5*T^5 + A6*T^6) * 0.1
  
  return(esat)
}

calculate_vapor_pressure <- function(RH, esat) {
  ea <- RH * esat / 100
  return(ea)
}

calculate_dewpoint <- function(ea) {
  # Handle edge cases
  if (is.na(ea) || ea <= 0) {
    return(NA)
  }
  
  # Teten's equation (inverse)
  ln_ea <- log(ea / 0.61078)
  Td <- (241.88 * ln_ea) / (17.558 - ln_ea)
  
  return(Td)
}

calculate_wet_bulb_vapor_pressure <- function(T, Tw, SP) {
  # Calculate saturated vapor pressure at wet-bulb temperature
  eswt <- calculate_saturated_vapor_pressure(Tw)
  
  # Campbell Scientific equation
  ewt <- eswt - (0.000660 * (1 + 0.00115 * Tw) * (T - Tw) * SP)
  
  return(ewt)
}

calculate_wet_bulb_temperature <- function(T, ea, SP, max_iterations = 50, tolerance = 0.01) {
  # Handle edge cases
  if (is.na(T) || is.na(ea) || is.na(SP)) {
    return(NA)
  }
  
  # Calculate dewpoint as initial guess
  Td <- calculate_dewpoint(ea)
  if (is.na(Td)) {
    return(NA)
  }
  
  # Initial guess for wet-bulb temperature
  Tw <- Td
  
  for (i in 1:max_iterations) {
    # Calculate vapor pressure at current wet-bulb temperature
    ewt <- calculate_wet_bulb_vapor_pressure(T, Tw, SP)
    
    # Calculate difference from actual vapor pressure
    diff <- ewt - ea
    
    # Adjust wet-bulb temperature estimate
    # Simple gradient descent approach
    Tw_new <- Tw - diff * 0.5  # Adjustment factor
    
    # Check for convergence
    if (abs(Tw_new - Tw) < tolerance) {
      return(Tw_new)
    }
    
    Tw <- Tw_new
    
    # Ensure wet-bulb temperature stays within reasonable bounds
    if (Tw < Td - 5 || Tw > T + 5) {
      break
    }
  }
  
  # If no convergence, return best estimate
  log_message("DEBUG", paste("Wet-bulb calculation did not converge for T=", T, "ea=", ea, "SP=", SP))
  return(Tw)
}

calculate_wbgt <- function(black_globe_temp, wet_bulb_temp, dry_bulb_temp) {
  # Handle edge cases
  if (is.na(black_globe_temp) || is.na(wet_bulb_temp) || is.na(dry_bulb_temp)) {
    return(NA)
  }
  
  # Campbell Scientific equation
  WBGT <- (0.2 * black_globe_temp) + (0.7 * wet_bulb_temp) + (0.1 * dry_bulb_temp)
  
  return(WBGT)
}

add_meteorological_calculations <- function(df) {
  log_message("INFO", "Calculating meteorological parameters (esat, ea, dewpoint, wet-bulb, WBGT)")
  
  # Extract required columns
  T <- df$AirTC_Avg      # Air temperature (°C)
  RH <- df$RH_Avg        # Relative humidity (%)
  P <- df$P_Air_Avg      # Air pressure (mbar)
  BG <- df$BGTemp_C_Avg  # Black globe temperature (°C)
  
  # Convert pressure from mbar to kPa
  SP <- P * 0.1
  
  # Calculate saturated vapor pressure
  df$esat_kPa <- calculate_saturated_vapor_pressure(T)
  
  # Calculate vapor pressure
  df$ea_kPa <- calculate_vapor_pressure(RH, df$esat_kPa)
  
  # Calculate dewpoint
  df$dewpoint_C <- sapply(df$ea_kPa, calculate_dewpoint)
  
  # Calculate wet-bulb temperature (vectorized)
  log_message("INFO", "Calculating wet-bulb temperatures (this may take a moment)...")
  df$wet_bulb_C <- mapply(calculate_wet_bulb_temperature, T, df$ea_kPa, SP)
  
  # Calculate WBGT
  df$WBGT_C <- mapply(calculate_wbgt, BG, df$wet_bulb_C, T)
  
  # Count successful calculations
  count_esat <- sum(!is.na(df$esat_kPa))
  count_ea <- sum(!is.na(df$ea_kPa))
  count_dewpoint <- sum(!is.na(df$dewpoint_C))
  count_wet_bulb <- sum(!is.na(df$wet_bulb_C))
  count_wbgt <- sum(!is.na(df$WBGT_C))
  
  log_message("INFO", "Meteorological calculations completed:")
  log_message("INFO", paste("  - Saturated vapor pressure:", count_esat, "values"))
  log_message("INFO", paste("  - Vapor pressure:", count_ea, "values"))
  log_message("INFO", paste("  - Dewpoint:", count_dewpoint, "values"))
  log_message("INFO", paste("  - Wet-bulb temperature:", count_wet_bulb, "values"))
  log_message("INFO", paste("  - WBGT:", count_wbgt, "values"))
  
  return(df)
}
