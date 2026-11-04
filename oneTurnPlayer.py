import asyncio

from translate import battle_to_state

from poke_engine import generate_instructions

from poke_env import Player, RandomPlayer
from poke_env import AccountConfiguration

def evaluate(state):
    my_score = 0
    opponent_score = 0

    for pokemon in state.side_one.pokemon:
        if pokemon.maxhp > 0:
            my_score += pokemon.hp / pokemon.maxhp

    for pokemon in state.side_two.pokemon:
        if pokemon.maxhp > 0:
            opponent_score += pokemon.hp / pokemon.maxhp

    unseen_pokemon = 6 - len(state.side_two.pokemon) # accounting for opponent's unseen pokemon
    opponent_score += unseen_pokemon

    return (my_score - opponent_score) / 6

def my_options(battle):
    legal_actions = {}

    for move in battle.available_moves:
        legal_actions[move.id] = Player.create_order(move)
        if battle.can_tera:
            legal_actions[f"{move.id}-tera"] = Player.create_order(move, terastallize=True)

    for pokemon in battle.available_switches:
        legal_actions[pokemon.species] = Player.create_order(pokemon)

    return legal_actions


def opponent_options(state):
    # opponent switches to be implemented later
    opponent = state.side_two.pokemon[0]
    moves = []

    for move in opponent.moves:
        moves.append(move.id)

    return moves

# Search (depth 1)

def expected_value(state, my_move, opponent_move):
    outcomes = generate_instructions(state, my_move, opponent_move)

    expected_score = 0

    for outcome in outcomes:
        probability = outcome.percentage / 100
        next_state = state.apply_instructions(outcome)
        expected_score += probability * evaluate(next_state)

    return expected_score

class OneTurnPlayer(Player): # minimax player (depth 1)
    def choose_move(self, battle):
        if battle.active_pokemon is None or battle.opponent_active_pokemon is None:
            return self.choose_random_move(battle)
        
        try:
            state = battle_to_state(battle)
            legal_actions = my_options(battle)
            best_option = None
            best_score = float("-inf")

            for my_move in legal_actions:
                worst_score = float("inf")

                for opponent_move in opponent_options(state):
                    score = expected_value(state, my_move, opponent_move)
                    worst_score = min(worst_score, score)

                if worst_score > best_score:
                    best_option = my_move
                    best_score = worst_score

            return legal_actions[best_option]
        
        except Exception as error:
            print(f"[{battle.battle_tag} turn {battle.turn}] fallback to random: {error!r}")
            return self.choose_random_move(battle)

# async def main():
#     bot = OneTurnPlayer(battle_format="gen9randombattle", save_replays=True)
#     opponent = RandomPlayer(battle_format="gen9randombattle")
#     await bot.battle_against(opponent, n_battles=20)
#     print(f"OneTurnPlayer won {bot.n_won_battles} of {bot.n_finished_battles}")

async def main():
    bot = OneTurnPlayer(
        account_configuration=AccountConfiguration("FutureSightBot", None),
        battle_format="gen9randombattle",
        save_replays=True,
    )
    print("Waiting for a challenge... challenge FutureSightBot at http://localhost:8000")
    await bot.accept_challenges(None, 1)   # None = accept from anyone, 1 = one battle
    print(f"Done. Bot won {bot.n_won_battles} of {bot.n_finished_battles}")

if __name__ == "__main__":
    asyncio.run(main())