"""
APPLICATION GESTION DE PROJET (v5 — MODE DUAL)
=============================================================================
Mode 1 : Projet par défaut (Recommandation E-commerce, Produits Electroniques)
          → menu complet  (1‑6 + 0)
Mode 2 : Saisie utilisateur libre (20 à 30 tâches)
          → menu étendu   (1‑5 + 0)
=============================================================================
pip install matplotlib
"""

import sys
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict, deque


# ═══════════════════════════════════════════════════════════════════════════════
# DONNÉES DU PROJET PAR DÉFAUT  (Recommandation E-commerce – Produits Électroniques)
# Format : (ID, Nom, Durée, [Prédecesseurs], Phase, Ressources, EstJalon)
# ═══════════════════════════════════════════════════════════════════════════════
TASKS_DEFAULT = [
    # ── Phase 1 — Analyse & Cadrage ──
    ("T1",  "Réunion de lancement",            1, [],                1, "CP",    False),
    ("T2",  "Analyse besoins utilisateurs",    3, ["T1"],            1, "CP",    False),
    ("T3",  "Étude marché électronique",       2, ["T1"],            1, "CP",    False),
    ("T4",  "Analyse concurrentielle",         2, ["T2","T3"],       1, "CP",    False),
    ("T5",  "Cahier des charges rec.",         3, ["T2","T4"],       1, "CP",    False),
    ("J1",  "Fin Phase Analyse",               0, ["T5"],            1, "—",     True),
    # ── Phase 2 — Données Produits ──
    ("T6",  "Identification sources données",  2, ["J1"],            2, "DE",    False),
    ("T7",  "Collecte catalogues produits",    4, ["T6"],            2, "DE",    False),
    ("T8",  "Extraction historique achats",    3, ["T6","T7"],       2, "DE",    False),
    ("T9",  "Analyse exploratoire données",    2, ["T7","T8"],       2, "DS",    False),
    ("J2",  "Fin Données",                     0, ["T9"],            2, "—",     True),
    # ── Phase 3 — Conception IA Recommandation ──
    ("T10", "Étude algo. recommandation",      3, ["J2"],            3, "DS",    False),
    ("T11", "Choix méthode recommandation",    2, ["J2","T10"],      3, "DS",    False),
    ("T12", "Conception architecture modèle",  3, ["T11"],           3, "DS",    False),
    ("T13", "Conception base produits",        1, ["T11"],           3, "DE",    False),
    ("J3",  "Conception validée",              0, ["T12","T13"],     3, "—",     True),
    # ── Phase 4 — Développement ──
    ("T14", "Feature engineering produits",    3, ["J3"],            4, "DS",    False),
    ("T15", "Dev moteur recommandation",       5, ["J3","T14"],      4, "DEV",   False),
    ("T16", "Interface administrateur",        3, ["J3"],            4, "DEV",   False),
    ("T17", "Intégration système e-commerce",  4, ["T15","T16"],     4, "DEV",   False),
    ("J4",  "Système développé",               0, ["T17"],           4, "—",     True),
    # ── Phase 5 — Tests ──
    ("T18", "Tests unitaires",                 2, ["J4"],            5, "QA",    False),
    ("T19", "Tests d'intégration",             3, ["J4","T18"],      5, "QA",    False),
    ("T20", "Évaluation performances modèle",  2, ["T19"],           5, "DS",    False),
    ("T21", "Tests utilisateurs",              1, ["T19"],           5, "QA",    False),
    ("T22", "Correction anomalies",           2, ["T20","T21"],     5, "DEV",   False),
    ("J5",  "Tests validés",                   0, ["T22"],           5, "—",     True),
    # ── Phase 6 — Finalisation ──
    ("T23", "Documentation technique",         3, ["J4"],            6, "CP",    False),
    ("T24", "Déploiement plateforme",          2, ["J5","T23"],      6, "DEV",   False),
    ("T25", "Soutenance projet",               1, ["T24"],           6, "CP",    False),
    ("J6",  "Fin Projet",                      0, ["T25"],           6, "—",     True),
]

