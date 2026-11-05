from poke_env import Player, AccountConfiguration
from poke_env.battle import Battle
from poke_engine import generate_instructions, State
from translate import battle_to_state 
import random
import copy
import asyncio
import math
import copy
    
# however, this data needs to be updated node-by-node, so poke-env data from battle object needs to be 
# abstracted into this format 

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

def get_available_actions(state: State):
    legal_actions = []
    for move in state.side_one.pokemon[state.side_one.active_index].moves:
        if move.pp > 0 and move.disabled is False:
            legal_actions.append[str(move.id).lower()]
    for pokemon in state.side_one.pokemon and pokemon is not state.side_one.pokemon[state.side_one.active_index]:
        if pokemon.hp != 0:
            legal_actions.append[str(pokemon.id).lower()]
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
        self.available_actions = get_available_actions(state)
        self.terminal = is_terminal(state)
    
    def visit(self):
        self.visits+=1
    
    def expand(self) -> MCTSNode:
        if self.terminal: return None # if terminal, no need to generate new nodes
        
        rand_idx = random.randint(0, self.available_actions.__sizeof__-1)
        side_one_action = self.available_actions.pop(rand_idx)
        side_two_placeholder = "tackle"

        instructions = generate_instructions(self.state, side_one_action, side_two_placeholder) # instructions: list of possible outcomes
        chosen_instruction = instructions[random.randint(0, instructions.__sizeof__-1)]
        new_state = copy.deepcopy(self.state) # must copy state to prevent current state from updating
        # probably suboptimal, can be enhanced using poke-engine state reversion
        new_state.apply_instructions(chosen_instruction) # generate new state

        new_node = MCTSNode(new_state, action=chosen_instruction)
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
        sim_state = copy.deepcopy(self.state)
        while not is_terminal(sim_state):
            legal_actions = get_available_actions(sim_state)
            if not legal_actions: 
                return None
            move = random.choice(legal_actions)
            instruction = random.choice(
                generate_instructions(self.state, side_one_action, side_two_placeholder))
            sim_state.apply_instructions(instruction)
        return get_reward(sim_state)
        
    def back_prop(self, reward: int):
        self.visits+=1
        self.reward+=reward
        if self.parent:
            self.parent.back_prop()

class MCTS(Player):
    def choose_move(self, battle: Battle):
        try:
            root_state = battle_to_state(battle) # should hold a poke-engine state
            root_node = MCTSNode(state=root_state)

            return
        
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