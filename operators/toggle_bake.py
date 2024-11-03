import bpy
from bpy.types import (Operator)


class EEVEE_OT_ToggleBakePreview(Operator):
    bl_idname = "object.eevee_toggle_bake_preview"
    bl_label = "Toggle Bake Preview"
    bl_description = "Toggle between bake preview and original shader"

    @staticmethod
    def is_bake_texture_connected(mat):
        """Check if Bake_Texture is connected to Material Output"""
        if not mat or not mat.use_nodes:
            return False
            
        material_output = mat.node_tree.nodes.get("Material Output")
        if not material_output or not material_output.inputs['Surface'].is_linked:
            return False
            
        connected_node = material_output.inputs['Surface'].links[0].from_node
        return connected_node.name == "Bake_Texture"

    def toggle_material_nodes(self, obj, show_bake: bool):
        """Toggle between bake preview and original shader"""
        if not obj or not obj.data.materials:
            print("No object or materials found.")
            return

        mat = obj.data.materials[0]
        if not mat.use_nodes:
            print("Material does not use nodes.")
            return

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        bake_tex = nodes.get("Bake_Texture")
        material_output = nodes.get("Material Output")

        if not bake_tex:
            print("Bake_Texture node not found.")
            return
        if not material_output:
            print("Material Output node not found.")
            return

        # Check if Bake_Texture is already connected, and only save the original if it's not
        if show_bake:
            if "original_connection" not in mat:
                if material_output.inputs['Surface'].is_linked:
                    current_link = material_output.inputs['Surface'].links[0]
                    if current_link.from_node.name != "Bake_Texture":
                        # Store both the node name and the output socket index
                        mat["original_connection"] = {
                            "node_name": current_link.from_node.name,
                            "socket_index": list(current_link.from_node.outputs).index(current_link.from_socket)
                        }
                    else:
                        print("Bake_Texture is already connected; original connection not saved.")

        # Clear existing connections on the Material Output's 'Surface' input
        for link in material_output.inputs['Surface'].links:
            links.remove(link)

        if show_bake:
            # Connect the bake texture node's output to the Material Output
            links.new(bake_tex.outputs[0], material_output.inputs['Surface'])
        else:
            # Retrieve the saved original connection information and reconnect
            original_connection = mat.get("original_connection")
            if original_connection:
                original_node = nodes.get(original_connection["node_name"])
                if original_node:
                    socket_index = original_connection["socket_index"]
                    if socket_index < len(original_node.outputs):
                        links.new(original_node.outputs[socket_index], material_output.inputs['Surface'])
                    else:
                        links.new(bake_tex.outputs[0], material_output.inputs['Surface'])
                else:
                    links.new(bake_tex.outputs[0], material_output.inputs['Surface'])
            else:
                links.new(bake_tex.outputs[0], material_output.inputs['Surface'])

    def execute(self, context):
        props = context.scene.eevee_baker
        active_obj = context.active_object

        if active_obj and active_obj.type == 'MESH' and active_obj.data.materials:
            # Toggle the state
            props.show_bake = not props.show_bake
            self.toggle_material_nodes(active_obj, props.show_bake)
        else:
            print("No active mesh object found.")

        # Clean up the property only after the execution is finished
        if active_obj and active_obj.type == 'MESH' and active_obj.data.materials:
            mat = active_obj.data.materials[0]
            if "original_connection" in mat and not props.show_bake:
                del mat["original_connection"]

        return {'FINISHED'}
