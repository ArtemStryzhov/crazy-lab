"""Cluster game configuration file/setup"""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Singleton cluster game configuration class."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "crazy_lab"
        self.provider_number = 0
        self.working_name = "Crazy Lab"
        self.wincap = 25000.0
        self.win_type = "cluster"
        self.rtp = 0.9700
        self.construct_paths()

        # Game Dimensions
        self.num_reels = 7
        # Optionally include variable number of rows per reel
        self.num_rows = [7] * self.num_reels
        # Board and Symbol Properties
        t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11 = (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12), (13, 13), (14, 14), (15, 49)
        pay_group = {
            (t1, "H1"): 1.0,
            (t2, "H1"): 1.5,
            (t3, "H1"): 1.75,
            (t4, "H1"): 2.0,
            (t5, "H1"): 2.5,
            (t6, "H1"): 5.0,
            (t7, "H1"): 7.5,
            (t8, "H1"): 15.0,
            (t9, "H1"): 35.0,
            (t10, "H1"): 70.0,
            (t11, "H1"): 150.0,
            (t1, "H2"): 0.75,
            (t2, "H2"): 1.0,
            (t3, "H2"): 1.25,
            (t4, "H2"): 1.5,
            (t5, "H2"): 2.0,
            (t6, "H2"): 4.0,
            (t7, "H2"): 6.0,
            (t8, "H2"): 12.5,
            (t9, "H2"): 30.0,
            (t10, "H2"): 60.0,
            (t11, "H2"): 100.0,
            (t1, "H3"): 0.5,
            (t2, "H3"): 0.75,
            (t3, "H3"): 1.0,
            (t4, "H3"): 1.25,
            (t5, "H3"): 1.5,
            (t6, "H3"): 3.0,
            (t7, "H3"): 4.5,
            (t8, "H3"): 10.0,
            (t9, "H3"): 20.0,
            (t10, "H3"): 40.0,
            (t11, "H3"): 60.0,
            (t1, "L1"): 0.4,
            (t2, "L1"): 0.5,
            (t3, "L1"): 0.75,
            (t4, "L1"): 1.0,
            (t5, "L1"): 1.25,
            (t6, "L1"): 2.0,
            (t7, "L1"): 3.0,
            (t8, "L1"): 5.0,
            (t9, "L1"): 10.0,
            (t10, "L1"): 20.0,
            (t11, "L1"): 40.0,
            (t1, "L2"): 0.3,
            (t2, "L2"): 0.4,
            (t3, "L2"): 0.5,
            (t4, "L2"): 0.75,
            (t5, "L2"): 1.0,
            (t6, "L2"): 1.5,
            (t7, "L2"): 2.5,
            (t8, "L2"): 3.5,
            (t9, "L2"): 8.0,
            (t10, "L2"): 15.0,
            (t11, "L2"): 30.0,
            (t1, "L3"): 0.25,
            (t2, "L3"): 0.3,
            (t3, "L3"): 0.4,
            (t4, "L3"): 0.5,
            (t5, "L3"): 0.75,
            (t6, "L3"): 1.25,
            (t7, "L3"): 2.0,
            (t8, "L3"): 3.0,
            (t9, "L3"): 6.0,
            (t10, "L3"): 12.0,
            (t11, "L3"): 25.0,
            (t1, "L4"): 0.2,
            (t2, "L4"): 0.25,
            (t3, "L4"): 0.3,
            (t4, "L4"): 0.4,
            (t5, "L4"): 0.5,
            (t6, "L4"): 1.0,
            (t7, "L4"): 1.5,
            (t8, "L4"): 2.5,
            (t9, "L4"): 5.0,
            (t10, "L4"): 10.0,
            (t11, "L4"): 20.0,
        }
        self.paytable = self.convert_range_table(pay_group)

        self.include_padding = True
        self.special_symbols = {"scatter": ["S"]}

        self.freespin_triggers = {
            self.basegame_type: {3: 10, 4: 12, 5: 15, 6: 20, 7: 30},
            self.freegame_type: {3: 10, 4: 12, 5: 15, 6: 20, 7: 30},
        }
        self.anticipation_triggers = {
            self.basegame_type: min(self.freespin_triggers[self.basegame_type].keys()) - 1,
            self.freegame_type: min(self.freespin_triggers[self.freegame_type].keys()) - 1,
        }

        self.maximum_board_mult = 1024

        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv", "WCAP": "WCAP.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(
                os.path.join(self.reels_path, f))

        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.0001,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "WCAP": 5},
                            },
                            "scatter_triggers": {4: 1, 5: 2},
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.002,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "scatter_triggers": {4: 5, 5: 1},
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=0.7,
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.2979,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
            BetMode(
                name="bonus",
                cost=100,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.0001,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "WCAP": 5},
                            },
                            "mult_values": {
                                self.basegame_type: {
                                    2: 10,
                                    3: 20,
                                    4: 30,
                                    5: 20,
                                    10: 20,
                                    20: 20,
                                    50: 10,
                                },
                                self.freegame_type: {
                                    2: 10,
                                    3: 20,
                                    4: 30,
                                    5: 20,
                                    10: 20,
                                    20: 20,
                                    50: 10,
                                },
                            },
                            "scatter_triggers": {4: 1, 5: 2},
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.01,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "scatter_triggers": {4: 5, 5: 1},
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                ],
            ),
        ]

        # Optimisation(rtp, avgWin, hit-rate, recordConditions)
