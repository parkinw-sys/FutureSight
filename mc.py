from poke_env import Player
from poke_env.battle import Battle
from poke_env.calc import calculate_damage
from poke_env.calc.damage_calc_gen1_2 import calculate_damage_gen12
from poke_env.data import GenData
from poke_env.stats import compute_raw_stats_dvs

# need to populate nodes    

class PokeState:
    def __init__(self, species: str, hp: int, max_hp: int, stats: dict, boosts: dict | None, moves: tuple):
        self.species = species
        self.hp = hp
        self.max_hp = max_hp
        self.stats = stats
        self.boosts = boosts
        self.moves = moves

    

# Node class, storing a battle state
class MCTSNode:
    def __init__(self):
        self.parent = None
        self.children = None



class MCTS(Player):
    def choose_move(self, battle):
        return
        # choose a move based on MC tree search

