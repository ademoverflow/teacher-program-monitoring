import { describe, expect, it } from "vitest";
import { plural } from "@/lib/plural";

describe("le pluriel français", () => {
	it("ne met un s qu'au-delà de un", () => {
		expect(plural(0, "jour")).toBe("jour");
		expect(plural(1, "jour")).toBe("jour");
		expect(plural(2, "jour")).toBe("jours");
	});
});
