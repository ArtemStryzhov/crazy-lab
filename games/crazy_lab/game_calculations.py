from src.executables.executables import Executables
from src.calculations.cluster import Cluster
from src.calculations.board import Board
from src.config.config import Config


class GameCalculations(Executables):
    """
    This class overrides cluster evaluation to account for position-based multipliers
    stored as hit counters on the grid, and quantizes wins to 0.1 steps to satisfy LUT checks.
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
        Determine payout amount from cluster, including position multipliers and global multiplier.
        - pos_mult_grid stores HITS per cell (number of explosions on that position).
          hits <= 1 -> no spot multiplier (0)
          hits >= 2 -> spot multiplier = min(2 ** (hits - 1), maximum_board_mult)
        - Cluster multiplier = 1 + sum(spot multipliers of all positions in the cluster)
        - Final cluster win = paytable * cluster_mult * global_multiplier
        - All wins are quantized to 0.1 to ensure payout % 10 == 0 in LUT (cents*1 units).
        """
        # Convert hit counter to actual spot multiplier (0, 2, 4, 8, ... capped by maximum_board_mult)
        def hits_to_spot_mult(hits: int) -> int:
            if hits <= 1:
                return 0
            val = 2 ** (hits - 1)
            return min(val, config.maximum_board_mult)

        # Quantize to 0.1 step; add tiny epsilon to avoid float artifacts
        def q01(x: float) -> float:
            return round(x + 1e-9, 1)

        exploding_symbols = []
        total_win = 0.0

        for sym in clusters:
            for cluster in clusters[sym]:
                syms_in_cluster = len(cluster)
                if (syms_in_cluster, sym) in config.paytable:
                    # Sum spot multipliers across all positions in the cluster
                    sum_spot_mult = 0
                    for r, c in cluster:
                        hits = pos_mult_grid[r][c]  # number of explosions on that cell
                        sum_spot_mult += hits_to_spot_mult(hits)

                    # Cluster multiplier = 1 + sum of spot multipliers
                    cluster_mult = 1 + sum_spot_mult

                    # Base pay from paytable (bet multipliers)
                    sym_win = config.paytable[(syms_in_cluster, sym)]

                    # Raw cluster win, then quantize to 0.1
                    raw_win = sym_win * cluster_mult * global_multiplier
                    symwin_mult = q01(raw_win)

                    # Accumulate (quantized) total win
                    total_win = q01(total_win + symwin_mult)

                    # Prepare positions for events/logs
                    json_positions = [{"reel": p[0], "row": p[1]} for p in cluster]
                    central_pos = Cluster.get_central_cluster_position(json_positions)

                    # Append win entry
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

                    # Mark exploding symbols on the board
                    for r, c in cluster:
                        board[r][c].explode = True
                        es = {"reel": r, "row": c}
                        if es not in exploding_symbols:
                            exploding_symbols.append(es)

        # Update return data with quantized total
        return_data["totalWin"] = q01(return_data["totalWin"] + total_win)

        return board, return_data
