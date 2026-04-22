---
title: "7.9 Rechenbeispiele und Matura-Muster"
tags:
  - "compact"
  - "Physik Mitschrift"
  - "Friedl Mappe"
---

<div v-pre>

Diese Seite sammelt die wichtigsten Rechenmuster aus der Gravitation. Sie verbindet die Mitschrift mit Friedl-Beispielen und der stärkeren Herleitungslogik aus den compact-Seiten zu [Kepler](./04_dieDreiGesetzeVonKepler.md), [Kreisbahn](./05_satellitAufEinerKreisbahn.md), [Fluchtgeschwindigkeit](./07_fluchtgeschwindigkeit.md) und [Schwarzen Löchern](./08_schwarzeLoecher.md).

## 7.9.1 Masse eines Zentralkörpers aus einem Mond

Aus dem dritten Kepler'schen Gesetz folgt für einen Körper, der eine Masse $M$ umkreist:

$$
\frac{T^2}{r^3} = \frac{4\pi^2}{G M}
$$

Nach $M$ umformen:

$$
M = \frac{4\pi^2 r^3}{G T^2}
$$

$M \dots$ Masse des umkreisten Körpers  
$r \dots$ Bahnradius des umkreisenden Körpers  
$T \dots$ Umlaufzeit  

==Damit kann man z.B. die Masse von Jupiter aus Umlaufzeit und Abstand eines Jupitermondes bestimmen.==

**Rechenweg:**

1. Abstand in Meter umrechnen.
2. Umlaufzeit in Sekunden umrechnen.
3. In $M = \frac{4\pi^2 r^3}{G T^2}$ einsetzen.
4. Ergebnis in kg interpretieren.

## 7.9.2 Bahngeschwindigkeit eines Satelliten

Für einen Satelliten auf Kreisbahn gilt:

$$
F_{ZP}=F_G
$$

$$
\frac{m v^2}{r}=G\frac{M m}{r^2}
$$

Masse des Satelliten kürzen:

$$
v=\sqrt{\frac{GM}{r}}
$$

==Der Radius $r$ ist immer der Abstand zum Erdmittelpunkt, nicht die Höhe über der Erdoberfläche.==

## 7.9.3 Geostationäre Bahn

Ein geostationärer Satellit hat die gleiche Winkelgeschwindigkeit wie die Erde:

$$
T \approx 24h
$$

Aus

$$
\omega = \frac{2\pi}{T}
$$

und

$$
\omega^2 r^3 = GM
$$

folgt:

$$
r=\sqrt[3]{\frac{G M T^2}{4\pi^2}}
$$

**Wichtig:**  
==Das Ergebnis ist der Bahnradius vom Erdmittelpunkt. Die Flughöhe erhält man erst durch Abziehen des Erdradius.==

## 7.9.4 Fluchtgeschwindigkeit der Erde

Allgemein:

$$
v_F=\sqrt{\frac{2GM}{r}}
$$

Für die Erdoberfläche nutzt man:

$G=6{,}67\cdot 10^{-11}$  
$M_E \approx 5{,}97\cdot 10^{24}kg$  
$r_E \approx 6{,}37\cdot 10^6m$  

Dann ergibt sich ungefähr:

$$
v_F \approx 11{,}2 \frac{km}{s}
$$

==Fluchtgeschwindigkeit bedeutet nicht, dass danach keine Gravitation mehr wirkt. Sie bedeutet: Der Körper kommt mit Grenzfall-Energie gerade unendlich weit weg.==

## 7.9.5 Fiktiver Schwarzschildradius der Erde

Jede Masse hat formal einen Schwarzschildradius:

$$
R_S=\frac{2GM}{c_0^2}
$$

Für die Erde:

$$
R_S=\frac{2\cdot 6{,}67\cdot 10^{-11}\cdot 5{,}97\cdot 10^{24}}{(3\cdot 10^8)^2}
$$

Das ergibt ungefähr:

$$
R_S \approx 8{,}9mm
$$

==Die Erde wäre nur dann ein Schwarzes Loch, wenn ihre gesamte Masse innerhalb einer Kugel mit etwa 9 mm Radius läge.==

## 7.9.6 Klassische Matura-Fallen

| Falle | Korrektur |
| --- | --- |
| Höhe statt Radius einsetzen | Immer Abstand zum Massenmittelpunkt verwenden. |
| Stunden oder Tage nicht umrechnen | $T$ immer in Sekunden einsetzen. |
| Masse des Satelliten bleibt in Kreisbahnformel | Sie kürzt sich heraus. |
| Fluchtgeschwindigkeit als konstante Geschwindigkeit verstehen | Nach dem Start wird der Körper durch Gravitation langsamer. |
| Ereignishorizont als feste Oberfläche verstehen | Er ist eine Grenze im Raum, keine materielle Membran. |

</div>
