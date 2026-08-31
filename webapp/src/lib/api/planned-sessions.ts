import { z } from "zod";
import { apiGet, apiPatch } from "@/lib/api/client";
import {
	type PlannedSessionDetail,
	plannedSessionDetailSchema,
} from "@/lib/api/days";
import { plannedSessionSummarySchema } from "@/lib/api/shared";

/**
 * The statut of a séance, in the teacher's own words — the values `SessionStatus` holds.
 *
 * It lives on the séance and not on the ligne de cahier journal, which is why a ligne the
 * teacher wrote herself has none to show (ADR-0031).
 */
export const SESSION_STATUSES = [
	"planifiée",
	"faite",
	"reportée",
	"annulée",
] as const;
export const sessionStatusSchema = z.enum(SESSION_STATUSES);
export type SessionStatus = z.infer<typeof sessionStatusSchema>;

/** Change a séance's statut. The whole séance comes back, rendered. */
export function updateSessionStatus(
	id: string,
	status: SessionStatus,
): Promise<PlannedSessionDetail> {
	return apiPatch(`/planned-sessions/${id}`, plannedSessionDetailSchema, {
		status,
	});
}

export const plannedSessionPageSchema = z.object({
	total: z.number(),
	limit: z.number(),
	offset: z.number(),
	sessions: z.array(plannedSessionSummarySchema),
});
export type PlannedSessionPage = z.infer<typeof plannedSessionPageSchema>;

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
