import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { ArrowLeft, FileText, TriangleAlert } from "lucide-react";
import { LevelBadge } from "@/components/LevelBadge";
import { Empty, LoadFailure, Loading } from "@/components/QueryState";
import { getLinkedSessions, getProgramItem } from "@/lib/api";
import { subjectDotStyle } from "@/lib/colors";
import { formatLongDate } from "@/lib/dates";

const LINKED_PAGE_SIZE = 20;

/** The fiche of one item de programme, with its source and the séances that work it. */
export default function ProgramItemPage() {
	const { id } = useParams({ from: "/programmes/$id" });
	const item = useQuery({
		queryKey: ["program-item", id],
		queryFn: () => getProgramItem(id),
	});
	const linked = useQuery({
		queryKey: ["program-item-sessions", id],
		queryFn: () => getLinkedSessions(id, { limit: LINKED_PAGE_SIZE }),
	});

	if (item.isPending) {
		return <Loading label="Chargement de l'item…" />;
	}
	if (item.isError) {
		return <LoadFailure error={item.error} what="cet item de programme" />;
	}

	const data = item.data;

	return (
		<div className="max-w-3xl p-6">
			<Link
				to="/programmes"
				className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-900"
			>
				<ArrowLeft className="size-4" aria-hidden="true" />
				Retour aux programmes
			</Link>

			<header className="mt-4">
				<div className="flex items-start justify-between gap-3">
					<h1 className="text-2xl font-semibold">{data.title}</h1>
					<LevelBadge level={data.level} hideCommun={false} />
				</div>
				<p className="mt-2 flex items-center gap-1.5 text-sm text-slate-500">
					<span
						style={subjectDotStyle(data.subject)}
						className="inline-block size-3 shrink-0 rounded-full border"
						aria-hidden="true"
					/>
					{data.subject?.label ?? "Sans matière"}
					{data.domain !== null && <> · {data.domain.label}</>}
				</p>
			</header>

			{data.needs_review && (
				<p className="mt-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
					<TriangleAlert
						className="mt-0.5 size-4 shrink-0"
						aria-hidden="true"
					/>
					Cet item a été extrait d'une zone difficile à lire : à vérifier contre
					la source.
				</p>
			)}

			{data.description !== null && (
				<div className="mt-4 whitespace-pre-line rounded-xl border border-slate-200 bg-white p-4 text-sm leading-relaxed">
					{data.description}
				</div>
			)}

			<p className="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
				<FileText className="size-3.5 shrink-0" aria-hidden="true" />
				{data.source_file}
				{data.source_page !== null && <> · page {data.source_page}</>}
			</p>

			<section className="mt-8">
				<h2 className="mb-2 text-lg font-semibold">Séances liées</h2>
				{linked.isPending && <Loading label="Recherche des séances…" />}
				{linked.isError && (
					<LoadFailure error={linked.error} what="les séances liées" />
				)}
				{linked.isSuccess &&
					(linked.data.total === 0 ? (
						<Empty>Aucune séance de l'année ne travaille cet item.</Empty>
					) : (
						<>
							<p className="mb-2 text-sm text-slate-500">
								{linked.data.total} séance{linked.data.total > 1 ? "s" : ""}{" "}
								dans la programmation
								{linked.data.total > linked.data.sessions.length && (
									<> · les {linked.data.sessions.length} premières</>
								)}
							</p>
							<ul
								aria-label="Séances liées"
								className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white"
							>
								{linked.data.sessions.map((session) => (
									<li
										key={session.id}
										className="flex items-baseline justify-between gap-3 px-4 py-2 text-sm"
									>
										<span className="min-w-0">
											<span className="block truncate">{session.title}</span>
											<span className="text-xs capitalize text-slate-500">
												{formatLongDate(session.date)}
											</span>
										</span>
										<LevelBadge level={session.level} />
									</li>
								))}
							</ul>
						</>
					))}
			</section>
		</div>
	);
}
