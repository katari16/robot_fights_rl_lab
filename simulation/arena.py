"""Two stock G1s in a rectangular arena, with primitive contact geometry."""

from __future__ import annotations

from copy import deepcopy
from io import BytesIO
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import resvg_py
import mujoco
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
G1_XML = ROOT / "external/unitree_rl_mjlab/src/assets/robots/unitree_g1/xmls/g1.xml"
DEFAULT_LOGO = HERE / "assets/rsl-mark.svg"
SPAWNS = ((-1.05, 0, 0), (1.05, 0, np.pi))

# Same order as Robo Jab's CSV and Unitree's 29-DoF MJCF.
JOINTS = tuple(
    [
        f"{s}_{j}_joint"
        for s in ("left", "right")
        for j in (
            "hip_pitch",
            "hip_roll",
            "hip_yaw",
            "knee",
            "ankle_pitch",
            "ankle_roll",
        )
    ]
    + [f"waist_{j}_joint" for j in ("yaw", "roll", "pitch")]
    + [
        f"{s}_{j}_joint"
        for s in ("left", "right")
        for j in (
            "shoulder_pitch",
            "shoulder_roll",
            "shoulder_yaw",
            "elbow",
            "wrist_roll",
            "wrist_pitch",
            "wrist_yaw",
        )
    ]
)