# Palette couleurs par phase (projet par défaut)
FILL_DEFAULT = {
    1: "#D6E8FB", 2: "#C8EDE0", 3: "#E0DCFC", 4: "#FBD9CC",
    5: "#FAE8C8", 6: "#D6EEC4",
}
EDGE_DEFAULT = {
    1: "#3A8FD6", 2: "#1A9E6A", 3: "#7060CC", 4: "#D06030",
    5: "#C08010", 6: "#4A9010",
}
PNAME_DEFAULT = {
    1: "Ph.1 Analyse & Cadrage",
    2: "Ph.2 Données Produits",
    3: "Ph.3 Conception IA",
    4: "Ph.4 Développement",
    5: "Ph.5 Tests",
    6: "Ph.6 Finalisation",
}
JFILL = "#EEEEEE"
JEDGE = "#888888"


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════
class ProjetGestion:
    """
    Gère un projet : calcul de niveaux, matrice d'arcs, graphes tâches/étapes.
    Si fill/edge/pname ne sont pas fournis, les couleurs sont générées auto.
    """

    def __init__(self, tasks, fill=None, edge=None, pname=None,
                 titre="Projet"):
        self.tasks  = tasks
        self.ids    = [t[0] for t in tasks]
        self.index  = {t[0]: i for i, t in enumerate(tasks)}
        self.dur    = {t[0]: t[2] for t in tasks}
        self.preds  = {t[0]: t[3] for t in tasks}
        self.phase  = {t[0]: t[4] for t in tasks}
        self.res    = {t[0]: t[5] for t in tasks}
        self.jalon  = {t[0]: t[6] for t in tasks}
        self.name   = {t[0]: t[1] for t in tasks}
        self.n      = len(tasks)
        self.titre  = titre

        # styles
        if fill is not None and edge is not None and pname is not None:
            self.fill, self.edge, self.pname = fill, edge, pname
        else:
            self.fill, self.edge, self.pname = self._auto_colors()

        self.arc_matrix = self._build_arc_matrix()
        self.succ_map   = self._build_succ()
        self.levels     = self._compute_levels()

    # ── couleurs automatiques ─────────────────────────────────────────────
    def _auto_colors(self):
        phases = sorted(set(self.phase.values()))
        fills  = ["#D6E8FB","#C8EDE0","#E0DCFC","#FBD9CC",
                   "#FAE8C8","#D6EEC4","#FBD0D0","#E0E0F0",
                   "#C8F0E0","#F0E0C8","#D0E8F0","#F0D0E0",
                   "#E8F0D0","#D0D0F0","#F0E8D0","#D0F0E8"]
        edges  = ["#3A8FD6","#1A9E6A","#7060CC","#D06030",
                   "#C08010","#4A9010","#D04040","#5050A0",
                   "#208060","#A06020","#207090","#A03060",
                   "#608020","#4040A0","#908020","#209070"]
        f, e, p = {}, {}, {}
        for i, ph in enumerate(phases):
            f[ph] = fills[i % len(fills)]
            e[ph] = edges[i % len(edges)]
            p[ph] = f"Phase {ph}"
        return f, e, p

    # ── utilitaires internes ──────────────────────────────────────────────
    def _build_succ(self):
        s = defaultdict(list)
        for tid, pl in self.preds.items():
            for p in pl:
                s[p].append(tid)
        return s

    def _build_arc_matrix(self):
        M = [[0] * self.n for _ in range(self.n)]
        for tid, pl in self.preds.items():
            j = self.index[tid]
            for pid in pl:
                M[self.index[pid]][j] = 1
        return M

    def _compute_levels(self):
        """Rang topologique de Bellman (Kahn BFS)."""
        niveau = {}
        in_deg = {t: len(self.preds[t]) for t in self.ids}
        succ   = self._build_succ()

        q = deque([t for t in self.ids if in_deg[t] == 0])
        for t in q:
            niveau[t] = 1

        processed = 0
        while q:
            t = q.popleft()
            processed += 1
            for s in succ[t]:
                niveau[s] = max(niveau.get(s, 0), niveau[t] + 1)
                in_deg[s] -= 1
                if in_deg[s] == 0:
                    q.append(s)

        if processed < self.n:
            missing = [t for t in self.ids if t not in niveau]
            print(f"  ⚠ CYCLE DÉTECTÉ parmi : {', '.join(missing)}")
            print("  ⚠ Le calcul des niveaux est incomplet.")

        self.niveau = niveau
        par = defaultdict(list)
        for tid, niv in niveau.items():
            par[niv].append(tid)
        return par

    # ── 1. TABLEAU DES ANTÉRIORITÉS ──────────────────────────────────────
    def afficher_tableau_anteriorite(self):
        # calcul des successeurs
        succ_map = defaultdict(list)
        for tid, pl in self.preds.items():
            for p in pl:
                succ_map[p].append(tid)

        print("\n" + "=" * 90)
        print("  TABLEAU DES ANTERIORITES")
        print("=" * 90)
        print(f"  {'ID':<6} {'Nom':<32} {'Dur':>4}  "
              f"{'Antécédents':<22} {'Successeurs'}")
        print("  " + "-" * 86)

        cur_ph = None
        for t in self.tasks:
            tid, nom, dur, preds, ph, res, jal = t
            if ph != cur_ph:
                cur_ph = ph
                label = self.pname.get(ph, f"Phase {ph}")
                print(f"\n  ── {label} ──")
            ps = ", ".join(preds) if preds else "---"
            ss = ", ".join(succ_map.get(tid, [])) if succ_map.get(tid) else "---"
            fl = "  ◄ JALON" if jal else ""
            print(f"  {tid:<6} {nom:<32} {str(dur) + 'j':>4}  "
                  f"{ps:<22} {ss}{fl}")
        print("  " + "-" * 86)

    # ── 2. MATRICE DES ARCS ──────────────────────────────────────────────
    def afficher_matrice_arcs(self):
        print("\n" + "=" * 74)
        print("  MATRICE DES ARCS  (1 = i → j  c-à-d i précède j)")
        print("=" * 74)
        header = "  " + "".join(f"{t:>5}" for t in self.ids)
        print(header)
        print("  " + "-" * (5 + 5 * self.n))
        for i, ti in enumerate(self.ids):
            row = f"  {ti:<5}|"
            for j in range(self.n):
                row += " 1" if self.arc_matrix[i][j] else " ."
            print(row)

    # ── 3. NIVEAUX (Bellman) ─────────────────────────────────────────────
    def afficher_niveaux(self):
        print("\n" + "=" * 74)
        print("  NIVEAUX DU PROJET  (Rang topologique de Bellman)")
        print("=" * 74)
        for niv in sorted(self.levels):
            ts      = self.levels[niv]
            reelles = [t for t in ts if not self.jalon[t]]
            jalons  = [t for t in ts if self.jalon[t]]
            par     = "  ◄ PARALLELE" if len(reelles) >= 2 else ""
            t_str   = " | ".join(f"{t}({self.dur[t]}j)" for t in reelles)
            j_str   = " | ".join(f"{t}[J]" for t in jalons)
            extra   = (" + " + j_str) if j_str else ""
            print(f"\n  Niv.{niv:>2}: {t_str}{extra}{par}")
            for t in reelles:
                print(f"    {t:<6} {self.name[t]:<38} {self.dur[t]}j")
            for t in jalons:
                print(f"    {t:<6} {self.name[t]:<38} 0j [JALON]")

    # ── 4. GRAPHE ORIENTÉ TÂCHES ─────────────────────────────────────────
    def afficher_graphe_taches(self):
        max_niv = max(self.levels.keys()) if self.levels else 1
        X_STEP  = max(1.4, min(2.8, 26.0 / max_niv))
        Y_STEP  = 1.5

        # placement des nœuds
        pos = {}
        for niv in sorted(self.levels):
            taches = self.levels[niv]
            nb = len(taches)
            ys = [(k - (nb - 1) / 2) * Y_STEP for k in range(nb)]
            for k, tid in enumerate(taches):
                pos[tid] = (niv * X_STEP, ys[k])

        def node_hw(tid):
            return (0.55, 0.22) if self.jalon[tid] else (1.1, 0.38)

        all_x = [p[0] for p in pos.values()]
        all_y = [p[1] for p in pos.values()]
        fig_w = max(20, (max(all_x) - min(all_x)) * 0.60 + 4)
        fig_h = max(8,  (max(all_y) - min(all_y)) * 1.1 + 5)
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        ax.set_facecolor("white")
        fig.patch.set_facecolor("white")
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"Graphe orienté TÂCHES — {self.titre}",
                      fontsize=13, fontweight="bold", pad=16)

        # flèches
        for tid, pl in self.preds.items():
            for pid in pl:
                if pid not in pos or tid not in pos:
                    continue
                x1, y1 = pos[pid]
                x2, y2 = pos[tid]
                hw1, hh1 = node_hw(pid)
                hw2, hh2 = node_hw(tid)
                sx, sy = x1 + hw1, y1
                dx, dy = x2 - hw2, y2
                ph  = self.phase[pid]
                col = self.edge.get(ph, JEDGE) if not self.jalon[pid] else JEDGE
                rad = 0.0 if abs(y2 - y1) < 0.01 else 0.15 * (1 if y2 > y1 else -1)
                ax.annotate(
                    "", xy=(dx, dy), xytext=(sx, sy),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=1.1,
                                    shrinkA=0, shrinkB=0,
                                    connectionstyle=f"arc3,rad={rad}"),
                    zorder=2)

        # nœuds
        for tid, (cx, cy) in pos.items():
            hw, hh = node_hw(tid)
            if self.jalon[tid]:
                fc, ec, tc = JFILL, JEDGE, "#444"
                style, fs, fw = "round,pad=0.05", 7, "normal"
                lbl = f"{tid}\n0j"
            else:
                ph = self.phase[tid]
                fc = self.fill.get(ph, "#DDDDDD")
                ec = self.edge.get(ph, "#999999")
                tc = "#111"
                style, fs, fw = "round,pad=0.07", 7.5, "bold"
                lbl = f"{tid} {self.dur[tid]}j\n{self.name[tid][:16]}"
            bbox = mpatches.FancyBboxPatch(
                (cx - hw, cy - hh), hw * 2, hh * 2,
                boxstyle=style, facecolor=fc, edgecolor=ec,
                linewidth=1.3, zorder=3)
            ax.add_patch(bbox)
            ax.text(cx, cy, lbl, ha="center", va="center",
                    fontsize=fs, fontweight=fw, color=tc,
                    zorder=4, linespacing=1.3)

        # étiquettes niveaux
        top_y = max(all_y) + 0.85
        for niv in sorted(self.levels):
            ax.text(niv * X_STEP, top_y, f"N{niv}",
                    ha="center", va="bottom",
                    fontsize=8, color="#888", fontstyle="italic")

        # légende
        handles = [
            mpatches.Patch(facecolor=self.fill[ph], edgecolor=self.edge[ph],
                           label=self.pname.get(ph, f"Phase {ph}"),
                           linewidth=1.2)
            for ph in sorted(self.fill)
        ]
        has_jalons = any(self.jalon[t] for t in self.ids)
        if has_jalons:
            handles.append(mpatches.Patch(facecolor=JFILL, edgecolor=JEDGE,
                                          label="Jalon (0j)", linewidth=1.2))
        ax.legend(handles=handles, loc="lower right", fontsize=7.5,
                  framealpha=0.95, title="Phases", title_fontsize=8, ncol=2)

        # boîte capturée en bas
        box_y = min(all_y) - 2.8
        ax.set_ylim(min(all_y) - 3.8, top_y + 0.5)
        ax.text(
            (min(all_x) + max(all_x)) / 2, box_y,
            f"{self.titre}\n"
            "Tableau d'antériorité des tâches\n"
            "(capturé en bas du graphe)",
            ha="center", va="top", fontsize=9,
            bbox=dict(boxstyle="round,pad=1",
                      facecolor="#F8F8F8", edgecolor="#666", linewidth=1.5))

        ax.set_xlim(min(all_x) - 1.8, max(all_x) + 1.8)
        plt.tight_layout()
        plt.savefig("graphe_taches.png", dpi=150,
                    bbox_inches="tight", facecolor="white")
        print("\n  ✓ graphe_taches.png sauvegardé.")
        plt.show()

    # ── 5. GRAPHE ORIENTÉ ÉTAPES ─────────────────────────────────────────
    def afficher_graphe_etapes(self):
        max_niv = max(self.levels.keys()) if self.levels else 0
        etapes      = ["E0"] + [f"E{i}" for i in range(1, max_niv + 1)]
        etape_label = {"E0": "E0\nDébut"}
        etape_ph    = {"E0": 1}

        for i in range(1, max_niv + 1):
            e = f"E{i}"
            etape_label[e] = f"E{i}"
            jalons_lv = [t for t in self.levels.get(i, []) if self.jalon[t]]
            if jalons_lv:
                etape_label[e] += f"\n{jalons_lv[0]}"
            tasks_in = self.levels.get(i, [])
            etape_ph[e] = self.phase[tasks_in[0]] if tasks_in else 6

        # arcs portant les tâches
        task_arcs = []
        for tid in self.ids:
            if tid not in self.niveau:
                continue
            k   = self.niveau[tid]
            src = "E0" if k == 1 else f"E{k - 1}"
            dst = f"E{k}"
            task_arcs.append((src, dst, tid, self.dur[tid], self.phase[tid]))

        groups = defaultdict(list)
        for arc in task_arcs:
            groups[(arc[0], arc[1])].append(arc)

        X_STEP = max(2.0, min(3.5, 32.0 / max(len(etapes), 1)))
        pos_e  = {e: (i * X_STEP, 0.0) for i, e in enumerate(etapes)}

        fig_w = max(24, len(etapes) * X_STEP * 0.55 + 6)
        fig_h = 14
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        ax.set_facecolor("white")
        fig.patch.set_facecolor("white")
        ax.axis("off")
        ax.set_title(f"Graphe orienté ÉTAPES — {self.titre}",
                      fontsize=13, fontweight="bold", pad=16)

        R_NODE = 0.45

        # dessin des arcs (tâches)
        for (src, dst), arcs_list in groups.items():
            n   = len(arcs_list)
            x1  = pos_e[src][0]
            x2  = pos_e[dst][0]
            if n == 1:
                rads = [0.0]
            else:
                step  = 0.25 if n <= 3 else 0.18
                start = -(n - 1) * step / 2
                rads  = [start + k * step for k in range(n)]

            for k, (s, d, tid, dur, ph) in enumerate(arcs_list):
                rad = rads[k]
                col = self.edge.get(ph, JEDGE) if not self.jalon[tid] else JEDGE
                ax.annotate(
                    "", xy=(x2, 0.0), xytext=(x1, 0.0),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=1.5,
                                    shrinkA=R_NODE * 72, shrinkB=R_NODE * 72,
                                    connectionstyle=f"arc3,rad={rad}"),
                    zorder=2)

                mx = (x1 + x2) / 2
                my = rad * (x2 - x1) * 0.38
                if self.jalon[tid]:
                    lbl = f"{tid} 0j\n[JALON]"
                else:
                    nm = self.name[tid]
                    short = nm[:19] + "." if len(nm) > 19 else nm
                    lbl = f"{tid} · {dur}j\n{short}"
                ax.text(mx, my, lbl, ha="center", va="center",
                        fontsize=6.5, fontweight="bold", color=col,
                        bbox=dict(boxstyle="round,pad=0.22", fc="white",
                                  ec=col, lw=0.8, alpha=0.93),
                        zorder=5)

        # nœuds étapes
        for e in etapes:
            cx, cy = pos_e[e]
            if e == "E0":
                fc, ec, tc = "#D6E8FB", "#3A8FD6", "#0C447C"
            elif e == etapes[-1]:
                fc, ec, tc = "#FBD0D0", "#D04040", "#600000"
            else:
                ph = etape_ph.get(e, 6)
                fc = self.fill.get(ph, "#DDDDDD")
                ec = self.edge.get(ph, "#999999")
                tc = "#111111"
            circle = plt.Circle((cx, cy), R_NODE,
                                facecolor=fc, edgecolor=ec,
                                linewidth=2.0, zorder=6)
            ax.add_patch(circle)
            ax.text(cx, cy, etape_label.get(e, e),
                    ha="center", va="center",
                    fontsize=7.5, fontweight="bold", color=tc,
                    zorder=7, linespacing=1.1)

        # légende
        handles = [
            mpatches.Patch(facecolor=self.fill[ph], edgecolor=self.edge[ph],
                           label=self.pname.get(ph, f"Phase {ph}"),
                           linewidth=1.2)
            for ph in sorted(self.fill)
        ]
        has_jalons = any(self.jalon[t] for t in self.ids)
        if has_jalons:
            handles.append(mpatches.Patch(facecolor=JFILL, edgecolor=JEDGE,
                                          label="Jalon (arc 0j)", linewidth=1.2))
        ax.legend(handles=handles, loc="upper center",
                  bbox_to_anchor=(0.5, -0.05), fontsize=8,
                  framealpha=0.95,
                  title="Couleur des arcs = phase de la tâche",
                  title_fontsize=8.5, ncol=4)

        all_x = [v[0] for v in pos_e.values()]
        ax.set_xlim(min(all_x) - 1.5, max(all_x) + 1.5)
        ax.set_ylim(-8, 8)
        plt.tight_layout()
        plt.savefig("graphe_etapes.png", dpi=150,
                    bbox_inches="tight", facecolor="white")
        print("  ✓ graphe_etapes.png sauvegardé.")
        plt.show()


