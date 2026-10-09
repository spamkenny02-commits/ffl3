# Récapitulatif — Final Fantasy Legend III FR

La ROM reste à 512 Ko, avec son MBC1, sa RAM de 8 Ko et ses sommes de contrôle recalculées. Cette reprise révise 13 entrées du projet. Le projet contient désormais 1 435 entrées ; 1 095 emplacements textuels présentent une différence binaire par rapport à la ROM USA.

## Corrections

- Paramètre de commande préservé : il avait été pris pour du texte et provoquait l’arrêt d’un dialogue sur la machine temporelle. La réinsertion refuse désormais de modifier ce paramètre connu.
- Trois fragments anglais oubliés ou tronqués ont été traités : « from », le possessif après Sharon et une seconde occurrence de « the party ».
- « utilise » est correctement au présent dans les messages de combat.
- Quelques accents du prologue ont été rétablis.
- Les choix État et Équipement restent alignés dans les positions fixes du menu.
- Le message de sauvegarde tient dans les deux lignes de sa fenêtre.

## Validation réalisée

Onze tests passent. Le premier combat a été gagné, les gains reçus, et le scénario initial a continué jusqu’au Talon. Sur ce parcours, l’audit de rendu ne relève aucune lecture dans les anciens blocs de texte déplacés. Les noms variables, les objets obtenus et les gains de combat ont été observés.

Une partie de test a été sauvegardée, l’émulateur fermé puis redémarré, et la partie chargée par Reprendre. Le groupe et ses valeurs affichées ont été retrouvés. La RAM sauvegardée occupe 8 192 octets.

## Reste à faire

Valider les autres époques, boutiques, sorts, donjons, boss et la fin du jeu. L’extraction des événements reste en partie heuristique ; d’autres paramètres ou fragments oubliés peuvent encore apparaître sur des chemins non exécutés. Les minuscules û, ë, ï et les majuscules accentuées ne sont pas installées. Les champs fixes acceptent é ; les autres glyphes accentués actuels nécessitent le moteur de dialogue. Les logos et certains graphismes restent anglais. Aucun essai sur console physique ni transfert d’une ancienne sauvegarde USA n’a été effectué. L’interface Tkinter n’a pas été testée interactivement dans cet environnement sans affichage.

La version demeure expérimentale ; les onze tests ne constituent pas une validation du jeu entier.
