from poke_env import Player
from poke_env.battle import Battle
from poke_engine import generate_instructions, State
import translate
import random
import copy
    
# however, this data needs to be updated node-by-node, so poke-env data from battle object needs to be 
# abstracted into this format 

# Node class, storing a battle state while implementing tree functionality
class MCTSNode:
    def __init__(self, state: State, action=None):
        self.parent = parent
        self.children = []
        self.state = state
        self.visits = 0
        self.reward = 0.0
        self.action = action
        self.available_actions = []
        self.terminal = False
    
    def visit(self):
        self.visits+=1
        
    def init_actions(self):
        legal_actions = []
        for move in self.state.side_one.pokemon[self.state.side_one.active_index].moves:
            if move.pp > 0 and move.disabled is False:
                legal_actions.append[str(move.id).lower()]
        for pokemon in self.state.side_one.pokemon and pokemon is not self.state.side_one.pokemon[self.state.side_one.active_index]:
            if pokemon.hp != 0:
                legal_actions.append[str(pokemon.id).lower()]
        self.available_actions = legal_actions


    # check if a leaf node has been reached
    def is_terminal(self):
        for pokemon in self.state.side_one.pokemon:
            if pokemon.hp > 0:
                return False
        for pokemon in self.state.side_two.pokemon:
            if pokemon.hp > 0:
                return False
        return True

    def explore(self) -> MCTSNode:
        if self.is_terminal: return None # if terminal, no need to generate new nodes
        
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
    
    def back_prop(self):
        return

class MCTS(Player):
    def choose_move(self, battle: Battle):
        root_state = translate.battle_to_state(battle) # should hold a poke-engine state
        root_node = MCTSNode(state=root_state)

        return
        # choose a move based on MC tree search

