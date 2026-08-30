# Teacher Program Monitoring

A local, single-user application for a French primary-school teacher running a double-level
CM1-CM2 class through the 2026-2027 school year (zone C). It holds the year's plan, the
official curriculum, and the daily teaching journal.

The domain language is French: the teacher's vocabulary is the source of truth. Code
identifiers are English (see §10 of `MASTER-PROMPT.md`), so each term below gives the French
domain word first and the English identifier used in code and in the database.

## Language

### The year and its calendar

**Année scolaire** (`school_year`):
The 2026-2027 school year for zone C, running from the pupils' first day to the start of the
summer holidays.
_Avoid_: academic year, term (in the American sense)

**Période** (`period`):
One of the five teaching blocks P1…P5 separated by school holidays. A période is the unit the
teacher plans against and the unit the curriculum is spread over.
_Avoid_: term, trimester, semester, half-term

**Vacances** (`school_holiday`):
A named stretch of days between two périodes (or after the last one) when there is no class.
_Avoid_: break, recess — "récréation" already means the mid-morning break

**Semaine** (`week`):
A week of class, running Monday to Friday. Every semaine has a number global to the year
(S1…S36) and a number relative to its période (P2-S3).
_Avoid_: week number in the ISO sense — the numbering here is the teacher's, not ISO 8601

**Jour de classe** (`school_day`):
A Monday, Tuesday, Thursday or Friday falling inside a période. There is never class on a
Wednesday. A jour de classe that falls on a public holiday or a bridge day is still a jour de
classe, marked as **chômé** — it keeps its place in the week so the plan can account for it.
_Avoid_: working day, weekday

**Chômé** (`is_off`):
The mark on a jour de classe cancelled by a public holiday or a bridge day.
_Avoid_: closed, cancelled, holiday — "vacances" is the school-holiday stretch, this is a
single lost day inside a période

### The timetable and what fills it

**Créneau** (`timetable_slot`):
One cell of the weekly timetable template: a day of the week, a time range, and what is taught
in it. The créneau repeats identically every week of the year and never moves — the timetable
(§4.1) is immutable.
_Avoid_: time slot, period (that word is taken), lesson

**Alternance** (`alternation`):
The rule that a shared créneau rotates between two matières — Histoire ↔ Géographie, Arts
plastiques ↔ Éducation musicale. Créneaux that alternate name the pair they rotate within
rather than a single matière; which one falls on a given week is decided when the year is
generated, not by the timetable itself.
_Avoid_: rotation, swap, split — "split" means something else here

**Créneau splitté** (a créneau whose **niveau** is CM1 or CM2):
A time range where the two levels do different things, so the same cell of the timetable is two
créneaux — one per niveau — running at the same time.

**Niveau** (`level`):
`CM1`, `CM2`, or `commun` when the two levels are taught together.
_Avoid_: grade, year group, class

**Séance** (`planned_session`):
One instance of a créneau on one jour de classe: what is actually taught that day in that slot,
with its title, objectives and materials.
_Avoid_: lesson, class, session (unqualified)

**Séquence** (`sequence`):
A run of séances from a teaching method covering one notion, spread over consecutive weeks
(e.g. maths CM1 séquence 12, "Addition et soustraction de nombres décimaux").
_Avoid_: unit, module, chapter

**Matière** (`subject`):
A school subject: Français, Mathématiques, Histoire, Sciences et technologie, EPS…
_Avoid_: discipline — that word names the free-text label of a cahier journal line

**Domaine** (`domain`):
A subdivision of a matière as the official curriculum cuts it up: Mathématiques → Nombres,
Calcul mental, Grandeurs et mesures; Français → Grammaire, Conjugaison, Lecture…
_Avoid_: topic, area, strand

**Item de programme** (`program_item`):
One institutional learning objective from the official CM1/CM2 curriculum, attributed to a
niveau, a matière and a domaine, and traceable back to its page in the source document.
_Avoid_: standard, competency, learning outcome

### The daily journal

**Cahier journal** (`journal_entries` for one jour de classe):
The teacher's record of one day, as an ordered list of lines. It starts as a copy of that day's
séances and then lives its own life — lines are edited, reordered, added and removed to say what
actually happened.
_Avoid_: logbook, diary, daybook

**Ligne de cahier journal** (`journal_entry`):
One line of the cahier journal: a discipline and a duration, the objectives and competences, and
the **bilan**.
_Avoid_: entry (unqualified), row, item

**Bilan** (`bilan`):
The teacher's after-the-fact note on a ligne de cahier journal: how it went, what to pick up next
time.
_Avoid_: review, assessment, evaluation — none of these carry the "written after the lesson"
sense

**Révision IA** (`journal_revision`):
A change to a day's cahier journal proposed by the AI in response to the teacher's free-text
feedback. A révision is proposed, then applied or rejected — never applied on its own.
_Avoid_: suggestion, AI edit, patch
