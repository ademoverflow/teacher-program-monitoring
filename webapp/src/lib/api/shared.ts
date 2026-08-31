import { z } from "zod";

/**
 * The shapes several responses embed, declared once.
 *
 * These mirror `core/src/core/schemas.py`, and only as far as the screens read them:
 * zod strips what is not declared, so the API may grow a field without breaking the front.
 */

/** `CM1`, `CM2`, or `commun` when the two niveaux are taught together. */
export const levelSchema = z.enum(["CM1", "CM2", "commun"]);
export type Level = z.infer<typeof levelSchema>;

/** Weekdays are numbered the way `date.isoweekday()` numbers them. Class is never on a Wednesday. */
export const weekdaySchema = z.union([
	z.literal(1),
	z.literal(2),
	z.literal(3),
	z.literal(4),
	z.literal(5),
]);
export type Weekday = z.infer<typeof weekdaySchema>;

/** A matière, with the colour the grid draws it in. */
export const subjectRefSchema = z.object({
	id: z.string(),
	code: z.string(),
	label: z.string(),
	color: z.string(),
});
export type SubjectRef = z.infer<typeof subjectRefSchema>;

/** A domaine, as it is named on a séance or in a filter. */
export const domainRefSchema = z.object({
	id: z.string(),
	code: z.string(),
	label: z.string(),
	level: levelSchema,
});
export type DomainRef = z.infer<typeof domainRefSchema>;

/**
 * One créneau of the gabarit.
 *
 * `duration_minutes` is the teaching time the cell prints and is not always
 * `ends_at - starts_at`: the vendredi calcul mental sits in the grid's 9h55-10h15 band and
 * lasts 15 minutes (ADR-0003). Place a cellule with the boundaries, print the duration.
 *
 * `subject` is null on the six alternating créneaux, which name a pair rather than a
 * matière (ADR-0002); the séance carries the one the génération resolved.
 */
export const slotSummarySchema = z.object({
	id: z.string(),
	day_of_week: weekdaySchema,
	starts_at: z.string(),
	ends_at: z.string(),
	duration_minutes: z.number(),
	label: z.string(),
	level: levelSchema,
	is_alternating: z.boolean(),
	alternation_group: z.string().nullable(),
	subject: subjectRefSchema.nullable(),
	domain: domainRefSchema.nullable(),
});
export type SlotSummary = z.infer<typeof slotSummarySchema>;

/** The séquence a séance comes from. */
export const sequenceRefSchema = z.object({
	id: z.string(),
	method: z.string(),
	level: levelSchema,
	number: z.number(),
	title: z.string(),
});
export type SequenceRef = z.infer<typeof sequenceRefSchema>;

/** An item de programme, as a séance names it. */
export const programItemRefSchema = z.object({
	id: z.string(),
	level: levelSchema,
	title: z.string(),
	subject: subjectRefSchema.nullable(),
	domain: domainRefSchema.nullable(),
});
export type ProgramItemRef = z.infer<typeof programItemRefSchema>;

/** A séance as the semaine grid draws it. */
export const plannedSessionSummarySchema = z.object({
	id: z.string(),
	date: z.string(),
	timetable_slot_id: z.string(),
	level: levelSchema,
	title: z.string(),
	status: z.string(),
	position: z.number(),
	subject: subjectRefSchema.nullable(),
	domain: domainRefSchema.nullable(),
	sequence: sequenceRefSchema.nullable(),
});
export type PlannedSessionSummary = z.infer<typeof plannedSessionSummarySchema>;
