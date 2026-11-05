
# Numberlink - VAPL ZS 2026, Peter Zaťko

Použitý SAT solver pre projekt je [Glucose 4.2.1](https://www.labri.fr/perso/lsimon/research/glucose/).

# Dokumentácia

## Popis problému

Na vstupu máme zadané nasledujúce parametre:
- rozmer $n \cdot n$ mriežky
- mriežka v maticovom formáte, kde
  - jeden riadok = 1 riadok v mriežke
  - stĺpce sú oddelené v rámci riadku (1) medzerou
- ďalej jednotlivé políčka sú:
  - $0$, ak sú prázdne, alebo
  - čísla $1$ až $m$, kde každé číslo musí byť v mriežke práve 2-krát 

Problém je nasledovný: ako spojiť všetky čísla súvislými, neprekrývajúcimi sa cestami tak, aby všetky páry rovnakých čísel boli spojené a zároveň, aby cez každé políčko prechádzala nejaká cesta? 

Na výstupe teda máme:
- $n \cdot n$ mriežku, kde každé políčko má priradené nejaké číslo s tým, že takáto mriežka splňuje požadované vlastnosti z popisu problému.

Príklad validného vstupu:
```
3
1 0 0
0 0 0
1 2 2
```

Validné riešenie pre daný vstup:
```
1 2 2 
1 2 2 
1 2 2 
```

## Zakódovanie do výrokových formulí

Tento problém je zakódovaný pomocou 2 základných kategórií výrokov, ktoré sú spolu spojené tak, aby dali dokopy jeden dlhý CNF výrok:

Základnou požiadavkou v Numberlinku je, že každé políčko musí odpovedať práve 1 číslu.
Na to si najprv zavedieme výrokovú premennú $Is_{x,y,i}$, kde takáto výroková premenná vyjadruje, či políčko na súradniciach $x,y$ (kde $0,0$ je vľavo hore a $n-1,n-1$ vpravo dole v mriežke) má priradené číslo $i \in \{1 \dots m\}$.
Požadujeme, aby každé políčko odpovedalo práve 1 číslu, to vieme rozpísať na dva CNF výroky:
- $Is_{x,y,i}$ je pravdivé pre aspoň 1 $i \in \{1 \dots m\}$
  - dostaneme výrok: $\bigvee_{i=1}^{m} Is_{x,y,i}$
  - pre všetky $x,y$:
    $$\bigwedge_{x,y \in \{0 \dots n-1\}} \bigvee_{i=1}^{m} Is_{x,y,i}$$
- $Is_{x,y,i}$ je pravdivé pre najviac 1 (t.j. žiadna dvojica nemôže platiť naraz) $i \in \{1 \dots m\}$
  - dostaneme výrok: $\bigwedge_{1 \le i < j \le m} (\neg Is_{x,y,i} \vee \neg Is_{x,y,j})$
  - pre všetky $x,y$:
    $$\bigwedge_{x,y \in \{0 \dots n-1\}} \bigwedge_{1 \le i < j \le m} (\neg Is_{x,y,i} \vee \neg Is_{x,y,j})$$

Ďalej požadujeme, aby čísla, ktoré sme zadali v rámci vstupných parametrov boli na zadaných políčkach, to znamená, že pre každé nenulové políčko s číslom $i \neq 0$ na $x,y$ potrebujeme, aby práve $Is_{x,y,i}$ bolo pravdivé a ostatné nepravdivé.
To, že bude pravdivé pre práve 1 číslo sme už vyriešili predchádzajúcou sériou výrokov, tu nám stačí požadovať, že bude pravdivé pre číslo zo vstupu, t.j.:
- pre každé $x,y$ s $grid[x,y] = i \neq 0$ dostávame: $Is_{x,y,i}$
- pre všetky $x,y$ s nenulovou hodnotou:
  $$\bigwedge_{\substack{x,y \in \{0 \dots n-1\} \\ grid[x,y] \neq 0}} Is_{x,y,grid[x,y]}$$

Tým by sme mali poriešené to, že každé políčko odpovedá práve 1 číslu, a že tie čísla, ktoré sme zadali na vstupe na ich pozíciách odpovedajú správne tiež.
Ďalej budeme potrebovať nejak zakódovať samotné cesty medzi číslami, to je predmetom nasledujúcich výrokových formulí.

Najprv si však uvedomme, že to, čo hľadáme - cesty medzi dvomi koncovými číslami (tie čísla, ktoré sme zadali na vstupe) sú vlastne postupnosti neorientovaných hrán v nejakom grafe.
Tento neorientovaný graf má vrcholy olabolované $x,y$ a zaveďme si konvenciu, že ak vedie (neorientovaná) hrana medzi $u$ a $v$, kde $u = (x_1, y_1)$, $v = (x_2, y_2)$, tak ju budeme značiť ako hranu $u \to v$, ak $u$ bude vrchol, pre ktorý bude platiť:
- $x_1 + y_1 < x_2 + y_2$
- alebo ak $x_1 + y_1 = x_2 + y_2$, tak $x_1 < x_2$

inak ju budeme značiť ako $v \to u$.

Definujme si teda výrokovú premennú $E_{u \to v}$ tak, že bude pravdivá práve vtedy, keď $u \to v$ hrana existuje v našom grafe.

Ako prvú triviálnu podmienku môžeme pridať to, že pre každé $E_{u \to v}$ musia $u$ a $v$ odpovedať rovnakému číslu, t.j. dostávame $E_{u \to v} \rightarrow (Is_{x_1, y_1, i} \leftrightarrow Is_{x_2, y_2, i})$ pre každé $i \in \{1 \dots m\}$.
Túto ekvivalenciu vieme rozpísať na dve implikácie a následne previesť do CNF.
Nakoniec dostaneme pre každé $i \in \{1 \dots m\}$:
$$ (\neg E_{u \to v} \vee \neg Is_{x_1, y_1, i} \vee Is_{x_2, y_2, i}) \wedge (\neg E_{u \to v} \vee \neg Is_{x_2, y_2, i} \vee Is_{x_1, y_1, i})$$

Týmto sme zaistili, že aby mohla viesť medzi nejakými políčkami hrana, tak musia mať rovnaké číslo.
Čo ďalej? Keď sa pozrieme na nejakú validnú cestu, tak určite spĺňa, že má práve 2 koncové vrcholy stupňa 1, a že ak má nejaké medzivrcholy, tak tie majú stupeň 2.

To znamená, že pre všetky políčka $x,y$ t.ž. ich hodnota bola po vstupe v mriežke $0$ vyžadujeme, aby mali stupeň 2.
Toto vieme opäť (podobne ako pri práve 1 číslu) rozpísať pomocou 2 výrokov:
- z/do políčka $x,y$ vchádzajú / vychádzajú **aspoň 2 hrany**:
  - pre dané políčko $x,y$ a množinu jeho incidentných hrán $Inc(x,y)$ vyžadujeme, aby pre každú možnú vynechanú hranu $e_i \in Inc(x,y)$ existovala aspoň jedna z ostatných hrán:
    $$\bigvee_{e \in Inc(x,y) \setminus \{e_i\}} e$$
  - pre všetky políčka $x,y$ s hodnotou $0$ spoločne:
    $$\bigwedge_{\substack{x,y \in \{0 \dots n-1\} \\ \text{kde } grid[x,y] = 0}} \bigwedge_{e_i \in Inc(x,y)} \bigvee_{e \in Inc(x,y) \setminus \{e_i\}} e$$

- z/do políčka $x,y$ vchádzajú / vychádzajú **najviac 2 hrany**:
  - pre dané políčko $x,y$ vyžadujeme, aby pre každú trojicu rôznych incidentných hrán $e_i, e_j, e_k \in Inc(x,y)$ neplatilo, že existujú všetky naraz (t.j. aspoň jedna z nich je nepravdivá):
    $$\neg e_i \vee \neg e_j \vee \neg e_k$$
  - pre všetky políčka $x,y$ s hodnotou $0$ spoločne:
    $$\bigwedge_{\substack{x,y \in \{0 \dots n-1\} \\ \text{kde } grid[x,y] = 0}} \bigwedge_{\{e_i, e_j, e_k\} \subseteq Inc(x,y)} (\neg e_i \vee \neg e_j \vee \neg e_k)$$

Pre koncové body podobne:
- z/do políčka $x,y$ vchádza / vychádza **aspoň 1 hrana**:
  - pre dané políčko $x,y$ a množinu jeho incidentných hrán $Inc(x,y)$ dostávame:
    $$\bigvee_{e \in Inc(x,y)} e$$
  - pre všetky políčka $x,y$ s hodnotou $\neq 0$ spoločne:
    $$\bigwedge_{\substack{x,y \in \{0 \dots n-1\} \\ \text{kde } grid[x,y] \neq 0}} \bigvee_{e \in Inc(x,y)} e$$

- z/do políčka $x,y$ vchádza / vychádza **najviac 1 hrana**:
  - pre dané políčko $x,y$ vyžadujeme, aby pre každú dvojicu rôznych incidentných hrán $e_i, e_j \in Inc(x,y)$ neexistovali obidve naraz (t.j. aspoň jedna z nich je nepravdivá):
    $$\neg e_i \vee \neg e_j$$
  - pre všetky políčka $x,y$ s hodnotou $\neq 0$ spoločne:
    $$\bigwedge_{\substack{x,y \in \{0 \dots n-1\} \\ \text{kde } grid[x,y] \neq 0}} \bigwedge_{\{e_i, e_j\} \subseteq Inc(x,y)} (\neg e_i \vee \neg e_j)$$

Akonáhle spojíme všetky tieto čiastkové formule dokopy do jednej veľkej CNF formule, tak získame obmedzenia pre priradenie čísel, fixáciu vstupných bodov, konzistenciu hrán a správne stupne vrcholov (stupeň 2 pre medzibody a stupeň 1 pre koncové body).

Čo je ekvivalentné požiadavkám numberlinku (// TODO: overiť).

## Používateľská dokumentácia

Základné spustenie:
`main.py [-h] [-i INPUT] [-o OUTPUT] [-s SOLVER] [-v {0,1}]`

Možnosti príkazového riadku:

- `-h`, `--help` : Zobrazí sa nápoveda k použitiu programu.
- `-i INPUT`, `--input INPUT` : Vstupný súbor s inštanciou. Defaultne: `"instances/input.in"`.
- `-o OUTPUT`, `--output OUTPUT` : Výsledná CNF formula v DIMACS formáte. Default: `"formula.cnf"`.
- `-s SOLVER`, `--solver SOLVER` : SAT solver, ktorý sa má použiť. Defaultne: `"glucose-syrup"`.
- `-v {0,1}`, `--verb {0,1}` : Verbosity použitého SAT solvera.

## Príklady inštancií problémov

V priečinku `instances/` sú k dispozícii rôzne testovacie inštancie pre Numberlink vo viacerých veľkostiach (od 3x3 až po 17x17), ktoré sú rozdelené na validné (splniteľné) a nevalidné (nesplniteľné - `invalid` / `unsat`).
Dataset problémov a ich správnych ohodnotení bol získaný z https://github.com/SmilingWayne/puzzlekit-dataset.

## Experimenty a hromadné spúšťanie testov

Na hromadné testovanie všetkých inštancii naraz tu máme skript `run_tests.py`, ktorý prejde celý priečinok `instances/`, rozpozná, či sa jedná o validnú alebo nevalidnú inštanciu podľa názvu súboru, spustí nad ňou `main.py` a skontroluje, či SAT solver vrátil správny výstup.

Spustenie testov:
`python run_tests.py`

## Experiments

// TODO