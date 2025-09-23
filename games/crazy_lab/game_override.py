from .game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """
    This class is used to override or extend universal state.py functions.
    e.g: A specific game may have custom book properties to reset
    """

    def reset_book(self):
        # Reset global values used across multiple projects
        super().reset_book()
        # Reset parameters relevant to local game only
        self.tumble_win = 0
        # NEW: reset per-spin collector state (for 'C' symbol aggregation)
        if hasattr(self, "reset_collector_state"):
            self.reset_collector_state()

    def reset_fs_spin(self):
        super().reset_fs_spin()
        self.reset_grid_mults()
        # NEW: also reset collector state at the start of each free spin
        if hasattr(self, "reset_collector_state"):
            self.reset_collector_state()

    def assign_special_sym_function(self):
        # Delegate to GameExecutables implementation (assigns multipliers to 'C')
        return super().assign_special_sym_function()

    def check_repeat(self) -> None:
        """Checks if the spin failed a criteria constraint at any point."""
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True

            if self.get_current_distribution_conditions()["force_freegame"] and not (self.triggered_freegame):
                self.repeat = True

            if self.win_manager.running_bet_win == 0 and self.criteria != "0":
                self.repeat = True
