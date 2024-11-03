import bpy
from bpy.types import (Operator)
from ..utils import (ProjectionSettings,TextureProjector)
class EEVEE_OT_TextureBaker(bpy.types.Operator):
    bl_idname = "object.eevee_texture_baker"
    bl_label = "Bake Texture"
    bl_description = "Bake texture using EEVEE viewport rendering"
    
    _timer = None
    projector = None
    _camera_angles = []
    _current_angle_index = 0
    
    def modal(self, context, event):
        props = context.scene.eevee_baker
        
        if props.should_cancel:
            self.cleanup(context)
            props.should_cancel = False
            self.report({'INFO'}, "Baking cancelled")
            return {'FINISHED'}
        
        if event.type == 'TIMER':
            if not props.auto_bake:
                # Single shot mode
                self.projector.project_texture(0, 1, 1)
                self.cleanup(context)
                return {'FINISHED'}
            
            if self._current_angle_index >= len(self._camera_angles):
                self.cleanup(context)
                return {'FINISHED'}
            
            # Process next angle
            view_type, h_angle = self._camera_angles[self._current_angle_index]
            self.projector.position_camera(h_angle, view_type)
            self.projector.setup_viewport()
            self.projector.project_texture(f"{view_type}_{h_angle}", 
                                         self._current_angle_index + 1, 
                                         len(self._camera_angles))
            
            # Update progress
            props.progress = self._current_angle_index + 1
            props.total_steps = len(self._camera_angles)
            
            self._current_angle_index += 1
            
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        try:
            props = context.scene.eevee_baker
            props.is_baking = True
            props.progress = 0
            props.should_cancel = False

            preferences = context.preferences.addons["Texture Paint Bake"].preferences
            if not preferences:
                self.report({'ERROR'}, "Could not find addon preferences")
                return {'CANCELLED'}
            
            # Apply quality preset settings from preferences
            scene = context.scene
            if props.quality_preset == 'FAST':
                scene.eevee.taa_render_samples = preferences.fast_taa_samples
                scene.eevee.shadow_cube_size = preferences.fast_shadow_size
                scene.eevee.shadow_cascade_size = preferences.fast_shadow_size
            elif props.quality_preset == 'BALANCED':
                scene.eevee.taa_render_samples = preferences.balanced_taa_samples
                scene.eevee.shadow_cube_size = preferences.balanced_shadow_size
                scene.eevee.shadow_cascade_size = preferences.balanced_shadow_size
            else:  # HIGH
                scene.eevee.taa_render_samples = preferences.high_taa_samples
                scene.eevee.shadow_cube_size = preferences.high_shadow_size
                scene.eevee.shadow_cascade_size = preferences.high_shadow_size
                scene.eevee.taa_render_samples = 32
                scene.eevee.shadow_cube_size = '1024'
            settings = ProjectionSettings(
                resolution=props.resolution,
                image_name=props.file_name,
                output_folder=bpy.path.abspath(props.output_directory),
                seam_bleed=props.seam_bleed
            )
            
            self.projector = TextureProjector(settings)
            self.projector.obj = context.active_object
            self.projector.create_uv_map()
            self.projector.bake_image = self.projector.create_bake_image()
            self.projector.setup_material_nodes()
            self.projector.setup_camera()
            
            if props.auto_bake:
                self._camera_angles = self.projector.generate_camera_angles()
                props.total_steps = len(self._camera_angles)
                wm = context.window_manager
                self._timer = wm.event_timer_add(0.1, window=context.window)
                wm.modal_handler_add(self)
                return {'RUNNING_MODAL'}
            else:
                # Single shot mode
                self._camera_angles = [(None, 0)]
                props.total_steps = 1
                wm = context.window_manager
                self._timer = wm.event_timer_add(0.1, window=context.window)
                wm.modal_handler_add(self)
        except Exception as e:
            self.cleanup(context)  # Ensure cleanup happens
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}
        

    
    def cleanup(self, context):
        props = context.scene.eevee_baker
        props.is_baking = False
        
        if self._timer:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)
        
        if self.projector:
            self.projector.cleanup()
            
            # Remove camera if in auto-bake mode
            if props.auto_bake and self.projector.camera:
                bpy.data.objects.remove(self.projector.camera, do_unlink=True)