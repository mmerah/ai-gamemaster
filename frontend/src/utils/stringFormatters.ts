/**
 * String formatting utilities
 */

/**
 * Capitalizes the first letter of each word in a string
 * @param str - The string to capitalize
 * @returns The capitalized string
 */
export function capitalizeWords(str: string | undefined | null): string {
  if (!str) return ''
  
  return str
    .split(/[\s-_]+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

/**
 * Formats a D&D term (race, class, background) for display
 * Handles special cases like "Half-Elf", "Dragonborn", etc.
 * @param term - The term to format
 * @returns The formatted term
 */
export function formatD5eTerm(term: string | undefined | null): string {
  if (!term) return ''
  
  // Special cases for D&D terms
  const specialCases: Record<string, string> = {
    'halfelf': 'Half-Elf',
    'half-elf': 'Half-Elf',
    'halforc': 'Half-Orc',
    'half-orc': 'Half-Orc',
    'highelf': 'High Elf',
    'high-elf': 'High Elf',
    'woodelf': 'Wood Elf',
    'wood-elf': 'Wood Elf',
    'darkelf': 'Dark Elf',
    'dark-elf': 'Dark Elf',
    'lightfoothalfling': 'Lightfoot Halfling',
    'lightfoot-halfling': 'Lightfoot Halfling',
    'stouthalfling': 'Stout Halfling',
    'stout-halfling': 'Stout Halfling',
    'mountaindwarf': 'Mountain Dwarf',
    'mountain-dwarf': 'Mountain Dwarf',
    'hilldwarf': 'Hill Dwarf',
    'hill-dwarf': 'Hill Dwarf',
    'rockgnome': 'Rock Gnome',
    'rock-gnome': 'Rock Gnome',
    'forestgnome': 'Forest Gnome',
    'forest-gnome': 'Forest Gnome'
  }
  
  const normalizedTerm = term.toLowerCase().replace(/[\s_]/g, '-')
  
  // Check for special cases first
  if (specialCases[normalizedTerm]) {
    return specialCases[normalizedTerm]
  }
  
  // Otherwise use general capitalization
  return capitalizeWords(term)
}