import { Link } from "@tanstack/react-router";
import { LevelBadge } from "@/components/LevelBadge";
import { SubjectLine } from "@/components/SubjectLine";
import type { PlannedSessionDetail } from "@/lib/api/days";
import { sessionSubject, subjectStyle } from "@/lib/colors";
import { formatDuration, formatTime } from "@/lib/dates";

/**
 * « Programmation du jour » — the séances the cahier journal was copied from, read-only.
 *
 * A ligne copies the discipline, the durée and the objectifs and stops there (ADR-0021).
 * The séquence, the séance de séquence, the items de programme and the matériel live only
 * on the séance, and this is where the teacher reads them — before the lesson, and while
 * writing the bilan after it.
 *
 * What is deliberately *not* here is the séance's `objectives`: a ligne already carries
 * them, so printing them again would make this panel a second copy of the table above it
 * rather than what the table leaves out. On a rituel they are the items de programme said
 * twice over (ADR-0015), and the chips below are the ones that lead anywhere.
 *
 * The statut is set on the ligne (ADR-0031); here it is only named, so there is one place
 * to write it and no doubt which one.
 */

interface DayProgrammeProps {
	sessions: PlannedSessionDetail[];
}

export function DayProgramme({ sessions }: DayProgrammeProps) {
	return (
		<ul aria-label="Programmation du jour" className="space-y-2">
			{sessions.map((session) => (
				<li
					key={session.id}
					style={subjectStyle(sessionSubject(session, session.slot))}
					className="rounded border-s-4 p-3"
				>
					<div className="flex flex-wrap items-baseline justify-between gap-2">
						<p className="text-xs tabular-nums text-slate-600">
							{formatTime(session.slot.starts_at)} –{" "}
							{formatTime(session.slot.ends_at)} ·{" "}
							{formatDuration(session.slot.duration_minutes)}
						</p>
						<span className="flex items-center gap-2">
							<LevelBadge level={session.level} />
							<StatusChip status={session.status} />
						</span>
					</div>

					<p className="mt-1 font-medium leading-snug">{session.title}</p>
					<SubjectLine subject={session.subject} domain={session.domain} />

					{session.sequence !== null && (
						<p className="mt-1 text-xs text-slate-600">
							{session.sequence.method} · séquence {session.sequence.number}
							{session.sequence_session !== null && (
								<> · étape {session.sequence_session.number}</>
							)}
						</p>
					)}

					{session.materials !== null && (
						<p className="mt-1 text-xs text-slate-600">
							Matériel : {session.materials}
						</p>
					)}

					{session.program_items.length > 0 && (
						<ul className="mt-2 flex flex-wrap gap-1">
							{session.program_items.map((item) => (
								<li key={item.id}>
									<Link
										to="/programmes/$id"
										params={{ id: item.id }}
										className="inline-flex items-center gap-1 rounded bg-white/70 px-1.5 py-0.5 text-[0.6875rem] text-slate-700 underline-offset-2 hover:underline"
									>
										{/*
										 * The niveau, because a commun séance links the CM1 item
										 * and the CM2 one and the two often print the same
										 * intitulé (ADR-0005).
										 */}
										<LevelBadge level={item.level} hideCommun={false} />
										{item.title}
									</Link>
								</li>
							))}
						</ul>
					)}
				</li>
			))}
		</ul>
	);
}

/** The statut a séance carries, named. « planifiée » is the default and says nothing. */
function StatusChip({ status }: { status: string }) {
	if (status === "planifiée") {
		return null;
	}
	return (
		<span className="rounded bg-slate-900 px-1.5 py-px text-[0.625rem] font-medium text-white">
			{status}
		</span>
	);
}
