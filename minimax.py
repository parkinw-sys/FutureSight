from pickle import EMPTY_LIST

from poke_env import Player
from poke_env.battle import Battle
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
    def calculate_net(self, battle:Battle, my_move, their_move):
        mon_out = battle.active_pokemon
        opponent = battle.opponent_active_pokemon
        self.estimate_stats(opponent, battle.gen)
        self_id = mon_out.identifier(battle.player_role)
        opp_id = opponent.identifier(battle.opponent_role)

        out_min, out_max, _ = calculate_damage_gen12(self_id, opp_id, my_move, battle)
        rec_min, rec_max, _ = calculate_damage_gen12(opp_id, self_id, their_move, battle)
        deal = (out_min+out_max)/2 # maybe change to just out_min and rec_max to follow the minimax ideology of like worst case
        recieve = (rec_min+rec_max)/2
        return deal/opponent.stats["hp"] - recieve/mon_out.stats["hp"] # getting the relative damage done to max
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
        op_moves = list(opponent.moves.values())

        if len(op_moves) < 4:
            pass # this is to add moves when we know none


        if battle.available_moves: # can attack
            results = [[self.calculate_net(battle, my_move, their_move) for my_move in moves] for their_move in opponent.moves.items()]

        return self.create_order(bestMove)


