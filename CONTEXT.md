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

**Cellule** (`WeekCell`):
One box of the semaine grid — one créneau on one jour de classe — holding the 0, 1 or 2
séances planned in it. Two séances in one cellule mean a commun créneau a méthodo splits by
niveau; two *cellules* at one hour mean the EDT itself has two créneaux there. The
distinction is what the grid draws differently: stacked inside one box, or side by side.
_Avoid_: cell, slot — « créneau » is the gabarit's row, a cellule is that row on a day

**Bande** (`GridBand`):
One row of the semaine grid: a stretch of the day that no créneau boundary cuts. The bandes
are not written down anywhere — they are derived from the créneaux' own hours, so a cellule
spans as many of them as its créneau lasts. Vendredi's 11h30-12h00 and the other jours'
11h30-12h15 are why: they overlap without matching, and only a bande finer than either can
hold both (ADR-0024).
_Avoid_: row, time slot, ligne — « créneau » is the gabarit's row

**Récréation** and **pause méridienne** (a stretch no créneau covers):
The two breaks §4.1 prints, 10h15-10h45 and 12h30-14h00. Neither is a créneau and neither
has a row in `timetable_slots`: they are the gaps the gabarit leaves, and both views find
them rather than being told where they are — the semaine grid as the bandes no créneau
covers, the printed cahier journal as the gaps between one jour's créneaux. Only their
names are written down (`lib/breaks.ts`).
_Avoid_: break, pause (unqualified) — « vacances » is the school-holiday stretch. The code
does say `break` (`GridBand.isBreak`, `findBreaks`), and it means the *general* thing —
any stretch of a jour no créneau covers. The two this EDT has are la récréation and la
pause méridienne, and those are the words for them.

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
A run of séances from a méthodo covering one notion, spread over consecutive weeks
(e.g. maths CM1 séquence 12, "Addition et soustraction de nombres décimaux").
_Avoid_: unit, module, chapter

**Méthodo** (`method`):
The published teaching method a séquence comes from, named by the string every séquence of
it carries: `maths-cm1`, `maths-cm2`, `retz-cm1`, `retz-cm2`, `litterature`. A méthodo
numbers its own séquences from 1, and that number is how the teacher refers to them.
_Avoid_: curriculum, programme — those name the institutional text, not a publisher's course

**Œuvre** (a séquence of the `litterature` méthodo):
A book read with the class over several semaines. The literature méthodo is a list of œuvres
rather than of notions, so an œuvre *is* a séquence: "Charlie et la chocolaterie" is séquence 1.
_Avoid_: book, text, reading

**Programmation** (`planning`):
The whole year's séances, worked out once from the calendar, the EDT and the méthodos.
The teacher can regenerate it, in whole or by période, and it is deterministic: the same
inputs always give the same year.
_Avoid_: schedule, timetable — « emploi du temps » is the weekly gabarit, this is the
year filled in against it

**Rituel** (a créneau of twenty minutes or less):
A short cell that comes back every day at the same time — l'accueil, le calcul mental, la
lecture offerte, la dictée du jour. A rituel repeats rather than progresses: it works the
same items de programme all year, where a longer créneau walks through them.
_Avoid_: routine, warm-up

**Progression** (how a séquence or a programme is spread over the year):
The order a méthodo numbers its séquences in, or the order the programme officiel prints
its items in, laid over the year's créneaux of that matière so that each créneau knows
what it is working on. The order is the source's; the pace is the generator's.
_Avoid_: schedule, curriculum map

**Marge** (the semaine the year has over the méthodo):
The 36th semaine, which no maths séquence reaches because the méthodo has 35. §4.2 gives
it to « révisions/bilans/fin des œuvres ».
_Avoid_: buffer, spare week

**Repli** (an œuvre §4.5 keeps in reserve):
« Hansel et Gretel (repli en P5 si manque de temps) » — an œuvre read only if the year
leaves room for it, and the first thing dropped when it does not.
_Avoid_: backup, optional

**Séance de séquence** (`sequence_session`):
One step of a séquence as its méthodo prints it — a numbered week of an œuvre, with what to do
and what it needs. It is a template, not a plan: it says what the méthodo lays out, never which
day it lands on. Turning one into a séance is the generator's job.
_Avoid_: lesson plan, template session

**Matière** (`subject`):
A school subject: Français, Mathématiques, Histoire, Sciences et technologie, EPS…
_Avoid_: discipline — that word names the free-text label of a cahier journal line

**Domaine** (`domain`):
A subdivision of a matière as the official curriculum cuts it up: Mathématiques → Nombres,
Calcul mental, Grandeurs et mesures; Français → Grammaire, Conjugaison, Lecture…
_Avoid_: topic, area, strand

**Item de programme** (`program_item`):
One block of the official CM1/CM2 curriculum — the heading the source prints and the
objectives it lists under it — attributed to a niveau, a matière and a domaine, and traceable
back to its page in the source document. Those four attributions are also what identifies it:
two blocks with the same intitulé are the same item only if they sit at the same niveau, in
the same matière and in the same domaine.
_Avoid_: standard, competency, learning outcome

**Thème** (an item de programme of histoire or géographie):
The unit the histoire-géographie programme is written in, and the unit it plans in: "Thème 1 :
La vie quotidienne au Moyen Âge (XIe - XIIIe siècles) (première et deuxième période)". A thème
names the périodes it should occupy, which no other matière's programme does.
_Avoid_: topic, chapter, unit

### The daily journal

**Cahier journal** (`journal_entries` for one jour de classe):
The teacher's record of one day, as an ordered list of lines. It starts as a copy of that day's
séances and then lives its own life — lines are edited, reordered, added and removed to say what
actually happened.
_Avoid_: logbook, diary, daybook

**Ligne de cahier journal** (`journal_entry`):
One line of the cahier journal: a discipline and a duration, the objectives and competences, and
the **bilan**. A ligne points at the séance it was copied from, or at nothing when the
teacher wrote it herself — which is why a statut can be set from some lignes and not others
(ADR-0031).
_Avoid_: entry (unqualified), row, item

**Discipline** (`discipline`):
The free-text heading of a ligne de cahier journal — « Grammaire », « Calcul mental »,
« Anglais ». It starts as the créneau's own label and is the teacher's to rewrite; it names
what she did, not what the timetable calls it.
_Avoid_: matière, subject — a matière is a row of `subjects`, a discipline is a line of text

**Bilan** (`bilan`):
The teacher's after-the-fact note on a ligne de cahier journal: how it went, what to pick up next
time.
_Avoid_: review, assessment, evaluation — none of these carry the "written after the lesson"
sense

**Rapport de validation** (`GenerationReport`):
What one run of the generation says it did — séances written, séquences placed,
alternances counted — and everything it could not do. The EDT is immutable, so a
placement that does not fit is reported here rather than worked around.
_Avoid_: log, summary, errors

**Période entamée** (`is_started`):
A période holding at least one jour de classe the generation would refuse to write over —
one that is past, or one a cahier journal already holds. Regenerating such a période needs
the teacher's explicit word, because the days it *would* rewrite are days she has already
started teaching towards.
_Avoid_: current period, active period — a période the teacher has looked ahead in is
entamée whether or not today falls inside it

**Révision IA** (`journal_revision`):
A change to a day's cahier journal proposed by the AI in response to the teacher's free-text
feedback. A révision is proposed, then applied or rejected — never applied on its own.
_Avoid_: suggestion, AI edit, patch
