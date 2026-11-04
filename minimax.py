from pickle import EMPTY_LIST
from poke_env import *
from poke_env.battle import Battle, MoveCategory, Move, PokemonType, Pokemon
from poke_env.calc import calculate_damage
from poke_env.calc.damage_calc_gen1_2 import calculate_damage_gen12
from poke_env.data import GenData
from poke_env.stats import compute_raw_stats_dvs
import translate
from poke_engine import Side, State, generate_instructions
import math


stat_names = ["hp", "atk", "def", "spa", "spd", "spe"]


SWITCH_WEIGHT = 0.1 # less than 1, probably less than 1/6.
# this is to keep the switching scores on par with damage scores
# a difference between effectiveness "levels" is 1 bc of logarithms,
# an OHKO from a full team is a difference of only 1/6, and it gets less as the average health goes down.
# ... maybe we tie this to the average health, hmm...


class Minimax(Player):

   def estimate_stats(self, mon): # since we can't just get the moves from the opponent, we just sub in the normal ones
       # use the sets JSON data to predict the opponent's pokemon's set
       return

   def evaluate_move(self, state): # basically just gives a state a "score" so we can test the difference between two by just subtracting
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
   def my_options(self, battle):
       legal_actions = {}

       for move in battle.available_moves:
           legal_actions[move.id] = Player.create_order(move)
           if battle.can_tera:
               legal_actions[f"{move.id}-tera"] = Player.create_order(move, terastallize=True)

       for pokemon in battle.available_switches:
           legal_actions[pokemon.species] = Player.create_order(pokemon)

       return legal_actions

   def opponent_options(self, state):
       # opponent switches to be implemented later
       opponent = state.side_two.pokemon[0]
       moves = []

       for move in opponent.moves:
           moves.append(move.id)

       return moves
   def expected_value(self, battle, my_move, opponent_move):  # the expected change in state, in the form of a score
       state = translate.battle_to_state(battle)
       outcomes = generate_instructions(state, my_move, opponent_move)  # every possible state change, with probabilities of each branch. if passed in move is a pokemon speices id, that's switching. wonderful
       play_state = State.from_string(state.to_string())  # copy of the real state, so that we don't modify the it while checking
       expected_score = 0

       for outcome in outcomes:  # compiling all the possible changes
           probability = outcome.percentage / 100  #
           next_state = play_state.apply_instructions(outcome)
           if my_move in battle.available_switches: # special logic for switches
               current_opp_mult = battle.active_pokemon.damage_multipler(opponent_move) # badness for the current pokemon
               new_opp_mult = next((mon for mon in battle.available_switches if mon.species == to_id_str(my_move))).damage_multipler(opponent_move) # badness for another pokemon
               if new_opp_mult == 0:
                   new_opp_mult = 0.1 #avoid dividing by zero, so we assume its the next step down but slightly better since its 0, so instead of 1/8 its 1/10
               expected_score += probability * SWITCH_WEIGHT * (math.log(current_opp_mult,2)-math.log(new_opp_mult,2)) # turning the geometric relation of the mults into an arithmetic one like damage, plus weighting it

           else:
               expected_score += probability * self.evaluate_move(next_state)
           play_state.reverse_instructions(outcome)  # revert back to the true state. this could be the source of a future bug

       return expected_score
   def choose_move(self, battle: Battle):





       # need actions we can do, actions the opponent can do afterward, and the outcomes for each of those.
       # for simplicity rn, we're just going to track the minimax of damage


       # The form of these battles is not made for Minimax, as i have learned,
       # due to it not being Zero-sum (the opponent doesnt lose as "much" as the player wins each turn)


       # The setup is a matrix with each of the player's actions on one side, and each of the opponent's actions on the other, and each value is the "score" of that path.
       # Because of that, the "score" for this is going to be the net damage. This is heavily subject to change, depending on if it's comprehensive


       # also add alpha-beta pruning at some point
       try:

           state = translate.battle_to_state(battle)
           my_options = self.my_options(battle)
           opponent = battle.opponent_active_pokemon
           their_options = self.opponent_options(state)
           if battle.available_moves:  # can attack
               results = [[(self.expected_value(battle, my_move, their_move), my_move) for their_move in
                           their_options] for my_move in my_options.keys()]
               maximum_options = []
               for i in range(len(list(opponent.moves.values()))):
                   maximum_options[i] = max(results[i])
               return my_options[min(maximum_options)[1]]
           else:
               return self.choose_random_move(battle)
       except Exception as error:
           print(f"[{battle.battle_tag} turn {battle.turn}] fallback to random: {error!r}")
           return self.choose_random_move(battle)