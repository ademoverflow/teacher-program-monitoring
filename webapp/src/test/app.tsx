import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryHistory, RouterProvider } from "@tanstack/react-router";
import { render } from "@testing-library/react";
import { vi } from "vitest";
import { createAppRouter } from "@/router";

/**
 * Mount the real router at a chosen URL, over a `fetch` that answers from frozen
 * responses. What is tested is what the teacher's browser would do — routing, query keys
 * and rendering — with the network replaced and nothing else.
 */

/** What a stubbed route answers: a body, or a body with the status the API would send. */
export type StubbedRoute =
	| unknown
	| { status: number; body?: unknown }
	| ((request: StubbedRequest) => unknown);

/** The request a route function is given, with its body already parsed. */
export interface StubbedRequest {
	method: string;
	url: string;
	body: unknown;
}

/**
 * Answer `/api/...` from a table of route to body.
 *
 * A key is `"METHOD /path"`; a key with no method means `GET`, which is how every read
 * test writes one. A value may be a body, a `{ status, body }` so a test can drive a 400,
 * or a function of the request — which is how a `PATCH` answers with what it was sent.
 *
 * Both sides are normalised — the query string is sorted — so a test states the parameters
 * it expects without depending on the order the client happens to write them in.
 */
export function stubApi(routes: Record<string, StubbedRoute>) {
	const table = new Map(
		Object.entries(routes).map(([route, answer]) => [normalise(route), answer]),
	);
	const fetchMock = vi.fn(
		async (input: RequestInfo | URL, init?: RequestInit) => {
			const method = (init?.method ?? "GET").toUpperCase();
			const url = String(input);
			const answer = table.get(normalise(`${method} ${url}`));
			if (answer === undefined) {
				return response(404, { detail: `${method} ${url}` });
			}
			const body =
				typeof answer === "function"
					? (answer as (request: StubbedRequest) => unknown)({
							method,
							url,
							body:
								init?.body === undefined
									? undefined
									: JSON.parse(String(init.body)),
						})
					: answer;
			if (isStatused(body)) {
				return response(body.status, body.body ?? null);
			}
			return response(200, body);
		},
	);
	vi.stubGlobal("fetch", fetchMock);
	return fetchMock;
}

function isStatused(body: unknown): body is { status: number; body?: unknown } {
	return (
		typeof body === "object" &&
		body !== null &&
		"status" in body &&
		typeof (body as { status: unknown }).status === "number"
	);
}

function response(status: number, body: unknown) {
	const OK = 300;
	return { ok: status < OK, status, json: async () => body };
}

/** `"PATCH /api/x?b=1&a=2"` and `"/api/x?a=2&b=1"` normalise to comparable keys. */
function normalise(route: string): string {
	const [head, tail] = route.includes(" ")
		? [route.slice(0, route.indexOf(" ")), route.slice(route.indexOf(" ") + 1)]
		: ["GET", route];
	const parsed = new URL(tail, "http://webapp.test");
	parsed.searchParams.sort();
	return `${head.toUpperCase()} ${parsed.pathname}${parsed.search}`;
}

export function renderApp(initialUrl: string) {
	const router = createAppRouter({
		history: createMemoryHistory({ initialEntries: [initialUrl] }),
	});
	const queryClient = new QueryClient({
		defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
	});
	const result = render(
		<QueryClientProvider client={queryClient}>
			<RouterProvider router={router} />
		</QueryClientProvider>,
	);
	return { ...result, router };
}
