from poke_env import Player
from poke_env.battle.pokemon import Pokemon
from poke_env.battle import Battle
from poke_env.calc import calculate_damage
from poke_env.data import GenData
from poke_env.stats import compute_raw_stats_dvs
    
# BattleState stores current info about the battle, notably that provided by poke-env
# however, this data needs to be updated node-by-node, so poke-env data from battle object needs to be 
# abstracted into this format 
class BattleState:
    def __init__(self, team: dict[str, Pokemon], o_team: dict[str, Pokemon], active_pokemon: Pokemon, o_active_pokemon: Pokemon, weather: Battle.weather):
        self.team = team
        self.o_team = o_team
        self.active_pokemon = active_pokemon
        self.o_active_pokemon = o_active_pokemon
        self.weather = weather

# Node class, storing a battle state while implementing tree functionality
class MCTSNode:
    def __init__(self, team: dict[str, Pokemon], o_team: dict[str, Pokemon], active_pokemon: Pokemon, o_active_pokemon: Pokemon, weather: Battle.weather, parent: MCTSNode, action=None):
        self.parent = parent
        self.children = []
        self.state = BattleState(team, o_team, active_pokemon, o_active_pokemon, weather) # to be passed in updated by parent node
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
        root_state = BattleState(battle.team, battle.opponent_team, battle.active_pokemon, battle.opponent_active_pokemon, battle.weather)

        return
        # choose a move based on MC tree search

