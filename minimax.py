import asyncio
import time
from pickle import EMPTY_LIST
from poke_env import *
from poke_env.battle import Battle, PokemonType
import translate
from poke_engine import Side, State, generate_instructions
import math

SWITCH_WEIGHT = 0.1  # less than 1, probably less than 1/6.
# this is to keep the switching scores on par with damage scores
# a difference between effectiveness "levels" is 1 bc of logarithms,

"""
The Minimax algorithm implementation for running a pokemon showdown bot.
"""
class Minimax(Player):
    """
    This function gives a Poke_engine state a "score" so the
    combinatorial Minimax function can actually compare different moves.
    Works by finding the average percentage health of each side, then taking the
    difference between our side and their side's average health.
    """
    def evaluate_move(self, state):
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
    """
    This generates a dictionary of all the possible moves that the bot can do, including 
    switches and terastallizing. this allows us to make the table
    .
    The key is the id of the move for processing, and the value is the move order itself.
    """
    def my_options(self, battle):
        legal_actions = {}

        for move in battle.available_moves:
            legal_actions[move.id] = Player.create_order(move)
            if battle.can_tera:
                legal_actions[f"{move.id}-tera"] = Player.create_order(move, terastallize=True)

        for pokemon in battle.available_switches:
            legal_actions[pokemon.species] = Player.create_order(pokemon)

        return legal_actions


    """
    This is similar to my_options, but for the bot's opponent.
    """
    def opponent_options(self, state):
        active_index = int(state.side_two.active_index) # after a switch, opponent's active pokemon isn't necessarily at index 0 in the list
        opponent = state.side_two.pokemon[active_index]
        options = []

        switches = []
        for index, pokemon in enumerate(state.side_two.pokemon):
            if index == active_index:
                continue
            if pokemon.hp > 0:
                switches.append(str(pokemon.id).lower())

        if opponent.hp <= 0:
            return switches

        for move in opponent.moves:
            options.append(move.id)

        options.extend(switches)

        return options
    """
    This is the logic for converting the battle state into scores for Minimax to work on.
    
    It uses Poke-engine's generate_instructions function, which outputs every possible outcome (due to accuracies, crit chance, etc) 
    of a pair of moves on a given state.
    
    Then, it applies each of the outcomes separately to a copy of the current state, and we evaluate the 
    change in "score" using our evaluate algorithms
    
    Switching is more complicated; it just compares the type advantage the opponent has, and returns a score of how
    much better or worse the type matchup is when we switch. The multipliers are logarithmised, to keep the change linear
    
    """
    def expected_value(self, battle, my_move, opponent_move):
        state = translate.battle_to_state(battle)
        outcomes = generate_instructions(state, my_move, opponent_move) # all possible outcomes of a set of moves
        play_state = State.from_string(
            state.to_string())  # copy of the real state, so that we don't modify the real one while checking
        expected_score = 0

        for outcome in outcomes:  # compiling all the possible changes
            probability = outcome.percentage / 100  #
            next_state = play_state.apply_instructions(outcome)
            if my_move in battle.available_switches:  # special logic for switches
                try:
                    opponent_move = PokemonType.from_name(opponent_move) # if the opponent is switching, grab it's type instead
                finally:
                    current_opp_mult = battle.active_pokemon.damage_multipler(
                        opponent_move)  # badness for our pokemon
                    new_opp_mult = next(
                        (mon for mon in battle.available_switches if mon.species == to_id_str(my_move))).damage_multipler(
                        opponent_move)  # badness for another pokemon, if we switched to it
                    if new_opp_mult == 0:
                        new_opp_mult = 0.1  # avoid dividing by zero, so we assume its the next
                        # step down but slightly better since its 0, so instead of 1/8 its 1/10
                    expected_score += probability * SWITCH_WEIGHT * (math.log(current_opp_mult, 2) - math.log(new_opp_mult,
                                                                                                          2))  # turning the geometric relation of the mults into an arithmetic one like damage, plus weighting it

            else:
                expected_score += probability * self.evaluate_move(next_state)
            play_state.reverse_instructions(outcome)  # revert back to the true state. this could be the source of a future bug

        return expected_score
    """
    this function is for displying the score table, and is purely for debugging
    """
    def debug(self, results, my_options, their_options):
        header = ["Debug"]
        header.extend(their_options)
        print(header)
        i = 0
        for option in my_options:
            addition = [option]
            addition.extend(results[i])
            i += 1
            print(addition)
        print()
        print("-----")
        print()

    """
    This function is the main algorithm for Minimax (in this case, Maximin, which is a type of minimax)
    it uses the APIs to gather the player and battle data, makes the payoff table, and chooses the best option.
    Minimax algorithms tend to choose the best option they can guaruntee themselves, so are pretty conservative.
    """
    def choose_move(self, battle: Battle):

        try:
            start_time = time.perf_counter()
            print(f"[turn {battle.turn}] Minimax thinking...")

            state = translate.battle_to_state(battle) # turning the poke_env's battle into poke_engine's state
            my_options = self.my_options(battle)

            opponent = battle.opponent_active_pokemon
            their_options = self.opponent_options(state)
            if not battle.available_moves:
                their_options = ["none"]
                print("none")
            # does the active pokemon have the ability to do anything
            # results is the payoff table that the algorithm decides with
            results = [[(self.expected_value(battle, my_move, their_move), my_move) for their_move in
                        their_options] for my_move in list(my_options.keys())]
            maximum_options = []
            # self.debug(results, list(my_options.keys()), their_options)
            for i in range(len(list(my_options.keys()))):
                op = min(results[i])
                maximum_options.append(op)

            elapsed = time.perf_counter() - start_time
            print(f"[turn {battle.turn}] Minimax done thinking in {elapsed:.1f}s")

            return my_options[max(maximum_options)[1]]
        except Exception as error:
            print(f"[{battle.battle_tag} turn {battle.turn}] fallback to random: {error!r}")
            return self.choose_random_move(battle)

'''
This is just code for running the bot on a localhost server, so it can play on Pokemon Showdown
'''
async def main():
    bot = Minimax(
        account_configuration=AccountConfiguration("FutureSightBot", None),
        battle_format="gen9randombattle",
        save_replays=True,
    )
    print("Waiting for a challenge... challenge FutureSightBot at http://localhost:8000")
    await bot.accept_challenges(None, 1)  # None = accept from anyone, 1 = one battle
    print(f"Done. Bot won {bot.n_won_battles} of {bot.n_finished_battles}")


if __name__ == "__main__":
    asyncio.run(main())
