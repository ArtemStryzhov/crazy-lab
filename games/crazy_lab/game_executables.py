from .game_calculations import GameCalculations
from src.calculations.cluster import Cluster
from .game_events import update_grid_mult_event
from src.events.events import update_freespin_event
import random


class GameExecutables(GameCalculations):
    """Game dependent grouped functions."""

    # ---------------------------
    # GRID MULTIPLIERS (hits-map)
    # ---------------------------
    def reset_grid_mults(self):
        """Initialize all grid position multipliers as hit counters (not direct multipliers)."""
        # Тут ми зберігаємо кількість вибухів (hits) на кожній клітинці.
        # hits = 0 → клітинка ще не активна
        # hits = 1 → клітинка активна, але множника ще нема
        # hits = 2 → множник x2
        # hits = 3 → множник x4
        # ...
        self.position_multipliers = [
            [0 for _ in range(self.config.num_rows[reel])] for reel in range(self.config.num_reels)
        ]

    def update_grid_mults(self):
        """
        Update position multipliers based on cluster wins.
        Each winning position increases its hit counter by 1.
        Actual multiplier = 0 if hits <= 1, else min(2 ** (hits - 1), maximum_board_mult).
        """
        if self.win_data["totalWin"] > 0:
            for win in self.win_data["wins"]:
                for pos in win["positions"]:
                    r, c = pos["reel"], pos["row"]
                    # Просто інкрементуємо кількість вибухів у цій клітинці
                    self.position_multipliers[r][c] += 1
            # Записати оновлену сітку у book для подій
            update_grid_mult_event(self)

    # ---------------------------
    # COLLECTOR 'C' (per-spin)
    # ---------------------------
    def reset_collector_state(self):
        """Reset per-spin accumulator for collector symbols."""
        # Усі зібрані C-позиції за один спін (включно з усіма тумблами)
        self.collector_positions = []
        # Ефективні множники C з урахуванням позиційного множника клітинки (spot)
        self.collector_effective_mults = []
        # Унікальні маркери інстансів Symbol для недопущення повторного підрахунку того ж C в межах спіну
        self._collector_marked = set()
        # Мапа множників C за ідентифікатором інстансу символу (щоб не писати в сам Symbol)
        self._collector_symbol_mult = {}

    def _weighted_pick(self, weights_map: dict) -> int:
        """Pick an integer key from weights_map with probability proportional to weight."""
        total = sum(weights_map.values())
        r = random.randint(1, total)
        acc = 0
        last_key = None
        for k, w in weights_map.items():
            acc += w
            last_key = k
            if r <= acc:
                return int(k)
        # fallback (не має статись, але лишаємо на випадок похибок)
        return int(last_key) if last_key is not None else 0

    def assign_special_sym_function(self):
        """
        Assign random multiplier to collector symbols (C) that don't have one yet.
        Викликати після кожного draw_board()/tumble_game_board().
        Стійко працює навіть коли self.board/self.gametype ще не ініціалізовані.
        """
        # Якщо дошки ще нема або порожня — вийти тихо (ранній виклик у __init__)
        if not hasattr(self, "board") or not self.board:
            return

        # Підбираємо таблицю ваг для поточного типу гри (base/free) з безпечними дефолтами
        values_by_mode = getattr(self.config, "collector_values", None)
        if not values_by_mode:
            return

        mode_key = getattr(self, "gametype", None)
        if mode_key is None:
            # дефолтно беремо basegame_type, якщо gametype ще не заданий
            mode_key = getattr(self.config, "basegame_type", None)

        values_map = values_by_mode.get(mode_key) if mode_key in values_by_mode else None
        if not values_map:
            # запасний варіант — беремо для base або перший-ліпший словник
            base_key = getattr(self.config, "basegame_type", None)
            values_map = (values_by_mode.get(base_key) if base_key in values_by_mode else None) \
                         or next(iter(values_by_mode.values()))

        # Пробігаємо за реальною геометрією дошки (на випадок змін висоти рядів)
        reels_on_board = len(self.board)
        for r in range(min(self.config.num_reels, reels_on_board)):
            rows_on_reel = len(self.board[r])
            target_rows = min(self.config.num_rows[r], rows_on_reel)
            for c in range(target_rows):
                sym = self.board[r][c]
                if sym.name == "C":
                    sid = id(sym)
                    if sid not in self._collector_symbol_mult:
                        picked = self._weighted_pick(values_map)
                        # Зберігаємо множник у локальній мапі (не в Symbol)
                        self._collector_symbol_mult[sid] = int(picked)

    def collect_collectors_current_reveal(self):
        """
        Scan board for 'C' symbols and accumulate their (spot-adjusted) multipliers for this spin.
        Викликати після assign_special_sym_function() на кожному reveal.
        """
        def hits_to_spot_mult(hits: int) -> int:
            if hits <= 1:
                return 0
            val = 2 ** (hits - 1)
            return min(val, self.config.maximum_board_mult)

        if not hasattr(self, "board") or not self.board:
            return

        reels_on_board = len(self.board)
        for r in range(min(self.config.num_reels, reels_on_board)):
            rows_on_reel = len(self.board[r])
            target_rows = min(self.config.num_rows[r], rows_on_reel)
            for c in range(target_rows):
                sym = self.board[r][c]
                if sym.name == "C":
                    sid = id(sym)
                    # Не рахуємо повторно той самий інстанс у межах спіну
                    if sid in self._collector_marked:
                        continue
                    self._collector_marked.add(sid)

                    # Базовий множник символу C (з нашої мапи)
                    base = self._collector_symbol_mult.get(sid, 0)
                    # Позиційний множник клітинки (0,2,4,8,... → 0 означає множимо на 1)
                    hits = self.position_multipliers[r][c]
                    spot = hits_to_spot_mult(hits)
                    eff = base * (spot if spot > 0 else 1)

                    # Акумулюємо для підсумкової виплати наприкінці серії тумблів
                    self.collector_positions.append({"reel": r, "row": c})
                    self.collector_effective_mults.append(eff)

    def finalize_collector_payout(self):
        """
        Pay once per spin for collector symbols after tumble sequence ends.
        If 4+ collector symbols appeared during the spin, payout = sum(effective_mults).
        Квантуємо до 0.1 (LUT вимога). C не вибухає і не запускає додаткові тумбли.
        """
        if len(self.collector_effective_mults) < 4:
            return

        q01 = lambda x: round(x + 1e-9, 1)
        payout_mult = q01(sum(self.collector_effective_mults))

        # Оновлюємо win_data
        if "totalWin" not in self.win_data:
            self.win_data["totalWin"] = 0.0
        self.win_data["totalWin"] = q01(self.win_data["totalWin"] + payout_mult)

        if "wins" not in self.win_data:
            self.win_data["wins"] = []
        self.win_data["wins"].append(
            {
                "symbol": "COLLECTOR",
                "clusterSize": len(self.collector_effective_mults),  # кількість C за спін
                "win": payout_mult,
                "positions": list(self.collector_positions),  # усі C-позиції за спін
                "meta": {
                    "globalMult": 1,
                    "clusterMult": 1,
                    "sumSpotMult": None,
                    "winWithoutMult": payout_mult,
                    "overlay": self.collector_positions[0] if self.collector_positions else {"reel": 0, "row": 0},
                    "collector": True,
                },
            }
        )

        # Оновлюємо менеджер виграшів, щоб фінал врахувався
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        self.win_manager.tumble_win = self.win_data["totalWin"]

    # ---------------------------
    # CLUSTER WINS
    # ---------------------------
    def get_clusters_update_wins(self):
        """Find clusters on board and update win manager."""
        clusters = Cluster.get_clusters(self.board)
        return_data = {
            "totalWin": 0,
            "wins": [],
        }
        self.board, self.win_data = self.evaluate_clusters_with_grid(
            config=self.config,
            board=self.board,
            clusters=clusters,
            pos_mult_grid=self.position_multipliers,
            global_multiplier=self.global_multiplier,
            return_data=return_data,
        )

        Cluster.record_cluster_wins(self)
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        self.win_manager.tumble_win = self.win_data["totalWin"]

    # ---------------------------
    # FREESPIN TICK
    # ---------------------------
    def update_freespin(self) -> None:
        """Called before a new reveal during freegame."""
        self.fs += 1
        update_freespin_event(self)
        self.win_manager.reset_spin_win()
        self.tumblewin_mult = 0
        self.win_data = {}
