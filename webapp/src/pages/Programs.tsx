import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useSearch } from "@tanstack/react-router";
import { Search, TriangleAlert } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Empty } from "@/components/Empty";
import { LevelBadge } from "@/components/LevelBadge";
import { LoadFailure } from "@/components/LoadFailure";
import { Loading } from "@/components/Loading";
import { SubjectLine } from "@/components/SubjectLine";
import type { DomainRef, ProgramItem, SubjectWithDomains } from "@/lib/api";
import { getSubjects, searchProgramItems } from "@/lib/api";
import { plural } from "@/lib/plural";
import type { ProgramSearch } from "@/lib/program-search";
import { PAGE_SIZE } from "@/lib/program-search";

/**
 * §7 écran 4 — the programmes officiels, filtered and searched.
 *
 * The filters live in the URL, so a filtered list is a link the teacher can keep. The
 * recherche is Postgres' own (`websearch_to_tsquery('french', …)`): the input is debounced
 * and sent, and nothing is filtered or re-sorted here on top of the answer.
 */
export default function ProgramsPage() {
	const search = useSearch({ from: "/programmes" });
	const navigate = useNavigate({ from: "/programmes" });
	const subjects = useQuery({ queryKey: ["subjects"], queryFn: getSubjects });

	const page = useQuery({
		queryKey: ["program-items", search],
		queryFn: () =>
			searchProgramItems({
				level: search.niveau,
				subject: search.matiere,
				domain: search.domaine,
				q: search.q,
				limit: PAGE_SIZE,
				offset: (search.page - 1) * PAGE_SIZE,
			}),
	});

	// Stable across renders: the debounce in `Filters` holds on to it.
	const setSearch = useCallback(
		(patch: Partial<ProgramSearch>): void => {
			navigate({
				search: (previous) => ({
					...previous,
					...patch,
					page: patch.page ?? 1,
				}),
				replace: true,
			});
		},
		[navigate],
	);

	return (
		<div className="p-6">
			<header className="mb-4">
				<h1 className="text-2xl font-semibold">Programmes officiels</h1>
				<p className="mt-1 text-sm text-slate-500">
					CM1 et CM2 ·{" "}
					{page.data === undefined
						? "…"
						: `${page.data.total} ${plural(page.data.total, "item")}`}{" "}
					pour ces filtres
				</p>
			</header>

			<Filters
				search={search}
				subjects={subjects.data ?? []}
				onChange={setSearch}
			/>

			{page.isPending && <Loading label="Recherche…" />}
			{page.isError && (
				<LoadFailure error={page.error} what="les items de programme" />
			)}
			{page.isSuccess &&
				(page.data.items.length === 0 ? (
					<Empty>Aucun item de programme ne correspond à ces filtres.</Empty>
				) : (
					<>
						<ul aria-label="Items de programme" className="space-y-2">
							{page.data.items.map((item) => (
								<li key={item.id}>
									<ItemRow item={item} />
								</li>
							))}
						</ul>
						<Pager
							total={page.data.total}
							page={search.page}
							onChange={(next) => setSearch({ page: next })}
						/>
					</>
				))}
		</div>
	);
}

interface FiltersProps {
	search: ProgramSearch;
	subjects: SubjectWithDomains[];
	onChange: (patch: Partial<ProgramSearch>) => void;
}

