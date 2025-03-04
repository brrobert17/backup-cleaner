# Backup Cleaner

A Python application with a GUI to help manage and clean up backup files by comparing files between origin and target folders.

## Features

- **User-Friendly Interface**: Easy-to-use interface with intuitive controls
- **Folder Comparison**: Compare files between origin and target folders
- **Intelligent File Matching**: 
  - Find files with the same name or with " - Copy" variations
  - Handle cases when one file has multiple potential matches
- **Multiple Matching Methods**: 
  - Name matching
  - Size matching (highlighted in blue)
  - Content matching via SHA-256 checksums (highlighted in green)
- **Flexible Search Options**: Optionally search for matches in different locations
- **Smart Actions**: 
  - Move unmatched files to the target folder (with folder structure preservation)
  - Copy size-matched files with "_v2" suffix to preserve both versions
  - Delete duplicate files that are exact matches (same content via checksum verification)
- **Directory Cleanup**: Automatically remove empty directories in the origin folder after actions
- **Selection Controls**: Select/deselect files to process with checkboxes

## Requirements

- Python 3.6 or higher
- tkinter (usually comes with Python installation)

## Usage

1. Run the application:
   ```
   python backup_cleaner.py
   ```

2. Select the origin folder (containing files you want to manage)
3. Select the target folder (where files should be compared against or moved to)
4. Choose whether to search for matches in different locations 
5. Click "Compare Folders" to analyze the files
6. Review the results:
   - Green: Exact content match (proposed action: delete from origin)
   - Blue: Same size but different content (proposed action: copy as "_v2")
   - Normal: Name match only or no match
7. Modify selections by clicking on checkboxes as needed
8. Click "Execute Actions" to perform the proposed operations

## How It Works

- Files in the origin folder are compared to files in the target folder.
- For each file in the origin folder, the program searches for matching files in the target folder.
- Matching criteria include:
  - Exact filename
  - Filename with " - Copy" added or removed
  - Optional: Searching in different locations within the target folder
- When a file has multiple potential matches, the best match is selected based on match quality:
  - Exact match (same content) is prioritized
  - Size match is next in priority
  - Name match is lowest priority
  - Alternative matches are listed with "Skip" action by default
- Files are compared by size, and if sizes match, by SHA-256 checksum.
- Default actions:
  - No match: Move to target folder
  - Name match only: Keep
  - Size match but different content: Copy to target with "_v2" suffix
  - Exact content match: Delete from origin
- After actions are executed, empty directories in the origin folder are automatically removed

## Safety Features

- Preview of all actions before execution
- Confirmation dialog before performing any operations
- No automatic deletion without user confirmation
