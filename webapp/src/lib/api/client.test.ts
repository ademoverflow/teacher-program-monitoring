import { afterEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";
import {
	ApiError,
	apiDelete,
	apiPatch,
	buildQuery,
	shouldRetry,
} from "@/lib/api/client";
import { stubApi } from "@/test/app";

afterEach(() => {
	vi.unstubAllGlobals();
});

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

describe("les verbes d'écriture", () => {
	it("envoie le corps en JSON et rend ce que le serveur a écrit", async () => {
		const fetchMock = stubApi({
			"PATCH /api/journal/entries/7": { id: "7", bilan: "Fait" },
		});

		const written = await apiPatch(
			"/journal/entries/7",
			z.object({ id: z.string(), bilan: z.string() }),
			{ bilan: "Fait" },
		);

		expect(written).toEqual({ id: "7", bilan: "Fait" });
		const [, init] = fetchMock.mock.calls[0];
		expect(init?.method).toBe("PATCH");
		expect(init?.body).toBe('{"bilan":"Fait"}');
	});

	it("ne cherche pas de corps dans le 204 d'une suppression", async () => {
		stubApi({ "DELETE /api/journal/entries/7": { status: 204 } });

		await expect(apiDelete("/journal/entries/7")).resolves.toBeUndefined();
	});

	it("porte la phrase que le serveur a écrite, en français (ADR-0027)", async () => {
		const detail =
			"L'ordre doit nommer exactement les lignes du cahier journal de ce jour, une fois chacune";
		stubApi({
			"PATCH /api/journal/entries/7": { status: 400, body: { detail } },
		});

		const failure = await apiPatch(
			"/journal/entries/7",
			z.object({}),
			{},
		).catch((error: unknown) => error as ApiError);

		expect(failure).toBeInstanceOf(ApiError);
		expect((failure as ApiError).status).toBe(400);
		expect((failure as ApiError).detail).toBe(detail);
		expect((failure as ApiError).message).toBe(detail);
	});

	it("parle français quand le serveur n'écrit pas de phrase", async () => {
		stubApi({ "PATCH /api/journal/entries/7": { status: 500, body: null } });

		const failure = await apiPatch(
			"/journal/entries/7",
			z.object({}),
			{},
		).catch((error: unknown) => error as ApiError);

		expect((failure as ApiError).detail).toBeNull();
		expect((failure as ApiError).message).toBe("Le serveur a répondu 500.");
		// The method and the URL are kept, for the console and not for the teacher.
		expect((failure as ApiError).request).toBe("PATCH /api/journal/entries/7");
	});

	it("ne montre pas la liste anglaise d'un 422 de Pydantic", async () => {
		// The shape FastAPI really answers with when a discipline is emptied — a list of
		// field errors written in English, which is not a sentence for the teacher.
		stubApi({
			"PATCH /api/journal/entries/7": {
				status: 422,
				body: {
					detail: [
						{
							type: "string_too_short",
							loc: ["body", "discipline"],
							msg: "String should have at least 1 character",
						},
					],
				},
			},
		});

		const failure = await apiPatch(
			"/journal/entries/7",
			z.object({}),
			{},
		).catch((error: unknown) => error as ApiError);

		expect((failure as ApiError).detail).toBeNull();
		expect((failure as ApiError).message).toBe("Le serveur a répondu 422.");
	});
});
