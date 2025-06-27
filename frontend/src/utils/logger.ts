/**
 * Simple logger utility for the frontend
 * In production, this could be replaced with a proper logging service
 */

const isDevelopment = import.meta.env.DEV

export const logger = {
  debug: (...args: unknown[]) => {
    if (isDevelopment) {
      console.log(...args)
    }
  },

  info: (...args: unknown[]) => {
    if (isDevelopment) {
      console.info(...args)
    }
  },

  warn: (...args: unknown[]) => {
    // Always log warnings
    console.warn(...args)
  },

  error: (...args: unknown[]) => {
    // Always log errors for debugging
    console.error(...args)
  },
}

export default logger
