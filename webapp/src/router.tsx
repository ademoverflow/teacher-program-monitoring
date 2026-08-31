import {
	createRootRoute,
	createRoute,
	createRouter,
	type RouterHistory,
	redirect,
} from "@tanstack/react-router";
import { AppLayout } from "@/components/AppLayout";
import { programSearchSchema } from "@/lib/program-search";
import CurrentWeekPage from "@/pages/CurrentWeek";
import DayPage from "@/pages/Day";
import ProgramItemPage from "@/pages/ProgramItem";
import ProgramsPage from "@/pages/Programs";
import TodayPage from "@/pages/Today";
import WeekPage from "@/pages/Week";
import YearPage from "@/pages/Year";

/**
 * The route tree.
 *
 * The paths are in French (ADR-0026): the address bar is what the teacher reads, and §10's
 * « identifiants en anglais » governs the code — these components and their query keys.
 */
const rootRoute = createRootRoute({
	component: AppLayout,
});

// « Aujourd'hui » is the home page (§8 Phase 6). Every other URL the teacher may have kept
// is where Phase 5 left it (ADR-0026).
const indexRoute = createRoute({
	getParentRoute: () => rootRoute,
	path: "/",
	beforeLoad: () => {
		throw redirect({ to: "/aujourdhui" });
	},
});

const todayRoute = createRoute({
	getParentRoute: () => rootRoute,
	path: "/aujourdhui",
	component: TodayPage,
});

const dayRoute = createRoute({
	getParentRoute: () => rootRoute,
	path: "/jour/$date",
	component: DayPage,
});

const yearRoute = createRoute({
	getParentRoute: () => rootRoute,
	path: "/annee",
	component: YearPage,
});

const currentWeekRoute = createRoute({
	getParentRoute: () => rootRoute,
	path: "/semaine",
	component: CurrentWeekPage,
});

const weekRoute = createRoute({
	getParentRoute: () => rootRoute,
	path: "/semaine/$number",
	component: WeekPage,
});

const programsRoute = createRoute({
	getParentRoute: () => rootRoute,
	path: "/programmes",
	validateSearch: programSearchSchema,
	component: ProgramsPage,
});

const programItemRoute = createRoute({
	getParentRoute: () => rootRoute,
	path: "/programmes/$id",
	component: ProgramItemPage,
});

export const routeTree = rootRoute.addChildren([
	indexRoute,
	todayRoute,
	dayRoute,
	yearRoute,
	currentWeekRoute,
	weekRoute,
	programsRoute,
	programItemRoute,
]);

interface AppRouterOptions {
	/** A memory history, so a test can mount the app at a chosen URL. */
	history?: RouterHistory;
}

export function createAppRouter({ history }: AppRouterOptions = {}) {
	return createRouter({
		routeTree,
		history,
		defaultPreload: "intent",
		scrollRestoration: true,
		defaultStructuralSharing: true,
		defaultPreloadStaleTime: 0,
	});
}

declare module "@tanstack/react-router" {
	interface Register {
		router: ReturnType<typeof createAppRouter>;
	}
}
