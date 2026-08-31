import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { shouldRetry } from "@/lib/api/client";

export function createQueryClient(): QueryClient {
	return new QueryClient({
		defaultOptions: {
			queries: {
				retry: (attempt, error) => shouldRetry(attempt, error as Error),
			},
		},
	});
}

export function getContext() {
	return {
		queryClient: createQueryClient(),
	};
}

export function Provider({
	children,
	queryClient,
}: {
	children: React.ReactNode;
	queryClient: QueryClient;
}) {
	return (
		<QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
	);
}
