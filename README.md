# Eevee Bake To Texture

A Blender addon that automates texture baking in Eevee by utilizing the texture paint projection workflow. This addon replicates Blender's "Edit Externally and Apply" texture paint method to project viewport renders onto a model's UV map.

## Features

- Automated texture baking using Eevee renderer
- Creates camera positions to capture all angles of the model
- Automatic UV mapping
- Multiple resolution presets for performance optimization
- Preview system to toggle between original shader and baked result
- Works with existing materials and shaders
- No complex setup required - one-click baking process

## Requirements

- Blender 3.6.5 or newer
- GPU with Eevee support
- Sufficient system memory for texture processing

## Installation

1. Download the Addon: https://github.com/27StudioAnimation/Texture-Paint-Baking---Blender-Addon/releases/tag/v1.1.0
2. Open Blender > Edit > Preferences > Add-ons
3. Click "Install" and select the downloaded zip file
4. Enable the addon by checking the box

## How It Works

The addon automates these steps:

1. Creates a Bake Camera that renders the model from multiple angles
2. Ensures proper UV mapping on the target object
3. Creates an empty bake texture
4. Renders each camera view using Eevee
5. Projects each render onto the model's UV map
6. Cleans up temporary render files
7. Sets up a shader network with the baked result

### The Baking Process

The baked result is accessible through a node setup in the shader editor:

- A UV Map node connected to
- An Image Texture node named "Bake_Texture"

## Usage

1. Select your object
2. Open the Eevee Bake panel in the N-panel
3. Choose resolution settings:
   - Fast: Fast but lower quality
   - Balanced: Balanced performance
   - High: Best quality but slower
4. Click "Bake"
5. Use "Toggle Preview" to switch between original and baked result
6. Uncheck Auto-Bake for manual | single_shot projections on the baked_texture

## Known Limitations

- **Performance**: During the baking process, Blender may become unresponsive. This is normal and varies based on:

  - Model complexity
  - Chosen resolution
  - Hardware specifications
  - Available system memory

- **Quality Factors**:
  - Best results on models with clean topology
  - Complex overlapping UVs may cause artifacts
  - Deep crevices might not bake accurately

## Tips for Best Results

1. Ensure proper UV unwrapping before baking
2. Start with lower resolutions for testing
3. Save your file before baking
4. Give Blender time to complete the process, even if it appears unresponsive

## Technical Notes

- The addon creates temporary renders during the baking process
- All temporary files are automatically cleaned up
- The baked texture is saved in your project's directory
- Camera positions are calculated based on model size and complexity

## Contributing

Found a bug or want to contribute? Please:

1. Create an issue describing the problem or enhancement
2. Fork the repository
3. Create a pull request with your changes

## License

This project is licensed under Apache License 2.0

---

**Important**: Due to the intensive nature of the baking process, it's recommended to save your work before starting a bake operation.
