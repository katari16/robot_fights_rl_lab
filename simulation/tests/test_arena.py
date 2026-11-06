import mujoco
import numpy as np
import pytest
from arena import Arena, JOINTS

@pytest.fixture(scope='module')
def arena():
    return Arena()


def test_model_and_joint_mapping(arena):
    m=arena.model
    assert (m.nq,m.nv,m.nu)==(72,70,58)
    for robot in range(2):
        for column,name in enumerate(JOINTS):
            assert m.joint(f'g1_{robot}/{name}').qposadr[0]==robot*36+7+column
    collision=(m.geom_contype!=0)|(m.geom_conaffinity!=0)
    assert not np.any(m.geom_type[collision]==mujoco.mjtGeom.mjGEOM_MESH)
    assert np.all(m.geom_contype[m.geom_type==mujoco.mjtGeom.mjGEOM_MESH]==0)


def test_robot_robot_and_mat_contacts(arena):
    arena.reset()
    arena.data.qpos[36:39]=arena.data.qpos[:3]+[.1,0,0]
    mujoco.mj_forward(arena.model,arena.data)
    pairs=[tuple(arena.model.geom(g).name for g in c.geom) for c in arena.data.contact]
    assert any(any(n.startswith('g1_0/') for n in p) and any(n.startswith('g1_1/') for n in p) for p in pairs)
    arena.reset()
    arena.data.qpos[2]-=.12
    mujoco.mj_forward(arena.model,arena.data)
    assert any('mat' in [arena.model.geom(g).name for g in c.geom] for c in arena.data.contact)
    arena.reset()


def test_physics_steps_and_torque_limits(arena):
    arena.reset()
    arena.step(np.full((2,29),1e6))
    np.testing.assert_allclose(arena.data.ctrl,arena.model.actuator_ctrlrange[:,1])
    arena.reset()
    for _ in range(1000):arena.step(np.zeros((2,29)))
    assert np.isfinite(arena.data.qpos).all()
    assert arena.data.time==pytest.approx(2)
    for bad in (np.zeros(58),np.full((2,29),np.nan)):
        with pytest.raises(ValueError):arena.step(bad)
    arena.reset()

