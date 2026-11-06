import { describe, expect, it } from 'vitest';
import { validatedPose } from './pose';

describe('kinematic pose validation', () => {
  it('normalizes free and ball rotations without changing input or hinge angles', () => {
    const source = [1, 2, 3, 2, 0, 0, 0, .4, 0, 0, 0, 3];
    const pose = validatedPose(source, 12, [0, 3, 1], [0, 7, 8]);
    expect(Array.from(pose)).toEqual([1, 2, 3, 1, 0, 0, 0, .4, 0, 0, 0, 1]);
    expect(source[3]).toBe(2);
  });
  it('rejects invalid states before a caller can write them', () => {
    expect(() => validatedPose([1], 7, [0], [0])).toThrow('Expected 7');
    expect(() => validatedPose([0,0,0,1,NaN,0,0], 7, [0], [0])).toThrow('finite');
    expect(() => validatedPose([0,0,0,0,0,0,0], 7, [0], [0])).toThrow('zero quaternion');
  });
});
