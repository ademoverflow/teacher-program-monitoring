import { z } from "zod";
import { levelSchema } from "@/lib/api/shared";

/** `schemas.PAGE_SIZE` — what one page of `GET /api/program-items` holds. */
export const PAGE_SIZE = 50;

/**
 * The filter state of §7 écran 4, kept in the URL.
 *
 * The parameter names are French like the rest of the address bar (ADR-0026); the API's
 * own names stay English, and `Programs.tsx` is where the two meet.
 */
export const programSearchSchema = z.object({
	q: z.string().min(1).optional(),
	niveau: levelSchema.optional(),
	matiere: z.string().min(1).optional(),
	domaine: z.string().min(1).optional(),
	page: z.number().int().min(1).catch(1).default(1),
});

export type ProgramSearch = z.infer<typeof programSearchSchema>;
