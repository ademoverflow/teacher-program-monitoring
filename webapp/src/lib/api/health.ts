import { z } from "zod";
import { apiGet } from "@/lib/api/client";

export const healthSchema = z.object({
	status: z.string(),
	uptime: z.number(),
	version: z.string(),
});
export type Health = z.infer<typeof healthSchema>;

export function getHealth(): Promise<Health> {
	return apiGet("/health", healthSchema);
}
