from .game_override import GameStateOverride
from .game_events import update_grid_mult_event


class GameState(GameStateOverride):
    """Core function handling simulation results."""

    def run_spin(self, sim):
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            # Reset simulation variables and draw a new board based on the betmode criteria.
            self.reset_book()

            # У базовій грі мультики живуть тільки в межах серії тумблів:
            # 1) Скидаємо сітку перед спіном
            self.reset_grid_mults()

            # Перше розкриття
            self.draw_board()
            # NEW: призначаємо множники C та збираємо їх у цьому reveal
            self.assign_special_sym_function()
            self.collect_collectors_current_reveal()

            # Перший підрахунок виграшів
            self.get_clusters_update_wins()
            self.emit_tumble_win_events()
            # 2) Оновлюємо сітку після кожного підрахунку в базі
            self.update_grid_mults()

            # Продовжуємо тумбли, поки є виграш і не спрацював wincap
            while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
                self.tumble_game_board()
                # NEW: після refill призначити множники C та зібрати їх
                self.assign_special_sym_function()
                self.collect_collectors_current_reveal()

                self.get_clusters_update_wins()
                self.emit_tumble_win_events()
                # Оновлення сітки після кожного тумбла
                self.update_grid_mults()

            # Перед завершенням послідовності тумблів — одноразовий підсумок за C-символи
            self.finalize_collector_payout()

            # Кінець послідовності тумблів
            self.set_end_tumble_event()

            # 3) Очищаємо сітку після завершення серії тумблів у базі
            self.reset_grid_mults()

            self.win_manager.update_gametype_wins(self.gametype)

            # Перевірка входу у фріспіни
            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self):
        self.reset_fs_spin()

        # Визначаємо назву режиму надійно: підтримуємо і об'єкт BetMode, і рядок
        mode_name = None
        if hasattr(self, "betmode"):
            bm = self.betmode
            if hasattr(bm, "get_name"):
                try:
                    mode_name = bm.get_name()
                except Exception:
                    mode_name = None
            if mode_name is None and isinstance(bm, str):
                mode_name = bm

        # Super Buy x500: у режимі 'super_bonus' усі клітинки стартують з hits=2 (тобто x2)
        if mode_name == "super_bonus":
            for r in range(self.config.num_reels):
                for c in range(self.config.num_rows[r]):
                    self.position_multipliers[r][c] = 2  # hits=2 => x2
            # Відправляємо подію з оновленою стартовою сіткою ще до першого спіну FS
            update_grid_mult_event(self)

        while self.fs < self.tot_fs:
            self.update_freespin()

            # Перше розкриття цього FS-спіну
            self.draw_board()
            update_grid_mult_event(self)
            # NEW: призначаємо множники C та збираємо їх у цьому reveal
            self.assign_special_sym_function()
            self.collect_collectors_current_reveal()

            # Оцінка виграшів
            self.get_clusters_update_wins()
            self.emit_tumble_win_events()
            # У фріспінах мультики персистять, тому оновлюємо їх після кожного підрахунку/тумбла
            self.update_grid_mults()

            # Тумбли у FS
            while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
                self.tumble_game_board()
                # NEW: після refill призначити множники C та зібрати їх
                self.assign_special_sym_function()
                self.collect_collectors_current_reveal()

                self.get_clusters_update_wins()
                self.emit_tumble_win_events()
                self.update_grid_mults()

            # Перед завершенням послідовності тумблів у цьому FS-спіні — одноразовий підсумок за C-символи
            self.finalize_collector_payout()

            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

        self.end_freespin()
