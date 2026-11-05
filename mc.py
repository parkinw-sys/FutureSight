from __future__ import annotations 
from poke_env import Player, AccountConfiguration
from poke_env.battle import Battle
from poke_engine import generate_instructions, State
from translate import battle_to_state 
import random
import copy
import asyncio
import math
import copy
import time
    
# however, this data needs to be updated node-by-node, so poke-env data from battle object needs to be 
# abstracted into this format 

ITERATIONS = 10000

# check if a leaf node has been reached
def is_terminal(state: State):
    side_one_alive = False
    side_two_alive = False
    for pokemon in state.side_one.pokemon:
        if pokemon.hp > 0:
            side_one_alive = True
    for pokemon in state.side_two.pokemon:
        if pokemon.hp > 0:
            side_two_alive = True
    return not side_one_alive or not side_two_alive 

# only after is_terminal, returns 1 if won 0 if not
def get_reward(state: State):
    for pokemon in state.side_one.pokemon:
        if pokemon.hp > 0:
            return 1
    return 0

def get_available_actions(side):
    legal_actions = []

    active_index = int(side.active_index)
    active_pokemon = side.pokemon[active_index]

    tera_used = False
    for pokemon in side.pokemon:
        if pokemon.terastallized:
            tera_used = True

    if active_pokemon.hp > 0:
        for move in active_pokemon.moves:
            if move.pp > 0 and not move.disabled:
                legal_actions.append(str(move.id).lower())
                if not tera_used and not active_pokemon.terastallized:
                    legal_actions.append(f"{move.id}-tera")

    for index, pokemon in enumerate(side.pokemon):
        if index == active_index:
            continue
        if pokemon.hp > 0:
            legal_actions.append(str(pokemon.id).lower())

    return legal_actions

# Node class, storing a battle state while implementing tree functionality
class MCTSNode:
    def __init__(self, state: State, parent: MCTSNode=None, action: str=None, opponent_action: str=None):
        self.parent = parent
        self.children: list[MCTSNode] = []
        self.state = state
        self.visits = 0
        self.reward = 0
        self.action = action
        self.opponent_action = opponent_action
        self.available_actions = get_available_actions(state.side_one)
        self.available_o_actions = get_available_actions(state.side_two)
        self.terminal = self.is_terminal()
    
    def visit(self):
        self.visits+=1
    
    def is_terminal(self):
        return is_terminal(self.state)
    
    def get_reward(self):
        return get_reward(self.state)

    def expand(self) -> MCTSNode:
        if self.terminal: return None # if terminal, no need to generate new nodes

        if not self.available_actions:
            raise ValueError("No available side 1 actions in expand")
        if not self.available_o_actions:
            raise ValueError("No available side 2 actions in expand")

        rand_idx = random.randint(0, len(self.available_actions)-1)
        side_one_action = self.available_actions.pop(rand_idx)
        rand_idx = random.randint(0, len(self.available_o_actions)-1)
        side_two_action = self.available_o_actions[rand_idx]

        instruction = random.choice(generate_instructions(self.state, side_one_action, side_two_action)) # instructions: list of possible outcomes
        new_state = self.state.apply_instructions(instruction) # apply_instructions makes a state copy, then returns new state without modifying the current one
        # probably suboptimal, can be enhanced using poke-engine state reversion

        new_node = MCTSNode(new_state, parent=self, action=side_one_action, opponent_action=side_two_action)
        self.children.append(new_node)

        return new_node
    
    # GeeksForGeeks (https://www.geeksforgeeks.org/machine-learning/monte-carlo-tree-search-mcts-in-machine-learning/) helped, c is a constant in UCT equation
    def best_child(self, c=1.4):
        for child in self.children:
            if child.visits == 0:
                return child
        def ucb(child):
            return child.reward/child.visits + c*math.sqrt(math.log(self.visits) / child.visits)

        return max(self.children, key=ucb)        
        
    # random rollout simulation to assign rewards (also based on GeeksForGeeks page)
    def rollout(self):
        sim_state = self.state
        while not is_terminal(sim_state):
            legal_actions = get_available_actions(sim_state.side_one)
            legal_o_actions = get_available_actions(sim_state.side_two)


            if not legal_actions: 
                raise ValueError("No side 1 actions during rollout")
            if not legal_o_actions:
                raise ValueError("No side 2 actions during rollout")
            
            move = random.choice(legal_actions)
            move_o = random.choice(legal_o_actions)
            instruction = random.choice(
                generate_instructions(sim_state, move, move_o))
            sim_state = sim_state.apply_instructions(instruction)
        return get_reward(sim_state)
        
    def back_prop(self, reward: int):
        self.visits+=1
        self.reward+=reward
        if self.parent:
            self.parent.back_prop(reward)

def my_options(battle):
    legal_actions = {}

    for move in battle.available_moves:
        legal_actions[move.id] = Player.create_order(move)
        if battle.can_tera:
            legal_actions[f"{move.id}-tera"] = Player.create_order(move, terastallize=True)

    for pokemon in battle.available_switches:
        legal_actions[pokemon.species] = Player.create_order(pokemon)

    return legal_actions


class MCTS(Player):
    def choose_move(self, battle: Battle):
        try:
            options = my_options(battle)

            if len(options) == 1:
                return next(iter(options.values()))

            start_time = time.perf_counter()
            print(f"[turn {battle.turn}] thinking...")
            
            root_state = battle_to_state(battle) # should hold a poke-engine state
            root_node = MCTSNode(state=root_state)

            for iteration in range(ITERATIONS):
                node = root_node

                while not node.terminal and not node.available_actions and node.children:
                    node = node.best_child()

                if not node.terminal and node.available_actions:
                    node = node.expand()

                reward = node.rollout()

                node.back_prop(reward)

                if (iteration + 1) % 100 == 0:
                    elapsed = time.perf_counter() - start_time
                    print(f"  {iteration + 1} iterations, {elapsed:.1f}s")

            elapsed = time.perf_counter() - start_time
            print(f"[turn {battle.turn}] done thinking in {elapsed:.1f}s")

            best_child = None
            for child in root_node.children:
                if best_child is None or child.visits > best_child.visits:
                    best_child = child

            if best_child is None or best_child.action not in options:
                return self.choose_random_move(battle)

            return options[best_child.action]

        except Exception as e:
            print(f"Error in choose_move: {e}")
            return self.choose_random_move(battle)


async def main():
    bot = MCTS(
            account_configuration=AccountConfiguration("FutureSightBot", None),
            battle_format="gen9randombattle",
            save_replays=True,
        )
    print("Waiting for a challenge... challenge FutureSightBot at http://localhost:8000")
    await bot.accept_challenges(None, 1)   # None = accept from anyone, 1 = one battle
    print(f"Done. Bot won {bot.n_won_battles} of {bot.n_finished_battles}")

if __name__ == "__main__":
    asyncio.run(main())