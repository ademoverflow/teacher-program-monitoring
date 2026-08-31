import type { z } from "zod";

/** Every API route lives under this prefix (forwarded to core by the Vite proxy). */
export const API_PREFIX = "/api";

export class ApiError extends Error {
	readonly status: number;

	constructor(status: number, message: string) {
		super(message);
		this.name = "ApiError";
		this.status = status;
	}
}

/**
 * A query string parameter as a caller writes it. `undefined`, `null` and `""` are
 * dropped rather than sent: an unset filter is an absent parameter, not an empty one.
 */
export type QueryValue = string | number | boolean | null | undefined;

export function buildQuery(params: Record<string, QueryValue>): string {
	const search = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value === undefined || value === null || value === "") {
			continue;
		}
		search.set(key, String(value));
	}
	const query = search.toString();
	return query === "" ? "" : `?${query}`;
}

/**
 * GET `/api{path}` and validate the JSON body against `schema`.
 *
 * This is the whole client. The write verbs belong to the screens that write (Phase 6),
 * so there is deliberately no `apiPost` here yet (ADR-0023).
 */
export async function apiGet<T>(
	path: string,
	schema: z.ZodType<T>,
	params: Record<string, QueryValue> = {},
): Promise<T> {
	const url = `${API_PREFIX}${path}${buildQuery(params)}`;
	const response = await fetch(url, {
		headers: { Accept: "application/json" },
	});
	if (!response.ok) {
		throw new ApiError(response.status, `GET ${url} → HTTP ${response.status}`);
	}
	return schema.parse(await response.json());
}
