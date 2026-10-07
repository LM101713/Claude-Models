"""Render materials matching the approved palette (preview only; filament
colours are chosen on the paint test tile)."""
import bpy

_M = {}


def _principled(name, base, metallic=0.0, roughness=0.5, transmission=0.0, emission=None, coat=0.0):
    if name in _M:
        return _M[name]
    m = bpy.data.materials.new("MAT_" + name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1.0)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = roughness
    if transmission:
        b.inputs["Transmission Weight"].default_value = transmission
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emission:
        b.inputs["Emission Color"].default_value = (*emission[0], 1.0)
        b.inputs["Emission Strength"].default_value = emission[1]
    _M[name] = m
    return m


def satin_alu():
    # cast / bead-blasted aluminium: not a mirror (flat faces reflected the dark sky and went black)
    return _principled("satin_aluminium", (0.66, 0.67, 0.69), metallic=0.75, roughness=0.58)


def matte_black():
    return _principled("matte_black", (0.025, 0.025, 0.027), metallic=0.0, roughness=0.78)


def stainless():
    return _principled("stainless", (0.72, 0.70, 0.66), metallic=1.0, roughness=0.22)


def painted_header():
    return _principled("header_ceramic", (0.80, 0.80, 0.78), metallic=0.3, roughness=0.35)


def amber_boot():
    return _principled("boot_glow", (0.95, 0.65, 0.25), metallic=0.0, roughness=0.3, transmission=0.6, emission=((1.0, 0.55, 0.15), 1.5))


def dark_steel():
    return _principled("dark_steel", (0.18, 0.18, 0.19), metallic=0.8, roughness=0.45)


def brushed_plate():
    return _principled("brushed_plate", (0.55, 0.56, 0.58), metallic=1.0, roughness=0.3)


def backdrop():
    return _principled("backdrop", (0.42, 0.43, 0.45), metallic=0.0, roughness=0.9)
