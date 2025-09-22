from .game_calculations import GameCalculations
from src.calculations.cluster import Cluster
from .game_events import update_grid_mult_event
from src.events.events import update_freespin_event


class GameExecutables(GameCalculations):
    """Game dependent grouped functions."""

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

    def get_clusters_update_wins(self):
        """Find clusters on board and update win manager."""
        clusters = Cluster.get_clusters(self.board, "wild")
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

    def update_freespin(self) -> None:
        """Called before a new reveal during freegame."""
        self.fs += 1
        update_freespin_event(self)
        self.win_manager.reset_spin_win()
        self.tumblewin_mult = 0
        self.win_data = {}
