import { Link, Outlet } from "@tanstack/react-router";
import { BookOpen, CalendarDays, LayoutGrid, Sun } from "lucide-react";
import type { ComponentType } from "react";
import { ApiStatus } from "@/components/ApiStatus";

interface NavItem {
	to: string;
	label: string;
	icon: ComponentType<{ className?: string; "aria-hidden"?: boolean }>;
}

/**
 * §7 asks for « Année · Semaine · Aujourd'hui · Programmes · Réglages ». Four of the five
 * are here. « Réglages » holds écran 5, la génération, which §8 assigns to no phase and
 * which can rewrite the year; it arrives with the screen that fills it, rather than as a
 * link to nothing.
 */
const NAV: NavItem[] = [
	{ to: "/aujourdhui", label: "Aujourd'hui", icon: Sun },
	{ to: "/annee", label: "Année", icon: CalendarDays },
	{ to: "/semaine", label: "Semaine", icon: LayoutGrid },
	{ to: "/programmes", label: "Programmes", icon: BookOpen },
];

export function AppLayout() {
	return (
		<div className="flex min-h-screen bg-slate-50 text-slate-900 print:block print:min-h-0 print:bg-white">
			<nav
				aria-label="Navigation principale"
				className="sticky top-0 flex h-screen w-52 shrink-0 flex-col border-r border-slate-200 bg-white print:hidden"
			>
				<div className="border-b border-slate-200 px-4 py-4">
					<p className="text-sm font-semibold leading-tight">
						Suivi de programme
					</p>
					<p className="text-xs text-slate-500">CM1-CM2 · 2026-2027</p>
				</div>

				<ul className="flex-1 space-y-1 p-2">
					{NAV.map((item) => (
						<li key={item.to}>
							<Link
								to={item.to}
								className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-slate-600 hover:bg-slate-100"
								activeProps={{
									className:
										"flex items-center gap-2 rounded-md px-3 py-2 text-sm bg-slate-900 text-white hover:bg-slate-900",
								}}
							>
								<item.icon className="size-4" aria-hidden={true} />
								{item.label}
							</Link>
						</li>
					))}
				</ul>

				<div className="border-t border-slate-200 px-4 py-3">
					<ApiStatus />
				</div>
			</nav>

			<main className="min-w-0 flex-1">
				<Outlet />
			</main>
		</div>
	);
}
