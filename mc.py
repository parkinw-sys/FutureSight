from poke_env import Player
from poke_env.battle.pokemon import Pokemon
from poke_env.battle import Battle
from poke_env.calc import calculate_damage
from poke_env.data import GenData
from poke_env.stats import compute_raw_stats_dvs
from poke_engine import generate_instructions
import translate
    
# however, this data needs to be updated node-by-node, so poke-env data from battle object needs to be 
# abstracted into this format 

# Node class, storing a battle state while implementing tree functionality
class MCTSNode:
    def __init__(self, state, action=None):
        self.parent = parent
        self.children = []
        self.state = 
        self.visits = 0
        self.reward = 0.0
        self.action = action
        self.available_actions = []
    
    def visit(self):
        self.visits+=1
    
    def available_switches(self):
        return {name: mon for name, mon in self.state.team if not mon.fainted and not self.state.active_pokemon}

    def get_actions(self):
        self.available_actions = self.state.active_pokemon.base_moves + self.available_switches()

    def expand(self):
        
        return
    
    def back_prop(self):
        return

class MCTS(Player):
    def choose_move(self, battle: Battle):
        root_state = translate.battle_to_state(battle) # should hold a poke-engine state
        root_node = MCTSNode(

        )

        return
        # choose a move based on MC tree search

