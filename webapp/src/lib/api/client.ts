import type { z } from "zod";

/** Every API route lives under this prefix (forwarded to core by the Vite proxy). */
export const API_PREFIX = "/api";

/**
 * A request the API refused, carrying what it said about it.
 *
 * `detail` is FastAPI's own `{"detail": "…"}`, which this API writes in French — « L'ordre
 * doit nommer exactement les lignes du cahier journal de ce jour, une fois chacune » for a
 * partial `PUT /order`, « Cette séance n'existe pas » for a stale id. That sentence is the
 * only part of a failure the teacher can act on, so it is the `message` where there is one
 * (ADR-0027).
 *
 * Where there is none the message is still French. Pydantic's own 422 answers `detail` as a
 * **list** of field errors written in English — « String should have at least 1 character »
 * — and that is a real, reachable answer here: emptying a discipline produces it. Neither
 * that list nor a method and a URL belong on the teacher's screen (§10), so the fallback
 * says what happened in her language and `request` keeps the diagnostic for the console.
 */
export class ApiError extends Error {
	readonly status: number;
	readonly detail: string | null;
	/** `PATCH /api/journal/entries/…` — for a developer, never for the screen. */
	readonly request: string;

	constructor(status: number, request: string, detail: string | null = null) {
		super(detail ?? `Le serveur a répondu ${status}.`);
		this.name = "ApiError";
		this.status = status;
		this.detail = detail;
		this.request = request;
	}
}

/**
 * A query string parameter as a caller writes it. `undefined`, `null` and `""` are
 * dropped rather than sent: an unset filter is an absent parameter, not an empty one.
 */
export type QueryValue = string | number | null | undefined;

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

/** Read the server's own sentence out of a failed response, if it wrote one. */
async function detailOf(response: Response): Promise<string | null> {
	try {
		const body = await response.json();
		const detail = (body as { detail?: unknown })?.detail;
		return typeof detail === "string" ? detail : null;
	} catch {
		return null;
	}
}

interface RequestOptions<T> {
	method: string;
	path: string;
	/** The shape to parse the answer into. `null` for a 204, which has no body. */
	schema: z.ZodType<T> | null;
	body?: unknown;
	params?: Record<string, QueryValue>;
}

/**
 * One request, one place. Every verb goes through here so that the error is built the same
 * way whether a semaine failed to load or a bilan failed to save.
 */
async function request<T>({
	method,
	path,
	schema,
	body,
	params = {},
}: RequestOptions<T>): Promise<T> {
	const url = `${API_PREFIX}${path}${buildQuery(params)}`;
	const response = await fetch(url, {
		method,
		headers:
			body === undefined
				? { Accept: "application/json" }
				: { Accept: "application/json", "Content-Type": "application/json" },
		body: body === undefined ? undefined : JSON.stringify(body),
	});
	if (!response.ok) {
		throw new ApiError(
			response.status,
			`${method} ${url}`,
			await detailOf(response),
		);
	}
	if (schema === null) {
		return undefined as T;
	}
	return schema.parse(await response.json());
}

/** GET `/api{path}` and validate the JSON body against `schema`. */
export function apiGet<T>(
	path: string,
	schema: z.ZodType<T>,
	params: Record<string, QueryValue> = {},
): Promise<T> {
	return request({ method: "GET", path, schema, params });
}

/** POST `/api{path}`. `body` is omitted for the endpoints that take none. */
export function apiPost<T>(
	path: string,
	schema: z.ZodType<T>,
	body?: unknown,
): Promise<T> {
	return request({ method: "POST", path, schema, body: body ?? {} });
}

/** PATCH `/api{path}` — a partial update, which is how every edit of a ligne is sent. */
export function apiPatch<T>(
	path: string,
	schema: z.ZodType<T>,
	body: unknown,
): Promise<T> {
	return request({ method: "PATCH", path, schema, body });
}

/** PUT `/api{path}` — the whole of something, which is what an order is (ADR-0029). */
export function apiPut<T>(
	path: string,
	schema: z.ZodType<T>,
	body: unknown,
): Promise<T> {
	return request({ method: "PUT", path, schema, body });
}

/** DELETE `/api{path}`. The API answers 204, so there is no body to parse. */
export function apiDelete(path: string): Promise<void> {
	return request({ method: "DELETE", path, schema: null });
}

/**
 * Whether a failed request is worth trying again.
 *
 * The API answers on localhost, so a failure is either the stack being down — worth two
 * more tries while the containers come up — or an answer the server meant: a semaine that
 * does not exist will not exist on the third ask either.
 */
export function shouldRetry(attempt: number, error: Error): boolean {
	const CLIENT_ERROR = 400;
	const SERVER_ERROR = 500;
	if (
		error instanceof ApiError &&
		error.status >= CLIENT_ERROR &&
		error.status < SERVER_ERROR
	) {
		return false;
	}
	return attempt < 2;
}
