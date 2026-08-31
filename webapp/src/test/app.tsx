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

/**
 * Answer `GET /api/...` from a table of URL to body.
 *
 * Both sides are normalised — the query string is sorted — so a test states the parameters
 * it expects without depending on the order the client happens to write them in.
 */
export function stubApi(routes: Record<string, unknown>) {
	const table = new Map(
		Object.entries(routes).map(([url, body]) => [normalise(url), body]),
	);
	const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
		const url = normalise(String(input));
		const body = table.get(url);
		if (body === undefined) {
			return { ok: false, status: 404, json: async () => ({ detail: url }) };
		}
		return { ok: true, status: 200, json: async () => body };
	});
	vi.stubGlobal("fetch", fetchMock);
	return fetchMock;
}

function normalise(url: string): string {
	const parsed = new URL(url, "http://webapp.test");
	parsed.searchParams.sort();
	return `${parsed.pathname}${parsed.search}`;
}

export function renderApp(initialUrl: string) {
	const router = createAppRouter({
		history: createMemoryHistory({ initialEntries: [initialUrl] }),
	});
	const queryClient = new QueryClient({
		defaultOptions: { queries: { retry: false } },
	});
	const result = render(
		<QueryClientProvider client={queryClient}>
			<RouterProvider router={router} />
		</QueryClientProvider>,
	);
	return { ...result, router };
}
