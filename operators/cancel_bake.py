import bpy
from bpy.types import Operator

class EEVEE_OT_CancelBake(Operator):
    bl_idname = "object.eevee_cancel_bake"
    bl_label = "Cancel Bake"
    bl_description = "Cancel the current baking process"
    
    def execute(self, context):
        props = context.scene.eevee_baker
        props.should_cancel = True  # Signal the baker to stop
        props.is_baking = False    # Reset baking state
        props.progress = 0         # Reset progress
        
        return {'FINISHED'}