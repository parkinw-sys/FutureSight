from pickle import EMPTY_LIST

from poke_env import Player
from poke_env.battle import Battle, MoveCategory
from poke_env.calc import calculate_damage
from poke_env.calc.damage_calc_gen1_2 import calculate_damage_gen12
from poke_env.data import GenData
from poke_env.stats import compute_raw_stats_dvs

stat_names = ["hp", "atk", "def", "spa", "spd", "spe"]


class Minimax(Player):

    def estimate_stats(self, mon, gen): # since we can't just get the moves from the opponent, we just sub in the normal ones
        raw = compute_raw_stats_dvs(mon.species, [15]*6, mon.level, GenData.from_gen(gen)) # showdown uses max dvs, so this is the hypothetical "worst case" opponent
        labelled_raw = dict(zip(stat_names, raw))
        for stat, value in mon.stats:
            if value is None:
                mon.stats[stat] = labelled_raw[stat] # replace unknown values for the opponent's moves
    def move_outcome(self, battle:Battle, atkr, defr, move, atkr_id, defr_id):
        atkr_hp = atkr.current_hp_fraction
        defr_hp = defr.current_hp_fraction
        if move.category == MoveCategory.STATUS: # doesnt do damage, usually a heal move
            if move.id == "rest":
                heal = 1.0-atkr.hp
            else :
                heal = move.heal
            return 0.0, min(heal, 1.0-atkr_hp)
        low, high, _ = calculate_damage_gen12(atkr_id, defr_id, move, battle)
        dmg = min((low+high)/2/defr.stats["hp"], defr_hp) # damage done up to fainting the others
        # if it has "drain" which is so complicated why
        heal = move.drain * dmg * defr.stats["hp"] / atkr.stats["hp"]
        return dmg, min(heal, 1.0-atkr_hp)
    def outcome_tuple(self, battle:Battle, my_move, their_move):
        mon_out = battle.active_pokemon
        opponent = battle.opponent_active_pokemon
        self.estimate_stats(opponent, battle.gen)
        my_id = mon_out.identifier(battle.player_role)
        opp_id = opponent.identifier(battle.opponent_role)

        # out_min, out_max, _ = calculate_damage_gen12(self_id, opp_id, my_move, battle)
        # rec_min, rec_max, _ = calculate_damage_gen12(opp_id, self_id, their_move, battle)

        my_dmg, my_heal = self.move_outcome(battle, mon_out, opponent, my_move, my_id, opp_id)
        opp_dmg, opp_heal = self.move_outcome(battle, opponent, mon_out, their_move, opp_id, my_id)

        return (my_dmg - opp_heal, opp_dmg - my_heal)
    def choose_move(self, battle: Battle):
        moves = battle.available_moves
        switches = battle.available_switches
        mon_out = battle.active_pokemon
        opponent = battle.opponent_active_pokemon
        op_switches = battle.opponent_team  # need to remove active one?
        field = battle.fields
        weather = battle.weather


        # need actions we can do, actions the opponent can do afterward, and the outcomes for each of those.
        # for simplicity rn, we're just going to track the minimax of damage

        # The form of these battles is not made for Minimax, as i have learned,
        # due to it not being Zero-sum (the opponent doesnt lose as "much" as the player wins each turn)

        # The setup is a matrix with each of the player's actions on one side, and each of the opponent's actions on the other, and each value is the "score" of that path.
        # Because of that, the "score" for this is going to be the net damage. This is heavily subject to change, depending on if it's comprehensive

        # also add alpha-beta pruning at some point
        op_moves = list(opponent.moves.values())

        if len(op_moves) < 4:
            pass # this is to add moves when we know none


        if battle.available_moves: # can attack
            results = [[self.calculate_net(battle, my_move, their_move) for my_move in moves] for their_move in opponent.moves.items()]

        return self.create_order(bestMove)


