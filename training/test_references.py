"""Checks for the frame/order mistakes that can silently corrupt a tracker."""

import unittest

import mujoco
import numpy as np

from prepare import DATA, mirror, training_scene


class References(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene, cls.model = training_scene()
        cls.motions = {
            n: np.load(DATA / f"{n}.npz")
            for n in ("left_punch", "right_punch", "right_kick")
        }

    def test_nominal_entry_and_recovery(self):
        for motion in self.motions.values():
            np.testing.assert_allclose(
                motion["qpos"][:30], np.tile(motion["qpos"][0], (30, 1))
            )
            np.testing.assert_allclose(
                motion["qpos"][-70:], np.tile(motion["qpos"][0], (70, 1))
            )
            np.testing.assert_allclose(motion["joint_vel"][-60:], 0, atol=1e-10)
            self.assertEqual(int(motion["fps"][0]), 50)

    def test_mirror_matches_forward_kinematics(self):
        right = self.motions["right_punch"]["qpos"]
        left = self.motions["left_punch"]["qpos"]
        names = self.scene["robot"].joint_names
        np.testing.assert_allclose(
            mirror(mirror(right, names), names), right, atol=1e-12
        )
        a, b = mujoco.MjData(self.model), mujoco.MjData(self.model)
        a.qpos[:], b.qpos[:] = right[139], left[139]
        mujoco.mj_forward(self.model, a)
        mujoco.mj_forward(self.model, b)
        for side, opposite in (("left", "right"), ("right", "left")):
            for part in ("ankle_roll", "wrist_yaw", "elbow", "knee"):
                ia = self.model.body(f"robot/{side}_{part}_link").id
                ib = self.model.body(f"robot/{opposite}_{part}_link").id
                np.testing.assert_allclose(
                    a.xpos[ia] * [1, -1, 1], b.xpos[ib], atol=3e-4
                )

    def test_saved_body_order_matches_training_model(self):
        data = mujoco.MjData(self.model)
        for motion in self.motions.values():
            self.assertEqual(
                tuple(motion["body_names"]), self.scene["robot"].body_names
            )
            self.assertEqual(
                tuple(motion["joint_names"]), self.scene["robot"].joint_names
            )
            ids = [self.model.body("robot/" + n).id for n in motion["body_names"]]
            for frame in (0, 128, len(motion["qpos"]) - 1):
                data.qpos[:] = motion["qpos"][frame]
                mujoco.mj_forward(self.model, data)
                np.testing.assert_allclose(
                    data.xpos[ids], motion["body_pos_w"][frame], atol=1e-10
                )

    def test_kick_has_one_support_leg(self):
        kick = self.motions["right_kick"]
        names = list(kick["body_names"])
        left = kick["body_pos_w"][:, names.index("left_ankle_roll_link"), 2]
        right = kick["body_pos_w"][:, names.index("right_ankle_roll_link"), 2]
        peak = np.argmax(right)
        self.assertGreater(right[peak], 0.65)
        self.assertLess(left[peak], 0.10)


if __name__ == "__main__":
    unittest.main()
