/**
 * French pluralisation: nothing takes an `s` below two, so « 0 jour », « 1 jour »,
 * « 2 jours ».
 */
export function plural(count: number, singular: string, suffix = "s"): string {
	return count > 1 ? `${singular}${suffix}` : singular;
}
