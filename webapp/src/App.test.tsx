import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

function renderApp() {
	const queryClient = new QueryClient({
		defaultOptions: { queries: { retry: false } },
	});
	return render(
		<QueryClientProvider client={queryClient}>
			<App />
		</QueryClientProvider>,
	);
}

function mockFetch(body: unknown, { ok = true, status = 200 } = {}) {
	const fetchMock = vi.fn().mockResolvedValue({
		ok,
		status,
		json: async () => body,
	});
	vi.stubGlobal("fetch", fetchMock);
	return fetchMock;
}

afterEach(() => {
	vi.unstubAllGlobals();
});

describe("App", () => {
	it("affiche l'état renvoyé par GET /api/health", async () => {
		const fetchMock = mockFetch({
			status: "ok",
			uptime: 12.5,
			version: "0.0.0",
		});
		renderApp();

		expect(await screen.findByText("ok")).toBeTruthy();
		expect(screen.getByText("0.0.0")).toBeTruthy();
		expect(screen.getByText("13 s")).toBeTruthy();
		expect(fetchMock).toHaveBeenCalledWith("/api/health", expect.anything());
	});

	it("signale une API injoignable", async () => {
		mockFetch({ detail: "down" }, { ok: false, status: 503 });
		renderApp();

		const alert = await screen.findByRole("alert");
		expect(alert.textContent).toContain("API injoignable");
		expect(alert.textContent).toContain("503");
	});
});
