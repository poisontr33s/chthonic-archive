import { expect, test } from "bun:test";
import manifest from "../package.json";

test("extension stays Rust-native and workspace-scoped", () => {
  expect(manifest.extensionKind).toEqual(["workspace"]);
  expect(manifest.dependencies).toEqual({});
  expect(manifest.contributes.configuration.properties["chthonic.provider"].enum).toContain("deepseek");
  expect(manifest.contributes.commands.some((command) => command.command === "chthonic.openTerminal")).toBe(true);
  expect(manifest.contributes.commands.some((command) => command.command === "chthonic.rollbackLastEdit")).toBe(true);
});
