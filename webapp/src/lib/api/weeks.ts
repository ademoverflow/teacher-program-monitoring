import { z } from "zod";
import { periodRefSchema } from "@/lib/api/calendar";
import { apiGet } from "@/lib/api/client";
import {
	plannedSessionSummarySchema,
	slotSummarySchema,
	weekdaySchema,
} from "@/lib/api/shared";

/**
 * One cellule of the semaine grid: a créneau, and the 0, 1 or 2 séances planned in it.
 *
 * Two séances mean a commun créneau a per-niveau méthodo splits (ADR-0010) — one CM1, one
 * CM2, drawn stacked in the same box. That is not the same thing as the hours where the
 * EDT itself holds two créneaux (mardi 11h30, jeudi 11h30, jeudi 15h00): those are two
 * cellules side by side. None at all means a jour chômé, or a créneau left unplanned.
 */
export const weekCellSchema = z.object({
	slot: slotSummarySchema,
	sessions: z.array(plannedSessionSummarySchema),
});
export type WeekCell = z.infer<typeof weekCellSchema>;

/** One jour of the semaine grid, with every créneau of its weekday. */
export const dayInWeekSchema = z.object({
	id: z.string(),
	date: z.string(),
	day_of_week: weekdaySchema,
	is_off: z.boolean(),
	off_reason: z.string().nullable(),
	cells: z.array(weekCellSchema),
});
export type DayInWeek = z.infer<typeof dayInWeekSchema>;

/**
 * A semaine as §4.1 prints it: the jours in columns, the créneaux in bands.
 *
 * S1 has three jours rather than four — the year opens on a mardi — so the columns come
 * from `days` and never from a constant.
 */
export const weekDetailSchema = z.object({
	number: z.number(),
	number_in_period: z.number(),
	starts_on: z.string(),
	ends_on: z.string(),
	period: periodRefSchema,
	previous_week_number: z.number().nullable(),
	next_week_number: z.number().nullable(),
	days: z.array(dayInWeekSchema),
});
export type WeekDetail = z.infer<typeof weekDetailSchema>;

export function getWeek(number: number): Promise<WeekDetail> {
	return apiGet(`/weeks/${number}`, weekDetailSchema);
}
