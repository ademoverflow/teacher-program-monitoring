import { z } from "zod";
import { apiGet } from "@/lib/api/client";
import { weekdaySchema } from "@/lib/api/shared";

/** A semaine as the year view lists it. `days_off` counts its jours chômés (ADR-0001). */
export const weekSummarySchema = z.object({
	number: z.number(),
	number_in_period: z.number(),
	starts_on: z.string(),
	ends_on: z.string(),
	days_off: z.number(),
});
export type WeekSummary = z.infer<typeof weekSummarySchema>;

export const periodRefSchema = z.object({
	id: z.string(),
	code: z.string(),
	label: z.string(),
	starts_on: z.string(),
	ends_on: z.string(),
});
export type PeriodRef = z.infer<typeof periodRefSchema>;

export const periodSummarySchema = periodRefSchema.extend({
	weeks: z.array(weekSummarySchema),
});
export type PeriodSummary = z.infer<typeof periodSummarySchema>;

/** A stretch of vacances. `ends_on` is open for the summer. */
export const holidaySchema = z.object({
	label: z.string(),
	starts_on: z.string(),
	ends_on: z.string().nullable(),
});
export type Holiday = z.infer<typeof holidaySchema>;

/** The whole année scolaire in one response — §7 écran 1. */
export const yearOverviewSchema = z.object({
	label: z.string(),
	zone: z.string(),
	starts_on: z.string(),
	ends_on: z.string(),
	today: z.string(),
	current_week_number: z.number().nullable(),
	periods: z.array(periodSummarySchema),
	holidays: z.array(holidaySchema),
});
export type YearOverview = z.infer<typeof yearOverviewSchema>;

/** A jour de classe and where it sits in the year. A jour chômé keeps its row (ADR-0001). */
export const dayRefSchema = z.object({
	id: z.string(),
	date: z.string(),
	day_of_week: weekdaySchema,
	is_off: z.boolean(),
	off_reason: z.string().nullable(),
	week_number: z.number(),
	number_in_period: z.number(),
	period_code: z.string(),
});
export type DayRef = z.infer<typeof dayRefSchema>;

/**
 * Where the teacher is in the year right now.
 *
 * `school_day` is today when today is a jour de classe — a jour chômé included, with its
 * motif. `next_taught_day` is the jour to open, and is null once the year is over.
 */
export const todaySchema = z.object({
	date: z.string(),
	school_day: dayRefSchema.nullable(),
	next_taught_day: dayRefSchema.nullable(),
});
export type Today = z.infer<typeof todaySchema>;

export function getYear(): Promise<YearOverview> {
	return apiGet("/calendar", yearOverviewSchema);
}

export function getToday(): Promise<Today> {
	return apiGet("/calendar/today", todaySchema);
}
