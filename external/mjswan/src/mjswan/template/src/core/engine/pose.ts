/** Validate before touching live state; normalize free/ball joint quaternions. */
export function validatedPose(
  values: ArrayLike<number>, nq: number,
  jointTypes: ArrayLike<number>, addresses: ArrayLike<number>,
): Float64Array {
  if (values.length !== nq) throw new Error(`Expected ${nq} qpos values, got ${values.length}`);
  const pose = Float64Array.from(values);
  if (!pose.every(Number.isFinite)) throw new Error('Pose values must be finite');
  for (let j = 0; j < jointTypes.length; j++) {
    const type = jointTypes[j];
    if (type !== 0 && type !== 1) continue; // MuJoCo free and ball joints.
    const start = addresses[j] + (type === 0 ? 3 : 0);
    const norm = Math.hypot(...pose.subarray(start, start + 4));
    if (norm < 1e-12) throw new Error('Pose has a zero quaternion');
    for (let i = start; i < start + 4; i++) pose[i] /= norm;
  }
  return pose;
}