# ═══════════════════════════════════════════════════════════════════════════════
# SAISIE MANUELLE DES TÂCHES  (20 min — 30 max)
# ═══════════════════════════════════════════════════════════════════════════════
def saisir_taches():
    """
    Permet à l'utilisateur de saisir entre 20 et 30 tâches.
    Retourne une liste au format TASKS_DEFAULT ou [] si annulé / hors bornes.
    """
    MIN_T, MAX_T = 20, 30
    tasks = []

    print("\n" + "═" * 66)
    print("  SAISIE DE VOTRE PROJET")
    print("═" * 66)
    print(f"  ⚠  Vous devez saisir entre {MIN_T} et {MAX_T} tâches.")
    print("  Format par ligne :  ID;Nom;Durée;Prédecesseurs;Phase")
    print("  ─────────────────────────────────────────────────────────")
    print("  • Prédecesseurs : IDs séparés par des virgules (vide = aucun)")
    print("  • Durée = 0  →  jalon automatique")
    print("  • Phase : numéro entier (1, 2, 3 …) pour le groupement")
    print("")
    print("  Exemples :")
    print("    A;Analyse besoins;3;;1")
    print("    B;Conception;4;A;1")
    print("    C;Développement;5;B;2")
    print("    D;Tests;2;C;3")
    print("    J1;Jalon fin;0;D;3")
    print("")
    print("  Tapez  FIN  (ou ligne vide) pour terminer la saisie.")
    print("─" * 66)

    while True:
        if len(tasks) >= MAX_T:
            print(f"\n  ✓ Maximum {MAX_T} tâches atteint.")
            break

        compteur = len(tasks) + 1
        reste    = MIN_T - len(tasks)
        hint     = f"  (reste {reste} min.)" if reste > 0 else ""
        ligne = input(f"  Tâche #{compteur}{hint} > ").strip()

        if not ligne or ligne.upper() == "FIN":
            break

        try:
            parts = [p.strip() for p in ligne.split(";")]
            if len(parts) < 4:
                print("  [!] Minimum 4 champs : ID;Nom;Durée;Prédecesseurs;Phase")
                continue

            tid       = parts[0]
            nom       = parts[1]
            dur       = int(parts[2])
            preds_str = parts[3]
            phase     = int(parts[4]) if len(parts) > 4 and parts[4] else 1

            if dur < 0:
                print("  [!] La durée doit être ≥ 0.")
                continue
            if not tid:
                print("  [!] L'ID ne peut pas être vide.")
                continue
            if any(t[0] == tid for t in tasks):
                print(f"  [!] L'ID '{tid}' est déjà utilisé.")
                continue

            preds = [p.strip() for p in preds_str.split(",") if p.strip()]
            is_jalon = (dur == 0)
            tasks.append((tid, nom, dur, preds, phase, "", is_jalon))

        except ValueError:
            print("  [!] Erreur : Durée et Phase doivent être des entiers.")
            print("      Format attendu : ID;Nom;3;;1")

    # ── vérification bornes ──
    if len(tasks) < MIN_T:
        print(f"\n  [!] Minimum {MIN_T} tâches requis "
              f"({len(tasks)} saisie(s)). Saisie annulée.")
        return []

    # ── validation des prédecesseurs ──
    ids_set = {t[0] for t in tasks}
    errors  = False
    for t in tasks:
        for p in t[3]:
            if p not in ids_set:
                print(f"  [!] Tâche '{t[0]}' : prédecesseur '{p}' introuvable.")
                errors = True
    if errors:
        print("\n  [!] Corrigez les prédecesseurs et relancez la saisie.")
        return []

    return tasks


