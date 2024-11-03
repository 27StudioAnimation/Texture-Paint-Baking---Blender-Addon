from dataclasses import dataclass

@dataclass
class ProjectionSettings:
    resolution: int = 4096
    uv_map_name: str = 'Bake_UV'
    image_name: str = 'Bake_Texture'
    camera_name: str = 'BakeCamera'
    seam_bleed: int = 2
    angle_offset: float = 30
    render_view_prefix: str = "EEVEE Bake Test_Model"
    output_folder: str = "texture_projections"
    temp_folder: str = "temp_renders"
    