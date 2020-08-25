import bpy
from os.path import basename
from mathutils import Vector, Quaternion, Matrix, Euler
from math import pi, radians

from reclaimer.hek.defs.antr import antr_def
from reclaimer.animation.animation_decompilation import extract_model_animations
from reclaimer.animation.jma import JmaAnimationSet,read_jma

from ..constants import (JMS_VERSION_HALO_1, NODE_NAME_PREFIX,
	MARKER_NAME_PREFIX, VERY_SMALL_NUMBER, FAKE_NODE_PREFIX)

def read_halo1anim(filepath):
    ''' Generates JmaAnimationSet'''


    tag = antr_def.build(filepath=filepath)

    data = extract_model_animations(tag.data.tagdata,"",write_jma=False)
    for anim in data:
        anim.apply_root_node_info_to_states()
    return data

def read_halojma(filepath):
    jma_string = open(filepath).read()

    jma = read_jma(jma_string,"",basename(filepath))
    jma.apply_root_node_info_to_states()
    return [jma]
def import_animations(animations,scale = 0.03048, format_filter = {}):
    scene = bpy.context.scene
    target = bpy.context.object
    # just random lazy inspection stuff
    bpy.debug_anim = animations
    if target.type != "ARMATURE":
        raise "Not an armature"
    
    if not target.animation_data:
        target.animation_data_create()
    bpy.ops.object.mode_set(mode="POSE")
    
    print(format_filter)
    for anim in animations:
        if len(format_filter) > 0 and len(animations) > 1 and anim.ext not in format_filter:
            
            continue
        action = bpy.data.actions.new(anim.name)
        target.animation_data.action = action
        action.use_fake_user = True
        scene.frame_start = 0
        scene.frame_end = len(anim.frames) - 1
        pose_bones = []
        for node in anim.nodes:
            pose_bones.append(target.pose.bones[NODE_NAME_PREFIX + node.name])
  
        for f in range(len(anim.frames)):
            bpy.context.scene.frame_set(f)
            for n in range(len(anim.frames[f])):
                frame = anim.frames[f][n]
                bone = pose_bones[n]
                
                T = Matrix.Translation(Vector((frame.pos_x, frame.pos_y, frame.pos_z))* scale)
                R = Quaternion((frame.rot_w, frame.rot_i, frame.rot_j, frame.rot_k)).inverted().to_matrix().to_4x4()
                S = Matrix.Scale(frame.scale ,4,(1,1,1))
        
        
                M =  T @ R @ S
                if not bone.parent:
                    bone.matrix = M
                else:
                    P = bone.parent.matrix
                    bone.matrix = P @ M
                bone.keyframe_insert(data_path="location", index=-1)
                bone.keyframe_insert(data_path="rotation_quaternion", index=-1)


    scene.frame_set(0)
    bpy.ops.object.mode_set(mode="OBJECT")