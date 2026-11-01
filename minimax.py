from pickle import EMPTY_LIST
from poke_env import Player
from poke_env.battle import Battle, MoveCategory
from poke_env.calc import calculate_damage
from poke_env.calc.damage_calc_gen1_2 import calculate_damage_gen12
from poke_env.data import GenData
from poke_env.stats import compute_raw_stats_dvs
import translate
from poke_engine import Side, State, generate_instructions


stat_names = ["hp", "atk", "def", "spa", "spd", "spe"]




class Minimax(Player):


   def estimate_stats(self, mon): # since we can't just get the moves from the opponent, we just sub in the normal ones
       # use the sets JSON data to predict the opponent's pokemon's set
       return

   def evaluate(self, state): # basically just gives a state a "score" so we can test the difference between two by just subtracting
       my_score = 0
       opponent_score = 0

       for pokemon in state.side_one.pokemon:
           if pokemon.maxhp > 0:
               my_score += pokemon.hp / pokemon.maxhp

       for pokemon in state.side_two.pokemon:
           if pokemon.maxhp > 0:
               opponent_score += pokemon.hp / pokemon.maxhp

       unseen_pokemon = 6 - len(state.side_two.pokemon)  # accounting for opponent's unseen pokemon
       opponent_score += unseen_pokemon

       return (my_score - opponent_score) / 6
   # def move_outcome(self, battle:Battle, atkr, defr, move, atkr_id, defr_id):
   #     atkr_hp = atkr.current_hp_fraction
   #     defr_hp = defr.current_hp_fraction
   #     if move.category == MoveCategory.STATUS: # doesnt do damage, usually a heal move
   #         if move.id == "rest":
   #             heal = 1.0-atkr.hp
   #         else :
   #             heal = move.heal
   #         return 0.0, min(heal, 1.0-atkr_hp)
   #     low, high, _ = calculate_damage_gen12(atkr_id, defr_id, move, battle)
   #     dmg = min((low+high)/2/defr.stats["hp"], defr_hp) # damage done up to fainting the others
   #     # if it has "drain" which is so complicated why
   #     heal = move.drain * dmg * defr.stats["hp"] / atkr.stats["hp"]
   #     return dmg, min(heal, 1.0-atkr_hp)
   # def outcome(self, battle:Battle, my_move, their_move):
   #     mon_out = battle.active_pokemon
   #     opponent = battle.opponent_active_pokemon
   #     self.estimate_stats(opponent)
   #     my_id = mon_out.identifier(battle.player_role)
   #     opp_id = opponent.identifier(battle.opponent_role)
   #
   #
   #     # out_min, out_max, _ = calculate_damage_gen12(self_id, opp_id, my_move, battle)
   #     # rec_min, rec_max, _ = calculate_damage_gen12(opp_id, self_id, their_move, battle)
   #
   #
   #     my_dmg, my_heal = self.move_outcome(battle, mon_out, opponent, my_move, my_id, opp_id)
   #     opp_dmg, opp_heal = self.move_outcome(battle, opponent, mon_out, their_move, opp_id, my_id)
   #
   #
   #     return my_dmg - opp_heal
   def expected_value(self, state, my_move, opponent_move, from_switch):  # the expected change in state, in the form of a score
       outcomes = generate_instructions(state, my_move, opponent_move)  # every possible state change, with probabilities of each branch. if passed in move is a pokemon speices id, that's switching. wonderful
       play_state = State.from_string(
           state.to_string())  # copy of the real state, so that we don't modify the it while checking
       expected_score = 0


       for outcome in outcomes:  # compiling all the possible changes
           probability = outcome.percentage / 100  #
           next_state = play_state.apply_instructions(outcome)
           #my_options_next_state = translate.my_options(battle_but_in_next_state) // need to be able to get player data from a state, not a battle. state-to-battle function?
           # if not from_switch and (my_move in battle.available_switches): # add detection for opponent switches, currently im not sure we do that and i dont have access to it
           #     expected_store += probability * (expected value for every single new option in the next state
           # else:
           #     expected_score += probability * self.evaluate(next_state)
           expected_score += probability * self.evaluate(next_state)
           play_state.reverse_instructions(
               outcome)  # revert back to the true state. this could be the source of a future bug

       return expected_score
   def choose_move(self, battle: Battle):
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

       state = translate.battle_to_state(battle)
       my_options = translate.my_options(battle)
       opponent = battle.opponent_active_pokemon
       their_options = translate.opponent_options(state)
       if battle.available_moves:  # can attack
           results = [[(self.expected_value(state, my_move, their_move, False), my_move) for their_move in
                       their_options] for my_move in my_options.keys()]
           maximum_options = []
           for i in range(len(list(opponent.moves.values()))):
               maximum_options[i] = max(results[i])
           return my_options[min(maximum_options)[1]]
       return my_options[0]