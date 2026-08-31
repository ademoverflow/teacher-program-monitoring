import { z } from "zod";
import { levelSchema } from "@/lib/api/shared";

/** `schemas.PAGE_SIZE` — what one page of `GET /api/program-items` holds. */
export const PAGE_SIZE = 50;

/**
 * The filter state of §7 écran 4, kept in the URL.
 *
 * The parameter names are French like the rest of the address bar (ADR-0026); the API's
 * own names stay English, and `Programs.tsx` is where the two meet.
 *
 * Every field falls back rather than throwing. A filtered list is a link the teacher keeps,
 * and a link that has been edited by hand — `?q=`, `?niveau=cm1` — should drop the filter
 * it cannot read, not replace the page with an error.
 */
export const programSearchSchema = z.object({
	q: z.string().min(1).optional().catch(undefined),
	niveau: levelSchema.optional().catch(undefined),
	matiere: z.string().min(1).optional().catch(undefined),
	domaine: z.string().min(1).optional().catch(undefined),
	page: z.number().int().min(1).catch(1).default(1),
});

export type ProgramSearch = z.infer<typeof programSearchSchema>;
