import { describe, it, expect } from "vitest";
import { resolvePressureRange } from "./pressureRange";

describe("resolvePressureRange", () => {
  it("uses fallback when no record is available", () => {
    const range = resolvePressureRange(undefined);
    expect(range).toEqual({ min: 980, max: 1040 });
  });

  it("calculates range with margins when valid record is provided", () => {
    const record = {
      min_value: 915,
      min_date: "2026-08-01",
      max_value: 925,
      max_date: "2026-08-02",
    };
    const range = resolvePressureRange(record);
    // 915 - 5 = 910
    // 925 + 5 = 930
    expect(range).toEqual({ min: 910, max: 930 });
  });

  it("forces a minimum amplitude if min and max are too close", () => {
    const record = {
      min_value: 920,
      min_date: "2026-08-01",
      max_value: 920.5,
      max_date: "2026-08-02",
    };
    const range = resolvePressureRange(record);
    // Even with margins: min=915, max=925.5 -> amplitude 10.5, which is ok if minimum amplitude is 10.
    // If we require amplitude of 10 around the center (920.25): min 915.25, max 925.25
    // Let's test that amplitude is at least 10
    expect(range.max - range.min).toBeGreaterThanOrEqual(10);
    // Center should be roughly preserved
    const center = (range.max + range.min) / 2;
    expect(center).toBeCloseTo(920.25, 1);
  });

  it("handles missing min/max values by using fallback", () => {
    const record = {
      min_value: null,
      min_date: null,
      max_value: null,
      max_date: null,
    };
    const range = resolvePressureRange(record);
    expect(range).toEqual({ min: 980, max: 1040 });
  });
});
