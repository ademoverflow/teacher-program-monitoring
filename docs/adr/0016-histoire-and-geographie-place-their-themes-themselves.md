# Histoire and géographie place their thèmes themselves

Histoire and géographie have no domaine: their programme is cut into thèmes, and a thème
names the périodes it is meant to occupy — « Thème 2 : La monarchie en France (XVIe –
XVIIe siècles) (deuxième et troisième périodes) ». No other matière's programme does
that, so these two are the only ones the generator is *told* where to put rather than
deciding, and the reading is done in
`core/services/programmation/themes.py` rather than spread over the year like everything
else (ADR-0015).

The mention is always parenthesised and always says « période ». Ten thèmes d'histoire
name their périodes outright. One of them — CM2's « Vers une France républicaine » —
prints « (deuxième période) » inside the block rather than in the heading, which is why
the description is read at all; it is only read when the heading says nothing, so that a
« période napoléonienne » in a body of text can never be mistaken for a placement.

The seven thèmes de géographie say only how many périodes they want: « (1 période) »,
« (2 périodes) », « (1 ou 2 périodes au choix) ». Which ones is ours. They are walked
through P1…P5 in the order the programme prints them, each taking its minimum first, and
the périodes left over are handed back to the thèmes that allow more, again in order. At
CM1 that gives « Se nourrir » two périodes and the other three one each; at CM2 the
minima already fill the five.

Within a période, the thèmes that claim it share that période's créneaux evenly — CM1's
P2 is claimed by both Thème 1 and Thème 2, and each gets half of it.