def floor_texture(logo: Path = DEFAULT_LOGO) -> bytes:
    """A visual-only texture, with the supplied mark centered on the mat."""
    size = (2048, 1536)
    img = Image.new("RGB", size, (27, 32, 43))
    draw = ImageDraw.Draw(img)
    for x in range(0, size[0], 128):
        draw.line((x, 0, x, size[1]), fill=(30, 36, 47), width=1)
    for y in range(0, size[1], 128):
        draw.line((0, y, size[0], y), fill=(30, 36, 47), width=1)
    draw.rectangle((84, 84, 1964, 1452), outline=(113, 127, 148), width=7)
    draw.rectangle((110, 110, 1938, 1426), outline=(56, 66, 83), width=2)
    draw.line((84, 84, 550, 84), fill=(33, 215, 184), width=13)
    draw.line((1498, 1452, 1964, 1452), fill=(145, 98, 230), width=13)
    for x, color in ((640, (33, 215, 184)), (1408, (145, 98, 230))):
        draw.line((x - 65, 690, x + 65, 690), fill=color, width=4)
        draw.line((x - 65, 846, x + 65, 846), fill=color, width=4)
    mark = Image.open(
        BytesIO(resvg_py.svg_to_bytes(svg_path=str(logo), width=640, height=306))
    )
    img.paste(mark, ((size[0] - mark.width) // 2, (size[1] - mark.height) // 2), mark)
    buf = BytesIO()
    # MuJoCo's texture convention has its vertical origin at the other edge.
    img.transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(buf, format="PNG")
    return buf.getvalue()


def _geom(parent, name, kind="box", **attrs):
    return ET.SubElement(
        parent,
        "geom",
        name=name,
        type=kind,
        **{
            k: " ".join(map(str, v)) if isinstance(v, (tuple, list)) else str(v)
            for k, v in attrs.items()
        },
    )


def foot_bottom(model, data, index: int) -> float:
    ids = [
        model.geom(f"g1_{index}/{side}_foot{n}_collision").id
        for side in ("left", "right")
        for n in range(1, 8)
    ]
    sizes = model.geom_size[ids]
    axes_z = data.geom_xmat[ids].reshape(-1, 3, 3)[:, 2, 2]
    return float(
        np.min(data.geom_xpos[ids, 2] - sizes[:, 0] - sizes[:, 1] * np.abs(axes_z))
    )


def make_spec(logo: Path = DEFAULT_LOGO) -> mujoco.MjSpec:
    source = ET.parse(G1_XML).getroot()
    root = ET.Element("mujoco", model="RSL rectangular G1 arena")
    ET.SubElement(root, "compiler", angle="radian", autolimits="true")
    ET.SubElement(
        root, "option", timestep="0.002", integrator="implicitfast", cone="elliptic"
    )
    visual = ET.SubElement(root, "visual")
    ET.SubElement(
        visual,
        "global",
        offwidth="1920",
        offheight="1080",
        azimuth="135",
        elevation="-24",
    )
    ET.SubElement(visual, "quality", shadowsize="4096", offsamples="4")
    ET.SubElement(
        visual,
        "headlight",
        ambient="0.4 0.4 0.44",
        diffuse="0.6 0.6 0.6",
        specular="0.2 0.2 0.2",
    )
    ET.SubElement(visual, "rgba", haze="0.03 0.04 0.06 1")
    root.append(deepcopy(source.find("default")))
    asset = deepcopy(source.find("asset"))
    root.append(asset)
    for mesh in asset.findall("mesh"):
        mesh.set("file", Path(mesh.get("file")).name)
    ET.SubElement(asset, "texture", name="mat_texture", type="2d", file="mat.png")
    ET.SubElement(
        asset,
        "material",
        name="mat",
        texture="mat_texture",
        texuniform="false",
        reflectance="0",
        shininess="0.15",
    )
    for name, rgba in (
        ("frame", "0.065 0.08 0.105 1"),
        ("glass", "0.35 0.55 0.65 0.09"),
        ("mint", "0.13 0.84 0.72 1"),
        ("violet", "0.57 0.38 0.9 1"),
    ):
        ET.SubElement(asset, "material", name=name, rgba=rgba, shininess="0.5")
    world = ET.SubElement(root, "worldbody")
    for i, pos in enumerate(("0 -3 6", "1 3 5", "-4 0 3")):
        ET.SubElement(
            world,
            "light",
            name=f"light_{i}",
            pos=pos,
            dir="0 0 -1",
            directional="false",
            diffuse="0.7 0.75 0.85",
            castshadow="true" if i == 0 else "false",
        )
    _geom(
        world,
        "surround",
        "plane",
        size=(20, 20, 0.1),
        pos=(0, 0, -0.28),
        rgba=(0.065, 0.075, 0.095, 1),
    )
    _geom(
        world, "platform", size=(2.55, 1.85, 0.13), pos=(0, 0, -0.15), material="frame"
    )
    _geom(
        world,
        "mat",
        size=(2.3, 1.6, 0.04),
        pos=(0, 0, -0.04),
        material="mat",
        friction=(0.8, 0.005, 0.0001),
        condim=3,
    )
    for x in (-2.33, 2.33):
        for y in (-1.63, 1.63):
            color = "mint" if x < 0 else "violet"
            _geom(
                world,
                f"post_{x}_{y}",
                size=(0.09, 0.09, 0.72),
                pos=(x, y, 0.64),
                material="frame",
            )
            _geom(
                world,
                f"pad_{x}_{y}",
                size=(0.11, 0.11, 0.45),
                pos=(x * 0.98, y * 0.98, 0.75),
                material=color,
            )
    for axis, span, edge in ((0, 2.3, 1.63), (1, 1.6, 2.33)):
        for side in (-1, 1):

            def place(a, z):
                return (a, side * edge, z) if axis == 0 else (side * edge, a, z)

            size = (span, 0.025, 0.61) if axis == 0 else (0.025, span, 0.61)
            _geom(
                world,
                f"panel_{axis}_{side}",
                size=size,
                pos=place(0, 0.61),
                material="glass",
            )
            for z in (0.03, 1.24):
                _geom(
                    world,
                    f"rail_{axis}_{side}_{z}",
                    "capsule",
                    size=(0.028,),
                    fromto=(*place(-span, z), *place(span, z)),
                    material="frame",
                )
            for a in (-span / 3, span / 3):
                _geom(
                    world,
                    f"stanchion_{axis}_{side}_{a}",
                    size=(0.023, 0.023, 0.61),
                    pos=place(a, 0.61),
                    material="frame",
                )
            _geom(
                world,
                f"light_strip_{axis}_{side}",
                "capsule",
                size=(0.009,),
                fromto=(*place(-span, 0.075), *place(span, 0.075)),
                material="mint" if side < 0 else "violet",
                contype=0,
                conaffinity=0,
            )
    contact = ET.SubElement(root, "contact")
    actuator = ET.SubElement(root, "actuator")
    for index, (x, y, yaw) in enumerate(SPAWNS):
        prefix = f"g1_{index}/"
        body = deepcopy(source.find("worldbody/body"))
        for elem in list(body):
            if elem.tag in ("light", "camera"):
                body.remove(elem)
        for elem in body.iter():
            if elem.get("name"):
                elem.set("name", prefix + elem.get("name"))
            if elem.tag == "geom" and "collision" in elem.get("name", ""):
                # Environment bit 1, robot A bit 2, robot B bit 4. Self contacts stay enabled.
                elem.set("contype", str(2 << index))
                elem.set("conaffinity", "7")
                elem.set("condim", "3" if "foot" in elem.get("name", "") else "1")
        body.set("pos", f"{x} {y} 0.8")
        body.set("quat", f"{np.cos(yaw / 2)} 0 0 {np.sin(yaw / 2)}")
        world.append(body)
        # Primitive envelopes overlap at these connected wrist and hip assemblies.
        for side in ("left", "right"):
            ET.SubElement(
                contact,
                "exclude",
                body1=prefix + f"{side}_elbow_link",
                body2=prefix + f"{side}_wrist_pitch_link",
            )
            ET.SubElement(
                contact,
                "exclude",
                body1=prefix + "pelvis",
                body2=prefix + f"{side}_hip_roll_link",
            )
        for name in JOINTS:
            limit = (
                139
                if "knee" in name or "hip_roll" in name
                else 88
                if "hip" in name or "waist_yaw" in name
                else 50
                if "ankle" in name or "waist" in name
                else 5
                if "wrist_pitch" in name or "wrist_yaw" in name
                else 25
            )
            ET.SubElement(
                actuator,
                "motor",
                name=prefix + name,
                joint=prefix + name,
                ctrllimited="true",
                ctrlrange=f"{-limit} {limit}",
            )
    assets = {p.name: p.read_bytes() for p in (G1_XML.parent / "assets").glob("*.STL")}
    assets["mat.png"] = floor_texture(logo)
    spec = mujoco.MjSpec.from_string(
        ET.tostring(root, encoding="unicode"), assets=assets
    )
    model = spec.compile()
    qpos = model.qpos0.copy()
    defaults = {
        ".*_hip_pitch_joint": -0.1,
        ".*_knee_joint": 0.3,
        ".*_ankle_pitch_joint": -0.2,
        ".*_shoulder_pitch_joint": 0.35,
        ".*_elbow_joint": 0.87,
        "left_shoulder_roll_joint": 0.18,
        "right_shoulder_roll_joint": -0.18,
    }
    for index in range(2):
        for name in JOINTS:
            for pattern, value in defaults.items():
                if re.fullmatch(pattern, name):
                    qpos[model.joint(f"g1_{index}/{name}").qposadr[0]] = value
    data = mujoco.MjData(model)
    data.qpos[:] = qpos
    mujoco.mj_forward(model, data)
    for index in range(2):
        qpos[index * 36 + 2] -= foot_bottom(model, data, index)
    spec.add_key(name="nominal", qpos=qpos)
    return spec


class Arena:
    """Physics access for two 29-DoF robots. Actions are motor torques in Nm.

    This is an environment foundation, not a trained balance controller.
    Kinematic replay uses set_pose; physics advances only through step.
    """

    def __init__(self, logo: Path = DEFAULT_LOGO):
        self.spec = make_spec(logo)
        self.model = self.spec.compile()
        self.data = mujoco.MjData(self.model)
        self.reset()

    def reset(self):
        mujoco.mj_resetDataKeyframe(self.model, self.data, 0)
        mujoco.mj_forward(self.model, self.data)
        return self.data.qpos.copy()

    def set_pose(self, qpos):
        qpos = np.asarray(qpos, dtype=float)
        if qpos.shape != (self.model.nq,) or not np.isfinite(qpos).all():
            raise ValueError(f"Expected {self.model.nq} finite position values")
        qpos = qpos.copy()
        for start in (3, 39):
            norm = np.linalg.norm(qpos[start : start + 4])
            if norm < 1e-12:
                raise ValueError("Root quaternion cannot be zero")
            qpos[start : start + 4] /= norm
        self.data.qpos[:] = qpos
        self.data.qvel[:] = 0
        mujoco.mj_forward(self.model, self.data)

    def step(self, torques):
        torques = np.asarray(torques, dtype=float)
        if torques.shape != (2, 29) or not np.isfinite(torques).all():
            raise ValueError("Expected finite torques with shape (2, 29)")
        self.data.ctrl[:] = np.clip(
            torques.ravel(),
            self.model.actuator_ctrlrange[:, 0],
            self.model.actuator_ctrlrange[:, 1],
        )
        mujoco.mj_step(self.model, self.data)
        return self.data.qpos.copy()
