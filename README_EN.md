# SpriteSheet Toolset

A Python toolset for SpriteSheet image processing, including intelligent splitting and realignment functions, with support for Chinese and English switching.

## Features

### Splitting Tool
- Automatically detects background color and sprite regions
- Supports manual drawing and adjustment of split regions
- Adjustable detection threshold to adapt to different images
- Supports zooming and panning for viewing
- Generates sequentially named image files
- Supports custom output directory
- Supports swapping sprite sequence numbers
- Chinese and English interface switching support

### Alignment Tool
- Import split small images as workspace
- Supports manual drag and drop position adjustment
- Supports grid display and center point marking
- Reference image function with semi-transparent display
- Supports auto-alignment functions (left align, right align, top align, bottom align, center align)
- Supports batch application of alignment settings
- Rich shortcut key support
- Supports zooming and panning for viewing
- Re-stitch processed sprites into a complete spritesheet
- Supports adjustment of rows, columns, and spacing
- Supports importing multiple directories, exporting with each group in one row
- Supports import/export offset settings
- Chinese and English interface switching support

## Installation Dependencies

Python 3

```bash
pip install -r requirements.txt
```

## Usage

### 1. SpriteSheet2Sprite

Run the graphical interface version with automatic sprite detection:

```bash
python SpriteSheet2Sprite.py
```

**Usage Steps:**
1. Click the "Select Image" button to choose the SpriteSheet image to split
2. Click the "Detect Sprites" button to automatically detect sprite regions in the image
3. Adjust the "Auto Detection Threshold" to optimize detection results
4. Manually add, delete, or adjust split regions if needed
5. Supports Ctrl+scroll wheel to zoom the image
6. Select an output directory, default is `output`
7. Click the "Start Splitting" button to begin splitting
8. A progress bar will be displayed during splitting, and a prompt window will appear upon completion

### 2. Sprite2SpriteSheet

Run the sprite alignment tool for manual or automatic alignment of split small images:

```bash
python Sprite2SpriteSheet.py
```

**Usage Steps:**
1. Click the "Import Split Images" button to select split small images (multiple selection supported)
2. Select the image to edit from the left list
3. In the workspace, you can:
   - Drag the image to adjust its position
   - Use the X/Y offset controls on the right for fine-tuning
   - Show/hide grid and center point markers
   - Set a reference image with semi-transparent display to assist alignment
   - Use auto-alignment functions for quick alignment
   - Batch apply alignment settings to all images
4. Set stitching parameters (columns, rows, spacing)
5. Click the "Stitch and Save Spritesheet" button to generate and save the complete spritesheet

**Shortcut Key Support:**
- F5: Apply auto-alignment to current image
- Ctrl+F5: Batch apply auto-alignment to all images
- Delete: Delete current image
- Ctrl+': Toggle grid display
- Ctrl+S: Stitch and save spritesheet
- Q/W/A/S/D: Image selection and up/down movement
- C: Toggle reference image display
- H: Toggle current image display
- Alt+W/A/S/D: Fine-tune X/Y offset

**Alignment Features:**
- Red crosshair and center point displayed in the center of the workspace
- Images are aligned by center point by default
- Supports drag and drop position adjustment
- Supports precise numerical offset adjustment
- Supports grid-assisted alignment
- Reference image with semi-transparent display for easy comparison
- Multiple auto-alignment options available

## Notes

1. Ensure Python 3 environment is installed
2. Supports common image formats: PNG, JPG, BMP, etc.
3. Output images are saved as PNG format by default
4. The splitting tool automatically detects sprite regions, no need to manually set split dimensions
5. The alignment tool supports batch operations to improve work efficiency
6. Using shortcut keys can complete operations faster
7. The reference image function can help you align sprites more accurately
