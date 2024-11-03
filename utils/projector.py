import os
import bpy
from bpy.types import (Operator)
from contextlib import contextmanager
from typing import Optional, List, Tuple
import time
import math
from mathutils import Vector
from .settings import ProjectionSettings
from .functions import memoize
class TextureProjector:
    def __init__(self, settings: ProjectionSettings):
        self.settings = settings
        self.obj: Optional[bpy.types.Object] = None
        self.bake_image: Optional[bpy.types.Image] = None
        self.camera: Optional[bpy.types.Object] = None
        self.temp_files: List[Tuple[str, str]] = []
        self.original_nodes = {}
        self._setup_directories()
        self._view3d_cache = None
        self.aspect_ratio = 1.0
        self.optimize_render_settings()

    def optimize_render_settings(self):
        """Apply optimized render settings for faster performance"""
        scene = bpy.context.scene
        
        # Optimize EEVEE settings
        scene.eevee.taa_render_samples = 8  # Reduced from 16
        scene.eevee.use_taa_reprojection = True
        scene.eevee.use_ssr = False  # Disable screen space reflections
        scene.eevee.use_ssr_refraction = False
        scene.eevee.use_gtao = False  # Disable ambient occlusion
        scene.eevee.use_bloom = False  # Disable bloom
        scene.eevee.use_motion_blur = False
        scene.eevee.shadow_cube_size = '512'  # Reduce shadow quality
        scene.eevee.shadow_cascade_size = '512'
        
        # Optimize viewport settings
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces[0]
                space.shading.show_shadows = False
                space.overlay.show_overlays = False

    def _setup_directories(self):
        """Creates output and temp directories with error handling"""
        try:
            base_dir = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else bpy.app.tempdir
            
            self.output_dir = os.path.join(base_dir, self.settings.output_folder)
            self.temp_dir = os.path.join(base_dir, self.settings.temp_folder)
            
            os.makedirs(self.output_dir, exist_ok=True)
            os.makedirs(self.temp_dir, exist_ok=True)
            
        except Exception as e:
            raise RuntimeError(f"Failed to setup directories: {str(e)}")

    @contextmanager
    def view3d_context(self):
        """Optimized 3D viewport context manager with caching"""
        if not self._view3d_cache:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    self._view3d_cache = area
                    break
            if not self._view3d_cache:
                raise RuntimeError("No 3D viewport found")
        
        with bpy.context.temp_override(area=self._view3d_cache):
            yield self._view3d_cache

    @contextmanager
    def object_mode(self, mode: str):
        """Optimized object mode switching"""
        if not self.obj:
            raise ValueError("No active object")
            
        original_mode = self.obj.mode
        if original_mode != mode:
            bpy.ops.object.mode_set(mode=mode)
        try:
            yield
        finally:
            if original_mode != mode:
                bpy.ops.object.mode_set(mode=original_mode)

    def cleanup_render_view_image(self, image_name: str):
        """Clean up existing render view image if it exists"""
        if image_name in bpy.data.images:
            image = bpy.data.images[image_name]
            image.user_clear()
            bpy.data.images.remove(image)

    def cleanup(self):
        """Optimized cleanup with batch processing"""
        print("Cleaning up resources...")
        
        # Batch cleanup of images
        images_to_remove = []
        for image_name, temp_path in self.temp_files:
            try:
                if image_name in bpy.data.images:
                    image = bpy.data.images[image_name]
                    image.use_fake_user = False
                    image.user_clear()
                    images_to_remove.append(image)
                
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
            except Exception as e:
                print(f"Error cleaning up {image_name}: {str(e)}")
        
        # Batch remove images
        if images_to_remove:
            bpy.data.batch_remove(images_to_remove)
        
        self.temp_files.clear()
        
        # Cleanup temp directory
        try:
            if os.path.exists(self.temp_dir) and not os.listdir(self.temp_dir):
                os.rmdir(self.temp_dir)
        except Exception as e:
            print(f"Error removing temp directory: {str(e)}")

    def create_uv_map(self):
        """Creates UV map only if needed"""
        bpy.context.view_layer.objects.active = self.obj
        props = bpy.context.scene.eevee_baker
        
        # Check if UV map already exists
        if self.settings.uv_map_name not in self.obj.data.uv_layers or props.force_new_uv:
            if self.settings.uv_map_name in self.obj.data.uv_layers:
                self.obj.data.uv_layers.remove(self.obj.data.uv_layers[self.settings.uv_map_name])
            self.obj.data.uv_layers.new(name=self.settings.uv_map_name)
            
            self.obj.data.uv_layers[self.settings.uv_map_name].active = True
            
            with self.object_mode('EDIT'):
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.00)

    def create_bake_image(self) -> bpy.types.Image:
        """Creates or reuses bake image based on auto_bake setting"""
        props = bpy.context.scene.eevee_baker
        
        if self.settings.image_name in bpy.data.images:
            if not props.auto_bake:
                # For single bake, reuse existing image
                return bpy.data.images[self.settings.image_name]
            else:
                # For auto bake, remove and recreate
                self.cleanup_render_view_image(self.settings.image_name)
        
        img = bpy.data.images.new(
            name=self.settings.image_name,
            width=self.settings.resolution,
            height=self.settings.resolution,
            alpha=True,
            float_buffer=False
        )
        img.generated_color = (0, 0, 0, 0)
        img_path = os.path.join(self.output_dir, f"{self.settings.image_name}.png")
        img.filepath_raw = bpy.path.relpath(img_path)
        img.file_format = 'PNG'
        return img

    def setup_material_nodes(self):
        """Sets up material nodes with improved handling"""
        if not self.obj.data.materials:
            mat = bpy.data.materials.new(name="Bake_Material")
            self.obj.data.materials.append(mat)
        else:
            mat = self.obj.data.materials[0]
        
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Store original node setup if not already stored
        if mat not in self.original_nodes:
            self.original_nodes[mat] = {
                'nodes': [(n.name, n.type) for n in nodes],
                'output_connection': None
            }
            # Store the original output connection
            material_output = nodes.get("Material Output")
            if material_output and material_output.inputs['Surface'].links:
                self.original_nodes[mat]['output_connection'] = material_output.inputs['Surface'].links[0].from_node
        
        # Check if bake nodes already exist
        existing_uv = nodes.get("Bake_UV")
        existing_tex = nodes.get("Bake_Texture")
        material_output = nodes.get("Material Output")
        
        if not existing_uv:
            uv_map_node = nodes.new('ShaderNodeUVMap')
            uv_map_node.name = "Bake_UV"
            uv_map_node.uv_map = self.settings.uv_map_name
            uv_map_node.location = (-600, 0)
        else:
            uv_map_node = existing_uv
            
        if not existing_tex:
            tex_image = nodes.new('ShaderNodeTexImage')
            tex_image.name = "Bake_Texture"
            tex_image.image = self.bake_image
            tex_image.location = (-300, 0)
        else:
            tex_image = existing_tex
            tex_image.image = self.bake_image
        
        # Ensure nodes are connected
        if not any(l.from_node == uv_map_node and l.to_node == tex_image for l in links):
            links.new(uv_map_node.outputs[0], tex_image.inputs[0])
        
        nodes.active = None  # Deactivate for baking

    def setup_camera(self):
        """Creates and sets up the camera with correct aspect ratio"""
        if self.settings.camera_name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[self.settings.camera_name], do_unlink=True)
        
        bpy.ops.object.camera_add()
        self.camera = bpy.context.active_object
        self.camera.name = self.settings.camera_name
        
        # Force 1:1 aspect ratio for the camera
        self.camera.data.sensor_fit = 'HORIZONTAL'
        self.camera.data.sensor_width = 36
        self.camera.data.sensor_height = 36  # Make it square
        
        # Set scene render settings to match
        bpy.context.scene.render.pixel_aspect_x = 1
        bpy.context.scene.render.pixel_aspect_y = 1
        
        # Force resolution to be square
        bpy.context.scene.render.resolution_x = self.settings.resolution
        bpy.context.scene.render.resolution_y = self.settings.resolution

    @memoize
    def calculate_optimal_distance(self, view_type: str) -> float:
        """Cached calculation of optimal camera distance"""
        if not self.obj:
            return 2.0
            
        bbox_corners = [self.obj.matrix_world @ Vector(corner) for corner in self.obj.bound_box]
        dimensions = Vector((
            max(c[0] for c in bbox_corners) - min(c[0] for c in bbox_corners),
            max(c[1] for c in bbox_corners) - min(c[1] for c in bbox_corners),
            max(c[2] for c in bbox_corners) - min(c[2] for c in bbox_corners)
        ))
        
        max_dimension = max(dimensions.x, dimensions.y)
        height = dimensions.z
        
        distance_factors = {
            "below": max_dimension * 1.2,
            "total": max(max_dimension, height) * 2.0,
            "upper": max_dimension * 1.2
        }
        
        base_distance = distance_factors.get(view_type, max_dimension * 1.2)
        fov = self.camera.data.angle
        return (base_distance / (2 * math.tan(fov / 2))) * 0.8
    
    @memoize
    def get_view_parameters(self, view_type: str) -> tuple[float, float, Vector]:
        """Cached calculation of view parameters"""
        bbox_corners = [self.obj.matrix_world @ Vector(corner) for corner in self.obj.bound_box]
        min_bound = Vector(tuple(map(min, zip(*bbox_corners))))
        max_bound = Vector(tuple(map(max, zip(*bbox_corners))))
        
        center = (min_bound + max_bound) / 2
        height = max_bound.z - min_bound.z
        
        view_params = {
            "below": (0.3, min_bound.z - (height * 0.2), center),
            "total": (1.0, center.z, center),
            "upper": (1.7, max_bound.z + (height * 0.2), center)
        }
        
        return view_params.get(view_type, (1.0, center.z, center))
  
    def position_camera(self, horizontal_angle: float, view_type: str = "total"):
        """Position camera with improved positioning logic"""
        if not self.obj or not self.camera:
            raise ValueError("Object or camera not set")
            
        z_mult, z_pos, target = self.get_view_parameters(view_type)
        distance = self.calculate_optimal_distance(view_type)
        
        h_rad = math.radians(horizontal_angle)
        
        # Calculate camera position with adjusted angles
        if view_type == "below":
            # Steeper upward angle for below shots
            vertical_offset = distance * 0.3
            camera_pos = Vector((
                target.x + (distance * 0.9) * math.cos(h_rad),
                target.y + (distance * 0.9) * math.sin(h_rad),
                z_pos - vertical_offset
            ))
        elif view_type == "total":
            # Maintain straight-on view for total shots
            camera_pos = Vector((
                target.x + distance * math.cos(h_rad),
                target.y + distance * math.sin(h_rad),
                target.z
            ))
        else:  # upper
            # Steeper downward angle for upper shots
            vertical_offset = distance * 0.3
            camera_pos = Vector((
                target.x + (distance * 0.9) * math.cos(h_rad),
                target.y + (distance * 0.9) * math.sin(h_rad),
                z_pos + vertical_offset
            ))
        
        self.camera.location = camera_pos
        
        # Aim camera at target with adjusted tracking
        direction = target - camera_pos
        rot_quat = direction.to_track_quat('-Z', 'Y')
        self.camera.rotation_euler = rot_quat.to_euler()
        
        # Update scene camera
        bpy.context.scene.camera = self.camera

    def generate_camera_angles(self) -> list[tuple[str, float]]:
        """Generate optimized camera angles with reduced number of views"""
        angles = []
        
        # Reduce number of views for faster processing
        for view_type in ["below", "total", "upper"]:
            # Use only cardinal directions (reduced from 8 to 4 angles)
            for h_angle in [0, 90, 180, 270]:
                angles.append((view_type, h_angle))
        
        return angles

    def setup_viewport(self):
        """Configures viewport settings"""
        with self.view3d_context() as area:
            space = area.spaces[0]
            space.region_3d.view_perspective = 'CAMERA'
            space.shading.type = 'RENDERED'
            space.shading.use_scene_lights = True
            space.shading.use_scene_world = True

    def project_texture(self, angle: float, current_count: int, total_count: int):
        """Performs texture projection for given angle without external editor"""
        bpy.context.view_layer.objects.active = self.obj
        
        with self.object_mode('TEXTURE_PAINT'):
            settings = bpy.context.scene.tool_settings.image_paint
            settings.mode = 'IMAGE'  # Changed from 'MATERIAL' to 'IMAGE'
            settings.canvas = self.bake_image
            settings.use_occlude = True
            settings.use_backface_culling = True
            settings.seam_bleed = self.settings.seam_bleed
            settings.screen_grab_size = (self.settings.resolution, self.settings.resolution)
            
            with self.view3d_context() as area:
                print(f"Processing view {current_count}/{total_count}")
                
                render_image = self.create_temp_render()
                
                if render_image:
                    try:
                        bpy.context.scene.tool_settings.image_paint.clone_image = render_image
                        
                        with bpy.context.temp_override(
                            window=bpy.context.window,
                            area=area,
                            region=[r for r in area.regions if r.type == 'WINDOW'][0],
                            scene=bpy.context.scene,
                            active_object=self.obj
                        ):
                            bpy.ops.paint.project_image(image=render_image.name)
                            self.bake_image.update()
                            self.bake_image.save()
                            
                    except Exception as e:
                        print(f"Error during texture projection: {str(e)}")            
                          
    def create_temp_render(self) -> Optional[bpy.types.Image]:
        """Creates temporary render with improved settings"""
        scene = bpy.context.scene
        original_settings = {
            'resolution_x': scene.render.resolution_x,
            'resolution_y': scene.render.resolution_y,
            'filepath': scene.render.filepath,
            'engine': scene.render.engine,
            'use_persistent_data': scene.render.use_persistent_data
        }
        
        temp_path = os.path.join(self.temp_dir, f"temp_render_{int(time.time())}.png")
        
        try:
            # Configure render settings for optimal projection
            scene.render.resolution_x = self.settings.resolution
            scene.render.resolution_y = self.settings.resolution
            scene.render.engine = 'BLENDER_EEVEE'
            scene.render.use_persistent_data = True
            
            # Disable border rendering for full capture
            scene.render.use_border = False
            scene.render.use_crop_to_border = False
            
            # Configure image settings
            scene.render.image_settings.file_format = 'PNG'
            scene.render.image_settings.color_mode = 'RGBA'
            scene.render.image_settings.compression = 0
            scene.render.film_transparent = True
            scene.render.filepath = temp_path
            
            # Ensure proper EEVEE settings
            scene.eevee.use_gtao = True
            scene.eevee.gtao_distance = 0.2
            scene.eevee.use_ssr = True
            scene.eevee.use_ssr_refraction = True
            
            bpy.ops.render.render(write_still=True)
            
            if os.path.exists(temp_path):
                temp_name = f"{self.settings.render_view_prefix}_{int(time.time())}"
                temp_image = bpy.data.images.load(temp_path)
                temp_image.name = temp_name
                temp_image.pack()
                
                self.temp_files.append((temp_name, temp_path))
                return temp_image
            
            return None
                
        except Exception as e:
            print(f"Error creating temp render: {e}")
            return None
            
        finally:
            # Restore original settings
            for key, value in original_settings.items():
                setattr(scene.render, key, value)
    
    def process(self):
        """Optimized main processing function with better error handling"""
        props = bpy.context.scene.eevee_baker
        try:
            self.obj = bpy.context.active_object
            if not self.obj or self.obj.type != 'MESH':
                raise ValueError("Please select a mesh object")

            # Ensure bake preview is off during baking
            # props.show_bake = False

            # Setup operations
            self.create_uv_map()
            self.bake_image = self.create_bake_image()
            self.setup_material_nodes()
            self.setup_camera()

            # Batch setup operations
            operations = [
                self.create_uv_map,
                lambda: setattr(self, 'bake_image', self.create_bake_image()),
                self.setup_material_nodes,
                self.setup_camera
            ]
            
            for op in operations:
                try:
                    op()
                except Exception as e:
                    raise RuntimeError(f"Setup failed during {op.__name__}: {str(e)}")

            if self.camera:
                self.camera.data.lens = 35
            
            camera_angles = self.generate_camera_angles()
            total_angles = len(camera_angles)
            
            # Process views in optimized batches
            for idx, (view_type, h_angle) in enumerate(camera_angles, 1):
                try:
                    self.position_camera(h_angle, view_type)
                    self.setup_viewport()
                    self.project_texture(f"{view_type}_{h_angle}", idx, total_angles)
                except Exception as e:
                    print(f"Error processing view {idx}/{total_angles}: {str(e)}")
                    continue
                    
        finally:
            self.cleanup()

