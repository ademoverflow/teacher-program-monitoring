import { describe, expect, it } from "vitest";
import { ApiError, buildQuery, shouldRetry } from "@/lib/api/client";

describe("la requête", () => {
	it("laisse tomber les filtres non renseignés", () => {
		expect(
			buildQuery({ level: "CM1", subject: undefined, q: "", offset: 0 }),
		).toBe("?level=CM1&offset=0");
		expect(buildQuery({})).toBe("");
	});
});

describe("le réessai", () => {
	it("abandonne sur une réponse que le serveur a voulue", () => {
		expect(shouldRetry(0, new ApiError(404, "aucune semaine 999"))).toBe(false);
		expect(shouldRetry(0, new ApiError(422, "numéro invalide"))).toBe(false);
	});

	it("réessaie une pile qui n'a pas fini de démarrer", () => {
		expect(shouldRetry(0, new TypeError("Failed to fetch"))).toBe(true);
		expect(shouldRetry(1, new ApiError(503, "core indisponible"))).toBe(true);
		expect(shouldRetry(2, new TypeError("Failed to fetch"))).toBe(false);
	});
});
