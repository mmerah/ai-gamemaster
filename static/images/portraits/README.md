# Character Portraits

This directory contains character portrait images for the D&D Game Master application.

## Adding Character Portraits

To add a portrait for a character:

1. **Image Requirements:**
   - Format: JPG, PNG, or GIF
   - Recommended size: 200x200 pixels or larger (square aspect ratio works best)
   - File size: Keep under 500KB for good performance

2. **Naming Convention:**
   - Use the character's ID as the filename
   - Example: `char_001.jpg`, `char_002.png`
   - The character ID can be found in the party panel tooltip or browser developer tools

3. **Fallback System:**
   - If no portrait image is found, the system will display the character's initials
   - Initials are automatically generated from the character's name

## Default Placeholders

Currently, the system uses a beautiful initials-based placeholder system with:
- Character initials in a golden circular badge
- Color-coded borders matching the fantasy theme
- Hover effects and smooth transitions

## Future Enhancements

- Support for different image formats
- Automatic image resizing and optimization
- Character portrait management interface
- Integration with character creation/editing

## Example Portrait Files

```
static/images/portraits/
├── char_001.jpg    # Portrait for character ID "char_001"
├── char_002.png    # Portrait for character ID "char_002"
├── wizard_001.jpg  # Portrait for character ID "wizard_001"
└── README.md       # This file
```
