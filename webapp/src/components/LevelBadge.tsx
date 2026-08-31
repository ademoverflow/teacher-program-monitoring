import type { Level } from "@/lib/api/shared";

const STYLES: Record<Level, string> = {
	CM1: "bg-sky-700 text-white",
	CM2: "bg-violet-700 text-white",
	commun: "bg-slate-500 text-white",
};

interface LevelBadgeProps {
	level: Level;
	/** `commun` is the default and says nothing; hide it unless it is worth stating. */
	hideCommun?: boolean;
}

/** The CM1 / CM2 badge §7 écran 2 asks for on a créneau splitté. */
export function LevelBadge({ level, hideCommun = true }: LevelBadgeProps) {
	if (level === "commun" && hideCommun) {
		return null;
	}
	return (
		<span
			className={`inline-block rounded px-1 py-px text-[0.625rem] font-semibold leading-tight ${STYLES[level]}`}
		>
			{level}
		</span>
	);
}
