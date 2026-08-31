# A cahier journal fills itself for the day being taught, and waits to be asked for every other

Opening `/jour/{date}` calls `POST /api/journal/{date}/initialise` by itself when the date
is today or in the past. Every other day — tomorrow, next month, June — shows what its
programmation holds and a button, « Initialiser depuis la programmation ». A jour chômé is
never filled automatically either; it has no séance to copy.

ADR-0021 says the endpoint « can be called every time the vue jour opens », and §8 Phase 6
asks for a cahier journal « pré-initialisé depuis les séances du jour (à la première
ouverture) ». Read literally, that is: fill it on every open. We do not, and the reason is
in `planning/writer.py`.

`_untouchable_days` excludes a jour de classe from a re-generation **as soon as it holds one
ligne de cahier journal** — not merely from being overwritten, from being written at all
(ADR-0020). So initialising a day is not only a decision about that day's cahier journal:
it freezes that day's programmation. A teacher who browses forward to April to see what is
coming would, on the literal reading, silently create twelve lignes there; when she later
changes the histoire/géographie alternance (a réglage, ADR-0013) and regenerates, April
would keep the old séances and nothing would say why. That is a wrong answer arrived at
quietly, which is worse than a button.

The rule that replaces it is the one the domain already gives. A cahier journal is the
record of a day — « what actually happened » (`CONTEXT.md`), and a bilan is written *after*
the lesson. A day that has not happened has nothing to record yet. So the app fills the day
it is living in, which is the case §1's definition of success describes — « le 1er septembre
2026, l'enseignante ouvre l'app … a son cahier journal pré-rempli » — and asks for the rest.

The cost is one click on a day the teacher wants to prepare ahead, and it is visible where
the alternative was not. On 2026-08-31 that click is on the home page: the pupils come back
tomorrow, so every day of the year is still in the future.

The 201/200 distinction ADR-0021 built for this is still what makes the automatic call
safe: re-opening a day already filled is a no-op the server states, so the effect does not
depend on the front remembering anything.
