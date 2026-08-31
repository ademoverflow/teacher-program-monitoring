import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Vitest runs without global test hooks, so Testing Library's own auto-cleanup never
// registers: without this, one test's DOM is still mounted while the next one queries.
afterEach(cleanup);
