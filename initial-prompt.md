Nous allons construire ensemble une application web complete pour ma femme, le but étant pour elle d'avoir une interface complète pour gérer
son année en double niveau cm1-cm2. La gestion doit s'étendre sur le programme complet de ces deux niveaux, un calendrier des périodes, répartitions du programme, détail des séances au jour le jour, entretien du carnet de bord journalier. Voici les grandes lignes.

D'un point de vue documentation et bibliographie, je vais te donner des documents importants:

- Programme CM1-CM2 dans un fichier pdf unique (avec liens internes).
- Emploi du temps "typique" d'une semaine, avec des contraintes temporelles sur les séances (format pdf) fait par ma femme. A respecter scrupuleusement.
- Des outils pédagogiques pour certaines matieres (maths, francais, littérature). Ce sont des méthodologies que ma femme veut utiliser pour cette année scolaire sur son double niveau.

Les documents en détails, dans le folder docs/:

- edt.pdf: l'emploi du temps typique a respecter scrupuleusement.
- outil-pedagogique-litterature-par-semaine.pdf: méthodologie par semaine pour la litérature
- exemple-cahier-journal-quotidien.pdf: exemple de cahier journal quotidien (journal de bord)
- outil-pedagogique-maths-cm1.pdf: méthodologie CM1 pour les maths
- outil-pedagogique-grammaire-conjugaison.pdf: méthodologie Grammaire conjugaison (CM1 et CM2 dans le meme PDF.)
- outil-pedagogique-maths-cm2.pdf: méthodologie maths CM2
- outil-pedagogique-litterature-annee.pdf: méthodologie literature a l'annee (overview)
- programme-cm1-cm2.pdf: programme complet CM1 et CM2.

Ce qu'on veut avoir, en terme de génération: 

- un programme COMPLET, par période de l'année scolaire, par semaine et par jour, de la répartition des séances, tout en respectant l'EDT.
- une interface web simple, permettant de naviguer sur cette programmation, permettant de voir le calendrier complet, jusqu'au détail de la journée.
- un gestionnaire de cahier journal, par jour, avec possibilité de le modifier a la volée si la gestion de la journée a été modifiée.

L'application sera utilisée en locale, sur le PC de ma femme uniquement. Pas besoin de login, etc. Simple et efficace.

Concernant la stack technique: tu es dans le repo de la codebase. Regarde comment le monorepo est structuré, pour comprendre comment on va servir l'app localement.

Les programmes doivent être accessibles et lisibles depuis l’application, a des fins de lecture. Possibilité de filtrer par matière, ou de chercher par mots clefs sur des descriptions ou titre (a toi de voir).

Il nous faut un moyen de stocker l’organisation, au jour pres, d’une journée de travail, avec le carnet journalier comme on a vu précédemment.

Il y aura une phase ou la programmation des jours doit être générée. Et aussi on doit pouvoir donner du feedback au jour le jour a une IA qui doit pouvoir modifier a la volée un carnet journalier après feedback.

On doit avoir une interface claire et fluide ui ux friendly qui permet d’organiser tout cela. A toi d’y penser concretement.

Tout doit être persistant en base de données.

Ce que je veux de toi ici est simple: ecrire un prompt propre, detaillant tout cela pour que je puisse commencer a envoyer des agents claude faire le boulot.

Aussi, je pense qu’il serait judicieux de mentionner certains skills de ce repository 
 https://github.com/mattpocock/skills 

Fais moi tout cela, et on peut commencer a dev le projet !