# ═══════════════════════════════════════════════════════════════════════════════
# MENUS
# ═══════════════════════════════════════════════════════════════════════════════
def menu_complet(p):
    """Menu complet — projet par défaut (options 1‑6 + 0)."""
    while True:
        print("\n" + "═" * 60)
        print("  MENU — GESTION DE PROJET")
        print("  (Recommandation E-commerce — Produits Électroniques)")
        print("═" * 60)
        print("  1. Tableau des anteriorites")
        print("  2. Matrice des arcs")
        print("  3. Niveaux (rang topologique de Bellman)")
        print("  4. Graphe oriente TACHES (horizontal + boîte capturée)")
        print("  5. Graphe oriente ETAPES (X=niveaux / arcs=tâches)")
        print("  6. Tout afficher + generer les deux graphes")
        print("  0. Quitter")
        print("─" * 60)
        c = input("  Votre choix > ").strip()

        if   c == "1": p.afficher_tableau_anteriorite()
        elif c == "2": p.afficher_matrice_arcs()
        elif c == "3": p.afficher_niveaux()
        elif c == "4": p.afficher_graphe_taches()
        elif c == "5": p.afficher_graphe_etapes()
        elif c == "6":
            p.afficher_tableau_anteriorite()
            p.afficher_matrice_arcs()
            p.afficher_niveaux()
            p.afficher_graphe_taches()
            p.afficher_graphe_etapes()
        elif c == "0":
            print("\n  Au revoir !\n")
            sys.exit(0)
        else:
            print("  [!] Entrez un chiffre entre 0 et 6.")


