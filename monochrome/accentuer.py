"""Reviewed word replacements; no global replacement of ambiguous 'a' or 'ou'."""
import json,re
from pathlib import Path
ROOT=Path(__file__).parent
PAIRS='''
épée sacrée sacrées sacrés été entité désolé désolée désolés dernière dernières derniers séance séances décidé décide décidons décidés décidé détruire détruit détruite détruits détruites inquiétude inquiets inquiète prépare préparé prêts prêt prête prêtes prêtent près après auprès bientôt forêt forêts où là déjà voilà désormais très même mêmes être êtes rêver rêve rêves réveil réveillé réveillée réveille réveiller réveillera réveilleront réveillés réveillées protéger protégera protégerai protégeront protégé protégés protégeras régner régnera règne sécurité célèbre célèbres célèbre réparer réparé répare réparerai réparera récupère récupérez récupérer récupéré récupéreront libérer libéré libérée libère libérez général généraux désintoxique pétrifié pétrifie dépétrifié paralysé paralysée paralysés paralysées empoisonné empoisonnée empoisonnés relâche relâcher guérison guéris guérir guérit guéri guérira guérissent bientôt précède précédent précédente précieux précieuse précieuses précautions première premiers premiers deuxième troisième quatrième unité unités équipage équipé équipée équipés équiper équipement équipements entraînement entraîne entraînez entraîner entraîne-toi maîtres maître maîtresse méthode océans océan ravagé dévasté avancée avancées empêché empêcher empêche empêchent empêchera énergie énergies entrée entrées entrerons étrange étranges étrangers étrangère événement événements décidé décidez détruit détient détention détentrice mélanger mélange mélanges mélangé séparés séparé séparée séparées j'espère espère espérer désespoir nécessaire nécessaires vérifier vérifié vérifie inquiétant inquiète inquiètes inquiéter terminé terminée termine terminer éliminé éliminez éliminer élimine évitez éviter évite évacué épargner épargne épargné enlevé enlevée enlevés enlevées abîme abîmée attaqué attaquée équipage héritage héritier héritiers découvert dévoilé dévoile révèle révélé révéler pénétrer pénètre pénétré succès règne régnait régné régnant déesse déesses méchant méchants méchante préférer préfère préféré mémoire mémoires désastre étoile étoiles hôpital téléportation téléporter téléporte téléporté accélère accélérer accéléré éternel éternelle éternité étages étage épaves épave état états sérénité marécage marécages marée marées généreux gêné gênant génie géant géants géante lèche dévore désire désir désirs décevoir déçoit gagné dépêche dépêcher dépêchez créature créatures création créé créée créer crée créera reprisé épuisé épuisée épuisés épuisées détruisez désactivé activé activée désactiver résisté résistance résistances dégât dégâts dégâts défend défense défaite défaites déplace déplacé félicitations résumé numéro numéros désaccord pétrification réservoir éteint détresse élever élevé élevées élevage espèce espèces troisièmement référence délivrer délivré délivrée délivrez délivrance déposé dépose déposé donné donnée données chargée sauvegardé sauvegardée effacé effacée effacer efface effacera effaceront sélection sélectionné sélectionnez pêche pêcher bête bêtes bêta fréquemment décidé passé passée passés passées passé présent présence présente présentés accepté acceptez côté côtés gardé protégée reçu reçue reçus reçues découverte découvrirez trouvé trouvée trouvés trouvées devenu devenue santé capacité capacités moitié combativité éternelle élément éléments élémentaire théorie réagir réagi détruirai départs départ intérêt intérêts étrangement détourné détournée détournement réalité réelles réel réelle souterrain souterrains récupéré utilisée utiliserai utilisé utilisées amélioré améliorer améliorée amélioration détour dangereux généreuse mécanique mécaniques vénérable météore débris quantité plutôt bientôt dès défi défis défié affronté dévoré observé détection détecté détecte détectés détectée détectées antérieur inférieur supérieure supérieur régénère régénérer répéter répète répété répétez répétés espéré espérée arrêté arrêt arrête arrêter arrêtez arrêté arrêtez-vous trésor trésors
'''
# Grouping with hyphens is handled as one token where present.
PAIRS+=' derrière sorcières sorcière conquérir spéciale spéciales vénérer vénère volonté volontés maléfiques maléfique tempête tempêtes réussi réussir réussira réussiras réussissent arrêté arrêtée arrêtées créateur créateurs créatrices déplacée blessés blesser déesse'
TRANSLIT=str.maketrans('éèêàâîôùç','eeeaaiouc')
GROUPS={}
for word in PAIRS.split():GROUPS.setdefault(word.translate(TRANSLIT),set()).add(word)
MAP={k:next(iter(v)) for k,v in GROUPS.items() if len(v)==1 and k not in v}
# Bare verb/noun forms need grammar context, so leave their ambiguous accent unchanged.
for key in ['ou','a','la','des','pres','prete','pretes','pretent','gene','lache','eleve','elevees','present','presentes','celebre','cote','garde','trouve','donne','charge','libere','termine','revele','detecte','depose','deplace','desire','cree','arrete','accepte','melange','separe','emploie','recupere']:
 MAP.pop(key,None)
def accentuate(text,fixed=False):
 def sub(m):
  word=m.group();target=MAP.get(word.lower())
  if not target:return word
  if word.isupper():return word # Uppercase accent glyphs are not installed.
  if word[0].isupper():target=target[0].upper()+target[1:]
  # Keep initial capitals without accents if unavailable; retain lower-case accents.
  target=target.translate(str.maketrans('ÉÈÊÀÂÎÔÙÇ','EEEAAIOUC'))
  if fixed and any(c in target for c in 'èàêâîôùç'):return word
  return target
 return re.sub(r"[A-Za-z]+(?:-[A-Za-z]+)*",sub,text)
if __name__=='__main__':
 p=ROOT/'project_fr.json';j=json.loads(p.read_text());count=0
 for e in j['entries']:
  before=e['french'];e['french']=accentuate(before,not e['compressed'])
  if before!=e['french']:count+=1
 # Context-sensitive edits in reviewed story lines, rather than blanket a/ou substitutions.
 for e in j['entries']:
  if not e['compressed']:continue
  s=e['french']
  for old,new in [('a bientôt','à bientôt'),('A bientôt','A bientôt'),('a bord','à bord'),('a Elan','à Elan'),('a Cronos','à Cronos'),('a Muu','à Muu'),('a Dharm','à Dharm'),('a Sol','à Sol'),('la-bas','là-bas'),('Ou est','Où est'),('Ou sont','Où sont'),('ou est','où est'),('ou sont','où sont'),('jusqu\'a','jusqu\'à')]:s=s.replace(old,new)
  # Explicit grammar fixes, reviewed against each extracted sentence.
  s=s.replace('Arrete !','Arrête !').replace('a cree','a créé').replace('est arretee','est arrêtée')
  s=s.replace('Peut-etre','Peut-être').replace('peut-etre','peut-être').replace('Qui etes-vous','Qui êtes-vous')
  s=s.replace('Ou\n', 'Où\n').replace("d'ou je","d'où je").replace('Ou suis-je','Où suis-je')
  e['french']=s
 j['font_fr']={'literal':{'é':'AB'},'escape':'4C8A','additional':['è','à','ê','â','î','ô','ù','ç'],'missing':['û','ë','ï','accents majuscules']}
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8');print('accentuated entries',count)
