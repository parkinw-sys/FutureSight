from poke_env import Player
from poke_env.battle.pokemon import Pokemon
from poke_env.battle import Battle
from poke_env.calc import calculate_damage
from poke_env.calc.damage_calc_gen1_2 import calculate_damage_gen12
from poke_env.data import GenData
from poke_env.stats import compute_raw_stats_dvs
    
class BattleState:
    def __init__(self, team: dict(str, Pokemon), o_team: dict(str, Pokemon), active_pokemon: Pokemon, o_active_pokemon: Pokemon, weather: Battle.weather):
        self.team = team
        self.o_team = o_team
        self.active_pokemon = active_pokemon
        self.o_active_pokemon = o_active_pokemon
        self.weather = weather

# Node class, storing a battle state while implementing tree functionality
class MCTSNode:
    def __init__(self, parent: MCTSNode, team: list(Pokemon), o_team: list(Pokemon), active_pokemon: Pokemon, o_active_pokemon: Pokemon, weather: Battle.weather):
        self.parent = parent
        self.children = []
        self.state = BattleState(team, o_team, active_pokemon, o_active_pokemon, weather)
        self.visits = 0
        self.reward = 0.0
        self.action =
    
    def visit():
        self.visits+=1
    
    




class MCTS(Player):
    def choose_move(self, battle: Battle):
        root_state = BattleState(battle.team, battle.opponent_team, battle.active_pokemon, battle.opponent_active_pokemon, battle.weather)
        return
        # choose a move based on MC tree search

