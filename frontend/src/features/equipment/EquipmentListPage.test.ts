import { describe, expect, it } from "vitest";

import { formatStatus } from "./EquipmentListPage";


describe("formatStatus", () => {
  it("converte o código técnico em texto legível", () => {
    expect(formatStatus("AGUARDANDO_TRIAGEM")).toBe("Aguardando triagem");
  });
});
