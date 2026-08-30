import { z } from "zod";

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

/** GET `/api{path}` and validate the JSON body against `schema`. */
export async function apiGet<T>(
	path: string,
	schema: z.ZodType<T>,
): Promise<T> {
	const url = `${API_PREFIX}${path}`;
	const response = await fetch(url, {
		headers: { Accept: "application/json" },
	});
	if (!response.ok) {
		throw new ApiError(response.status, `GET ${url} → HTTP ${response.status}`);
	}
	return schema.parse(await response.json());
}

export const healthSchema = z.object({
	status: z.string(),
	uptime: z.number(),
	version: z.string(),
});
export type Health = z.infer<typeof healthSchema>;

export function getHealth(): Promise<Health> {
	return apiGet("/health", healthSchema);
}
