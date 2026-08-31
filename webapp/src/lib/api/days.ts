import { z } from "zod";
import { periodRefSchema } from "@/lib/api/calendar";
import { apiGet } from "@/lib/api/client";
import {
	plannedSessionSummarySchema,
	programItemRefSchema,
	sequenceRefSchema,
	slotSummarySchema,
	weekdaySchema,
} from "@/lib/api/shared";

/** The séance de séquence a séance instantiates — the méthodo's own numbered step. */
export const sequenceStepRefSchema = z.object({
	id: z.string(),
	number: z.number(),
	title: z.string(),
});
export type SequenceStepRef = z.infer<typeof sequenceStepRefSchema>;

/**
 * A séance with everything it says — what the vue Jour shows beside the cahier journal.
 *
 * A ligne de cahier journal copies the discipline, the durée and the objectifs and stops
 * there (ADR-0021). The séquence, la séance de séquence, les items de programme et le
 * matériel live only here, which is why the vue Jour shows the programmation as well.
 */
export const plannedSessionDetailSchema = plannedSessionSummarySchema.extend({
	school_day_id: z.string(),
	objectives: z.string().nullable(),
	content: z.string().nullable(),
	materials: z.string().nullable(),
	slot: slotSummarySchema,
	sequence: sequenceRefSchema.nullable(),
	sequence_session: sequenceStepRefSchema.nullable(),
	program_items: z.array(programItemRefSchema),
});
export type PlannedSessionDetail = z.infer<typeof plannedSessionDetailSchema>;

/**
 * A jour de classe and its séances in the order they run.
 *
 * A jour chômé answers like any other, with `is_off`, its motif and no séance: the day
 * keeps its place in the semaine so the plan can account for it (ADR-0001).
 */
export const dayDetailSchema = z.object({
	id: z.string(),
	date: z.string(),
	day_of_week: weekdaySchema,
	is_off: z.boolean(),
	off_reason: z.string().nullable(),
	week_number: z.number(),
	number_in_period: z.number(),
	period: periodRefSchema,
	previous_day: z.string().nullable(),
	next_day: z.string().nullable(),
	has_journal: z.boolean(),
	sessions: z.array(plannedSessionDetailSchema),
});
export type DayDetail = z.infer<typeof dayDetailSchema>;

export function getDay(date: string): Promise<DayDetail> {
	return apiGet(`/days/${date}`, dayDetailSchema);
}