def menu_reduit(p):
    """Menu étendu — projet saisi par l'utilisateur (options 1‑5 + 0)."""
    while True:
        print("\n" + "═" * 60)
        print("  MENU — VOTRE PROJET (saisie libre)")
        print("═" * 60)
        print("  1. Tableau des anteriorites")
        print("  2. Matrice des arcs")
        print("  3. Niveaux (rang topologique de Bellman)")
        print("  4. Graphe oriente TACHES (horizontal + boîte capturée)")
        print("  5. Graphe oriente ETAPES (X=niveaux / arcs=tâches)")
        print("  0. Retour au menu principal")
        print("─" * 60)
        c = input("  Votre choix > ").strip()

        if   c == "1": p.afficher_tableau_anteriorite()
        elif c == "2": p.afficher_matrice_arcs()
        elif c == "3": p.afficher_niveaux()
        elif c == "4": p.afficher_graphe_taches()
        elif c == "5": p.afficher_graphe_etapes()
        elif c == "0": return
        else:
            print("  [!] Entrez un chiffre entre 0 et 5.")


def menu_principal():
    """Menu racine — choix du mode d'utilisation."""
    while True:
        print("\n" + "╔" + "═" * 56 + "╗")
        print("║       APPLICATION  GESTION  DE  PROJET          ║")
        print("╠" + "═" * 56 + "╣")
        print("║  1. Projet par défaut                         ║")
        print("║     (Recommandation E-commerce,               ║")
        print("║      Produits Électroniques)                  ║")
        print("║                                                ║")
        print("║  2. Saisir votre propre liste de tâches       ║")
        print("║     (entre 20 et 30 tâches)                   ║")
        print("║                                                ║")
        print("║  0. Quitter                                    ║")
        print("╚" + "═" * 56 + "╝")
        c = input("  Votre choix > ").strip()

        if c == "1":
            p = ProjetGestion(
                TASKS_DEFAULT,
                FILL_DEFAULT, EDGE_DEFAULT, PNAME_DEFAULT,
                titre="Recommandation E-commerce — Produits Électroniques")
            n_t = sum(1 for t in TASKS_DEFAULT if not t[6])
            n_j = sum(1 for t in TASKS_DEFAULT if t[6])
            print(f"\n  ✓ Chargé : {n_t} tâches + {n_j} jalons "
                  f"/ {len(p.levels)} niveaux / 6 phases")
            menu_complet(p)

        elif c == "2":
            tasks = saisir_taches()
            if not tasks:
                print("  [!] Aucun projet valide. Retour au menu.\n")
                continue
            p = ProjetGestion(tasks, titre="Projet personnel")
            n_t = sum(1 for t in tasks if not t[6])
            n_j = sum(1 for t in tasks if t[6])
            print(f"\n  ✓ Chargé : {n_t} tâches + {n_j} jalons "
                  f"/ {len(p.levels)} niveau(x)")
            menu_reduit(p)

        elif c == "0":
            print("\n  Au revoir !\n")
            sys.exit(0)

        else:
            print("  [!] Entrez 0, 1 ou 2.")


# ═══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    menu_principal()