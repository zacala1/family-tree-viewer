# Family Tree Application - User Guide

## Getting Started

### First Launch

1. **Run the Application**
   - Double-click `FamilyTree.exe` (or run `python main.py`)
   - The application will start with an empty family tree

2. **Add Your First Person**
   - Click the "Add Member" button or press `Ctrl+N`
   - Fill in the person's details:
     - Name (required)
     - Gender
     - Birth date (year, month, day)
     - Birth place, occupation, etc.
   - Click "Save"

3. **Building Your Tree**
   - Select a person from the left panel
   - Click "Edit" or double-click the person card
   - Go to the "Relationships" tab
   - Add parents, spouses, or children

## Managing Family Members

### Adding Information

**Basic Information Tab:**
- Name, gender
- Birth date (can specify lunar calendar)
- Death date (if applicable)

**Additional Information Tab:**
- Birth place
- Current address
- Occupation
- Education
- Phone number
- Email address

**Notes Tab:**
- Free-form text notes about the person

**Relationships Tab:**
- Parents (father, mother)
- Spouse(s) - can have multiple
- Children

### Multiple Spouses

The application supports multiple marriages:

1. Add the first spouse using "Add Spouse"
2. Add marriage date and divorce date (if applicable)
3. The current spouse (most recent, not divorced) is highlighted in green
4. Divorced spouses are shown in gray with dashed lines in the tree view

### Distinguishing People with Same Name

When multiple people have the same name:
- Birth dates are shown in the person list
- Example: "김서준 (1985.03.15)" vs "김서준 (1990.07.20)"

## Viewing and Navigating

### Tree View

**Zoom Controls:**
- Zoom in: `Ctrl++` or click zoom in button
- Zoom out: `Ctrl+-` or click zoom out button
- Reset zoom: `Ctrl+0` or click reset button
- Mouse wheel also zooms in/out

**Pan/Move:**
- Click and drag on the canvas to move the view
- The view will smoothly scroll to the selected person

**Visual Elements:**
- **Blue cards** = Male family members
- **Pink cards** = Female family members
- **Solid lines** = Parent-child relationships
- **Teal lines** = Spouse relationships
- **Dashed gray lines** = Divorced spouse relationships
- **Drop shadows** = Modern visual depth

### Selection and Highlighting

- Click any person to select them
- Selected person has a highlighted border
- Direct family members (parents, spouses, children) are also highlighted
- Details appear in the right panel

## Themes

### Dark Mode

Toggle between light and dark themes:
- Press `Ctrl+T`
- Or use View → Toggle Theme menu

**Dark Theme Features:**
- Catppuccin-inspired color palette
- Reduced eye strain in low light
- All UI elements adapt automatically

## File Operations

### Saving Your Work

**Save:**
- `Ctrl+S` or File → Save
- Saves to the current file location

**Save As:**
- `Ctrl+Shift+S` or File → Save As
- Choose a new location and format

**Auto-Save:**
- The application tracks unsaved changes
- You'll be prompted before closing if there are unsaved changes

### Loading Files

**Open:**
- `Ctrl+O` or File → Open
- Supports:
  - JSON files (.json) - native format
  - Excel files (.xlsx)
  - GEDCOM files (.ged)

**Import:**
- File → Import
- Imports additional family members from another file

**Export:**
- File → Export
- Export to Excel for viewing in spreadsheet applications

### File Formats

**JSON (Recommended):**
- Preserves all data including:
  - Person details
  - Relationships
  - Marriage/divorce dates
  - Notes
- Human-readable format
- Can be edited in a text editor

**Excel:**
- Good for:
  - Viewing in spreadsheet applications
  - Bulk editing data
  - Sharing with non-technical users
- Limitations:
  - Some relationship details may be simplified

**GEDCOM:**
- Import only
- Standard genealogy format
- Compatible with other family tree software

## Language Support

Switch between languages:
- View → Language → English or Korean
- All UI text updates immediately
- Person data is not affected (you can mix languages in names)

## Tips and Best Practices

### Data Entry

1. **Start with yourself or a common ancestor**
   - Build outward from there
   - Add immediate family first

2. **Use consistent date formats**
   - Full dates are most useful: YYYY.MM.DD
   - Partial dates are okay: just year, or year and month

3. **Add notes liberally**
   - Stories, facts, sources
   - Notes are searchable and preserve family history

4. **Verify relationships before adding**
   - Double-check parent-child connections
   - The app prevents circular relationships but can't validate accuracy

### Organization

1. **Regular backups**
   - Save copies of your file periodically
   - Consider using date-stamped filenames: `family_tree_2025_01_15.json`

2. **Use the search box**
   - Quickly find people by name
   - Especially useful for large family trees

3. **Keep spouse relationships updated**
   - Mark divorced spouses with divorce dates
   - This helps visualize the current family structure

### Performance

For large family trees (100+ people):
- The tree view may take a moment to calculate layout
- Use the search function instead of scrolling through the full list
- Consider splitting into multiple files (maternal/paternal sides)

## Keyboard Shortcuts Reference

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | Add new family member |
| `Ctrl+O` | Open file |
| `Ctrl+S` | Save |
| `Ctrl+Shift+S` | Save as |
| `Ctrl+T` | Toggle theme |
| `Ctrl++` | Zoom in |
| `Ctrl+-` | Zoom out |
| `Ctrl+0` | Reset zoom |
| `Delete` | Delete selected person |
| `Double Click` | Edit person details |

## Troubleshooting

### Common Issues

**"Name is required" error when saving:**
- Every person must have a name
- Enter at least a first name or identifier

**"Invalid email format" error:**
- Check the email address format
- Must be like: user@example.com
- Leave blank if unknown

**"Death date cannot be before birth date":**
- Check your date entries
- Common mistake: swapping month and day

**Can't see all the text in the side panel:**
- Drag the divider between panels to resize
- Maximum width is 600px for the left panel

**Tree view looks cramped:**
- Zoom out using `Ctrl+-`
- Drag the view to center on your area of interest
- Consider focusing on one branch at a time

## Getting Help

For issues not covered in this guide:

1. Check the main README.md file
2. Look at log files: `~/.familytree/logs/familytree.log`
3. Try the sample data: `data/sample.json`

## Privacy and Data Security

- All data is stored locally on your computer
- No internet connection required
- No data is sent to external servers
- Back up your files regularly to prevent data loss