function Filters({ search, subjects, onChange }: FiltersProps) {
	const [text, setText] = useState(search.q ?? "");

	// The URL is the source of truth: keep the box in step when a link changes it.
	useEffect(() => {
		setText(search.q ?? "");
	}, [search.q]);

	// Debounced, because every keystroke would otherwise be a full-text query.
	useEffect(() => {
		const current = search.q ?? "";
		if (text === current) {
			return;
		}
		const timer = setTimeout(() => onChange({ q: text || undefined }), 300);
		return () => clearTimeout(timer);
	}, [text, search.q, onChange]);

	const selected = subjects.find((subject) => subject.code === search.matiere);
	const domains = domainOptions(selected ? [selected] : subjects);

	return (
		<div className="mb-4 flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-3">
			<label className="flex min-w-64 flex-1 flex-col gap-1 text-xs text-slate-500">
				Recherche
				<span className="flex items-center gap-2 rounded-md border border-slate-300 px-2 py-1.5">
					<Search
						className="size-4 shrink-0 text-slate-400"
						aria-hidden="true"
					/>
					<input
						type="search"
						value={text}
						onChange={(event) => setText(event.target.value)}
						placeholder="fractions, « nombres décimaux », -géométrie…"
						className="w-full text-sm text-slate-900 outline-none"
					/>
				</span>
			</label>

			<label className="flex flex-col gap-1 text-xs text-slate-500">
				Niveau
				<select
					value={search.niveau ?? ""}
					onChange={(event) =>
						onChange({
							niveau:
								event.target.value === ""
									? undefined
									: (event.target.value as ProgramSearch["niveau"]),
						})
					}
					className="rounded-md border border-slate-300 px-2 py-1.5 text-sm text-slate-900"
				>
					<option value="">Tous</option>
					<option value="CM1">CM1</option>
					<option value="CM2">CM2</option>
					<option value="commun">Commun</option>
				</select>
			</label>

			<label className="flex flex-col gap-1 text-xs text-slate-500">
				Matière
				<select
					value={search.matiere ?? ""}
					onChange={(event) =>
						onChange({
							matiere: event.target.value || undefined,
							domaine: undefined,
						})
					}
					className="rounded-md border border-slate-300 px-2 py-1.5 text-sm text-slate-900"
				>
					<option value="">Toutes</option>
					{subjects.map((subject) => (
						<option key={subject.code} value={subject.code}>
							{subject.label}
						</option>
					))}
				</select>
			</label>

			<label className="flex flex-col gap-1 text-xs text-slate-500">
				Domaine
				<select
					value={search.domaine ?? ""}
					onChange={(event) =>
						onChange({ domaine: event.target.value || undefined })
					}
					className="rounded-md border border-slate-300 px-2 py-1.5 text-sm text-slate-900"
				>
					<option value="">Tous</option>
					{domains.map((domain) => (
						<option key={domain.code} value={domain.code}>
							{domain.label}
						</option>
					))}
				</select>
			</label>
		</div>
	);
}

/**
 * The domaines to offer, one per code.
 *
 * A code is what the API filters on, and two matières share one: arts plastiques and
 * éducation musicale both print « Compétences travaillées ». Two options with the same
 * value would be two ways to ask the same question, and a `<select>` could not tell which
 * one was picked.
 */
function domainOptions(subjects: SubjectWithDomains[]): DomainRef[] {
	const byCode = new Map<string, DomainRef>();
	for (const subject of subjects) {
		for (const domain of subject.domains) {
			if (!byCode.has(domain.code)) {
				byCode.set(domain.code, domain);
			}
		}
	}
	return [...byCode.values()];
}

interface ItemRowProps {
	item: ProgramItem;
}

function ItemRow({ item }: ItemRowProps) {
	return (
		<Link
			to="/programmes/$id"
			params={{ id: item.id }}
			className="block rounded-lg border border-slate-200 bg-white p-3 hover:border-slate-400 hover:bg-slate-50"
		>
			<div className="flex items-start justify-between gap-3">
				<h2 className="text-sm font-medium">{item.title}</h2>
				<span className="flex shrink-0 items-center gap-2">
					{item.needs_review && (
						<TriangleAlert
							className="size-4 text-amber-600"
							aria-label="Extraction à relire"
						/>
					)}
					<LevelBadge level={item.level} hideCommun={false} />
				</span>
			</div>
			<SubjectLine
				subject={item.subject}
				domain={item.domain}
				className="mt-1 text-xs text-slate-500"
			/>
			{item.description !== null && (
				<p className="mt-1 line-clamp-2 text-xs text-slate-600">
					{item.description}
				</p>
			)}
		</Link>
	);
}

interface PagerProps {
	total: number;
	page: number;
	onChange: (page: number) => void;
}

function Pager({ total, page, onChange }: PagerProps) {
	const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
	if (pages === 1) {
		return null;
	}
	return (
		<nav
			aria-label="Pagination"
			className="mt-4 flex items-center justify-center gap-3 text-sm"
		>
			<button
				type="button"
				disabled={page <= 1}
				onClick={() => onChange(page - 1)}
				className="rounded-md border border-slate-300 bg-white px-3 py-1.5 disabled:opacity-40"
			>
				Précédent
			</button>
			<span className="text-slate-500">
				Page {page} sur {pages}
			</span>
			<button
				type="button"
				disabled={page >= pages}
				onClick={() => onChange(page + 1)}
				className="rounded-md border border-slate-300 bg-white px-3 py-1.5 disabled:opacity-40"
			>
				Suivant
			</button>
		</nav>
	);
}
