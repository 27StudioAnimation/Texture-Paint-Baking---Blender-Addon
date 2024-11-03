import bpy
from bpy.types import (Panel)
from ..operators import (EEVEE_OT_ToggleBakePreview, EEVEE_OT_CancelBake, EEVEE_OT_TextureBaker)

class EEVEE_PT_TextureBakerPanel(Panel):
    bl_label = "EEVEE Texture Baker"
    bl_idname = "EEVEE_PT_texture_baker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EEVEE Baker'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.eevee_baker
        
        # Only enable settings when not baking
        for prop in ["output_directory", "file_name", "resolution", "seam_bleed", "auto_bake","quality_preset"]:
            row = layout.row()
            row.enabled = not props.is_baking
            row.prop(props, prop)
        if not props.is_baking:
            row = layout.row()
            row.operator(EEVEE_OT_ToggleBakePreview.bl_idname, 
                        text="Show Original" if props.show_bake else "Show Bake",
                        icon='HIDE_OFF' if props.show_bake else 'HIDE_ON')
        if props.is_baking:
            box = layout.box()
            box.label(text=f"Baking Progress: {props.progress}/{props.total_steps}")
            # Fixed progress bar
            row = box.row()
            row.prop(props, "progress", text="", slider=True)
            # Add cancel button
            row = box.row()
            row.operator(EEVEE_OT_CancelBake.bl_idname, icon='X')
        else:
            layout.operator(EEVEE_OT_TextureBaker.bl_idname, icon='RENDER_STILL')
