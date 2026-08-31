import { z } from "zod";
import { apiGet, type QueryValue } from "@/lib/api/client";
import {
	type Level,
	plannedSessionSummarySchema,
	programItemRefSchema,
} from "@/lib/api/shared";

/**
 * An item de programme with everything the browser shows of it.
 *
 * `needs_review` marks a block the extraction found hard to read (ADR-0007). It is shown
 * and never filtered on.
 */
export const programItemSchema = programItemRefSchema.extend({
	description: z.string().nullable(),
	source_file: z.string(),
	source_page: z.number().nullable(),
	source_order: z.number(),
	needs_review: z.boolean(),
});
export type ProgramItem = z.infer<typeof programItemSchema>;

export const programItemPageSchema = z.object({
	total: z.number(),
	limit: z.number(),
	offset: z.number(),
	items: z.array(programItemSchema),
});
export type ProgramItemPage = z.infer<typeof programItemPageSchema>;

export const plannedSessionPageSchema = z.object({
	total: z.number(),
	limit: z.number(),
	offset: z.number(),
	sessions: z.array(plannedSessionSummarySchema),
});
export type PlannedSessionPage = z.infer<typeof plannedSessionPageSchema>;

export interface ProgramItemQuery {
	level?: Level | null;
	subject?: string | null;
	domain?: string | null;
	q?: string | null;
	limit?: number;
	offset?: number;
}

/**
 * Filter and search the items de programme.
 *
 * `q` goes to `websearch_to_tsquery('french', …)` server-side — it stems, and it honours
 * quoted phrases and `-mot`. Nothing is filtered or re-sorted on top of the answer:
 * without `q` the items come in the source's order, with one they come by rank.
 */
export function searchProgramItems(
	query: ProgramItemQuery,
): Promise<ProgramItemPage> {
	return apiGet("/program-items", programItemPageSchema, {
		...query,
	} as Record<string, QueryValue>);
}

export function getProgramItem(id: string): Promise<ProgramItem> {
	return apiGet(`/program-items/${id}`, programItemSchema);
}

/** How many linked séances a fiche shows before saying how many more there are. */
export const LINKED_SESSIONS_SHOWN = 20;

/** The séances linked to one item de programme — §7 écran 4's « voir les séances liées ». */
export function getLinkedSessions(
	programItemId: string,
): Promise<PlannedSessionPage> {
	return apiGet("/planned-sessions", plannedSessionPageSchema, {
		program_item_id: programItemId,
		limit: LINKED_SESSIONS_SHOWN,
		offset: 0,
	});
}
