import { expect, test } from "bun:test";
import { doctorProviders, listProviders } from "../src/providers/doctor";

test("providers list returns seeded registry entries", () => {
  const providers = listProviders();
  expect(providers.length).toBeGreaterThan(5);
  expect(providers.some((p) => p.id === "pix2text-mfr")).toBe(true);
});

test("provider doctor passes when providers disabled", () => {
  const result = doctorProviders();
  expect(result.providersEnabled).toBe(false);
  expect(result.checks.some((c) => c.name === "providers-disabled")).toBe(true);
});
