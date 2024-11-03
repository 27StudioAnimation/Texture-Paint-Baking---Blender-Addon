import bpy
from bpy.types import (PropertyGroup, AddonPreferences)
from bpy.props import (StringProperty, BoolProperty, IntProperty, FloatProperty, 
                      EnumProperty)

class EEVEEBakerProperties(PropertyGroup):
    quality_preset: EnumProperty(
        name="Quality Preset",
        description="Quality settings for baking",
        items=[
            ('FAST', "Fast", "Lower quality, faster baking"),
            ('BALANCED', "Balanced", "Medium quality and speed"),
            ('HIGH', "High", "High quality, slower baking")
        ],
        default='BALANCED'
        #type: ignore
    ) 
    show_bake: BoolProperty(
        name="Show Bake",
        description="Toggle between bake preview and original shader",
        default=False
        #type: ignore
    ) 
    force_new_uv: BoolProperty(
        name="Force New UV",
        description="Create a new UV map even if one exists",
        default=False
        #type: ignore
    ) 
    should_cancel: BoolProperty(
        name="Should Cancel",
        description="Flag to cancel the baking process",
        default=False
        #type: ignore
    ) 
    output_directory: StringProperty(
        name="Output Directory",
        description="Directory to save baked textures",
        default="//texture_projections",
        subtype='DIR_PATH'
        #type: ignore
    ) 
    
    file_name: StringProperty(
        name="File Name",
        description="Name for the baked texture",
        default="Bake_Texture"
        #type: ignore
    ) 
    
    auto_bake: BoolProperty(
        name="Auto Bake",
        description="Automatically bake from multiple angles",
        default=True
        #type: ignore
    ) 
    
    resolution: IntProperty(
        name="Resolution",
        description="Texture resolution",
        default=4096,
        min=64,
        max=16384
        #type: ignore
    ) 
    
    seam_bleed: IntProperty(
        name="Seam Bleed",
        description="Seam bleed in pixels",
        default=2,
        min=0,
        max=32
        #type: ignore
    ) 
    
    progress: IntProperty(
        name="Progress",
        default=0,
        min=0
        #type: ignore
    ) 
    
    total_steps: IntProperty(
        name="Total Steps",
        default=0,
        min=0
        #type: ignore
    ) 
    
    is_baking: BoolProperty(
        name="Is Baking",
        default=False
        #type: ignore
    ) 

class EEVEEBakerPreferences(AddonPreferences):
    bl_idname = "Texture Paint Bake"

    # Fast preset settings
    fast_taa_samples: IntProperty(
        name="Fast TAA Samples",
        description="TAA samples for fast preset",
        default=0,
        min=0,
        max=64
        #type: ignore
    )
    fast_shadow_size: EnumProperty(
        name="Fast Shadow Size",
        description="Shadow resolution for fast preset",
        items=[
            ('64', "64px", "64px shadow map"),
            ('128', "128px", "128px shadow map"),
            ('256', "256px", "256px shadow map"),
            ('512', "512px", "512px shadow map"),
            ('1024', "1024px", "1024px shadow map"),
            ('2048', "2048px", "2048px shadow map"),
            ('4096', "4096px", "4096px shadow map"),
        ],
        default='128'
        #type: ignore
    )

    # Balanced preset settings
    balanced_taa_samples: IntProperty(
        name="Balanced TAA Samples",
        description="TAA samples for balanced preset",
        default=16,
        min=0,
        max=64
        #type: ignore
    )
    balanced_shadow_size: EnumProperty(
        name="Balanced Shadow Size",
        description="Shadow resolution for balanced preset",
        items=[
            ('64', "64px", "64px shadow map"),
            ('128', "128px", "128px shadow map"),
            ('256', "256px", "256px shadow map"),
            ('512', "512px", "512px shadow map"),
            ('1024', "1024px", "1024px shadow map"),
            ('2048', "2048px", "2048px shadow map"),
            ('4096', "4096px", "4096px shadow map"),
        ],
        default='512'
        #type: ignore
    )

    # High preset settings
    high_taa_samples: IntProperty(
        name="High TAA Samples",
        description="TAA samples for high preset",
        default=32,
        min=0,
        max=64
        #type: ignore
    )
    high_shadow_size: EnumProperty(
        name="High Shadow Size",
        description="Shadow resolution for high preset",
        items=[
            ('64', "64px", "64px shadow map"),
            ('128', "128px", "128px shadow map"),
            ('256', "256px", "256px shadow map"),
            ('512', "512px", "512px shadow map"),
            ('1024', "1024px", "1024px shadow map"),
            ('2048', "2048px", "2048px shadow map"),
            ('4096', "4096px", "4096px shadow map"),
        ],
        default='1024'
        #type: ignore
    )

    def draw(self, context):
        layout = self.layout
        
        # Fast preset settings
        box = layout.box()
        box.label(text="Fast Preset Settings:")
        row = box.row()
        row.prop(self, "fast_taa_samples")
        row = box.row()
        row.prop(self, "fast_shadow_size")
        
        # Balanced preset settings
        box = layout.box()
        box.label(text="Balanced Preset Settings:")
        row = box.row()
        row.prop(self, "balanced_taa_samples")
        row = box.row()
        row.prop(self, "balanced_shadow_size")
        
        # High preset settings
        box = layout.box()
        box.label(text="High Preset Settings:")
        row = box.row()
        row.prop(self, "high_taa_samples")
        row = box.row()
        row.prop(self, "high_shadow_size")
