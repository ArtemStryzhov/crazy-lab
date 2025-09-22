from src.executables.executables import Executables
from src.calculations.cluster import Cluster
from src.calculations.board import Board
from src.config.config import Config


class GameCalculations(Executables):
    """
    This function will override the evaluate_clusters() function in cluster.py
    This is to account for the grid multiplier in winning positions.
    """

    # Override cluster evaluation functions to include grid position multipliers
    def evaluate_clusters_with_grid(
        self,
        config: Config,
        board: Board,
        clusters: dict,
        pos_mult_grid: list,
        global_multiplier: int = 1,
        return_data: dict = {"totalWin": 0, "wins": []},
    ) -> type:
        """
        Determine payout amount from cluster, including symbol multiplier and global multiplier value.
        Game specific function which takes into account position multipliers.
        """
        exploding_symbols = []
        total_win = 0

        # Локальна функція для конвертації hits → фактичний множник клітинки
        def hits_to_spot_mult(hits: int) -> int:
            if hits <= 1:
                return 0
            # 1-й вибух → ще немає мульта, 2-й → x2, 3-й → x4, ...
            val = 2 ** (hits - 1)
            return min(val, config.maximum_board_mult)

        for sym in clusters:
            for cluster in clusters[sym]:
                syms_in_cluster = len(cluster)
                if (syms_in_cluster, sym) in config.paytable:
                    # Сума спотових множників (0,2,4,8...) по всіх клітинках кластера
                    sum_spot_mult = 0
                    for positions in cluster:
                        r, c = positions[0], positions[1]
                        hits = pos_mult_grid[r][c]  # кількість вибухів на клітинці
                        sum_spot_mult += hits_to_spot_mult(hits)

                    # Загальний множник кластера = 1 + сума спотових
                    cluster_mult = 1 + sum_spot_mult

                    sym_win = config.paytable[(syms_in_cluster, sym)]
                    symwin_mult = sym_win * cluster_mult * global_multiplier
                    total_win += symwin_mult

                    json_positions = [{"reel": p[0], "row": p[1]} for p in cluster]
                    central_pos = Cluster.get_central_cluster_position(json_positions)

                    return_data["wins"] += [
                        {
                            "symbol": sym,
                            "clusterSize": syms_in_cluster,
                            "win": symwin_mult,
                            "positions": json_positions,
                            "meta": {
                                "globalMult": global_multiplier,
                                "clusterMult": cluster_mult,
                                "sumSpotMult": sum_spot_mult,
                                "winWithoutMult": sym_win,
                                "overlay": {"reel": central_pos[0], "row": central_pos[1]},
                            },
                        }
                    ]

                    # Позначаємо символи, що вибухнули
                    for positions in cluster:
                        board[positions[0]][positions[1]].explode = True
                        if {
                            "reel": positions[0],
                            "row": positions[1],
                        } not in exploding_symbols:
                            exploding_symbols.append({"reel": positions[0], "row": positions[1]})

        return_data["totalWin"] += total_win

        return board, return_data
