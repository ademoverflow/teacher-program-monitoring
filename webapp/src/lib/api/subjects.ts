import { z } from "zod";
import { apiGet } from "@/lib/api/client";
import { domainRefSchema, subjectRefSchema } from "@/lib/api/shared";

/** A matière and the domaines under it — what the programme filters are built from. */
export const subjectWithDomainsSchema = subjectRefSchema.extend({
	domains: z.array(domainRefSchema),
});
export type SubjectWithDomains = z.infer<typeof subjectWithDomainsSchema>;

export function getSubjects(): Promise<SubjectWithDomains[]> {
	return apiGet("/subjects", z.array(subjectWithDomainsSchema));
}
