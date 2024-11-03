bl_info = {
    "name": "texture paint bake",
    "author": "STUDIO27",
    "version": (1, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > EEVEE Baker",
    "description": "Bake textures using EEVEE viewport rendering",
    "category": "Object",
}
import bpy
from bpy.props import (IntProperty,PointerProperty)
from .operators import *
from .panels import *
from .properties import *
from .utils import *
from .operators import EEVEE_OT_TextureBaker


def node_tree_changed_handler(scene):
    """Handler to update show_bake property when node connections change"""
    active_obj = bpy.context.active_object
    if not active_obj or active_obj.type != 'MESH' or not active_obj.data.materials:
        return

    mat = active_obj.data.materials[0]
    is_bake_connected = EEVEE_OT_ToggleBakePreview.is_bake_texture_connected(mat)
    
    scene.eevee_baker.show_bake = is_bake_connected

classes = (
    EEVEEBakerPreferences,
    EEVEEBakerProperties,
    EEVEE_OT_TextureBaker,
    EEVEE_OT_CancelBake,
    EEVEE_OT_ToggleBakePreview,
    EEVEE_PT_TextureBakerPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.eevee_baker = bpy.props.PointerProperty(type=EEVEEBakerProperties)
    bpy.types.Scene.eevee_baker_progress = bpy.props.IntProperty(default=0)
    bpy.types.Scene.eevee_baker_total_steps = bpy.props.IntProperty(default=0)
    bpy.app.handlers.depsgraph_update_post.append(node_tree_changed_handler)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.eevee_baker
    del bpy.types.Scene.eevee_baker_progress
    del bpy.types.Scene.eevee_baker_total_steps
    if node_tree_changed_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(node_tree_changed_handler)
    if hasattr(bpy.types.Scene, "eevee_baker_projector"):
        del bpy.types.Scene.eevee_baker_projector