import asyncio

from poke_engine import Move as EngineMove
from poke_engine import Pokemon as EnginePokemon
from poke_engine import Side, State, generate_instructions

from poke_env import AccountConfiguration
from poke_env.battle import Status
from poke_env.data import GenData
from poke_env.player import Player, RandomPlayer
from poke_env.stats import compute_raw_stats


GEN_DATA = GenData.from_gen(9)

VALID_TYPES = {
    "normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison",
    "ground", "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark",
    "steel", "fairy", "stellar",
}

STATUS_NAMES = {
    Status.BRN: "burn", Status.SLP: "sleep", Status.FRZ: "freeze",
    Status.PAR: "paralyze", Status.PSN: "poison", Status.TOX: "toxic",
}

PLACEHOLDER_MOVE = "tackle"  # implement belief model later

# poke-env to poke-engine conversions

def type_name(pokemon_type):
    if pokemon_type is None:
        return "typeless"
    
    name = pokemon_type.name.lower()

    if name not in VALID_TYPES:
        return "typeless"
    
    return name

def engine_types(pokemon):
    types = []

    for pokemon_type in pokemon.types[:2]: # poke-engine can only handle up to 2 types per pokemon
        types.append(type_name(pokemon_type))

    while len(types) < 2:
        types.append("typeless")

    return tuple(types)

def randbats_stats(pokemon):
    hp, attack, defense, sp_attack, sp_defense, speed = compute_raw_stats(
        pokemon.species, 
        [85] * 6, 
        [31] * 6, 
        pokemon.level, 
        "serious", # serious is a neutral nature
        GEN_DATA,
    )

    return {"hp": hp, "atk": attack, "def": defense, "spa": sp_attack, "spd": sp_defense, "spe": speed}

def to_engine_pokemon(pokemon, is_mine):
    if is_mine:
        stats = pokemon.stats
        max_hp = pokemon.max_hp
        current_hp = pokemon.current_hp

        moves = []
        for move in pokemon.moves.values():
            engine_move = EngineMove(id=move.id, pp=move.current_pp)
            moves.append(engine_move)

        item = pokemon.item or "none"
        ability = pokemon.ability or "none"

    else:
        stats = randbats_stats(pokemon)
        max_hp = stats["hp"]
        current_hp = round(pokemon.current_hp_fraction * max_hp) # pokemon showdown displays opponent HP as %
        
        moves = []
        for move in pokemon.moves.values():
            engine_move = EngineMove(id=move.id, pp=move.current_pp)
            moves.append(engine_move)
        
        if not moves:
            moves = [EngineMove(id=PLACEHOLDER_MOVE)] # belief model later

        item = "none" # belief model later
        ability = "none" # belief model later

        if pokemon.fainted:
            current_hp = 0

    return EnginePokemon(
        id=pokemon.species,
        level=pokemon.level,
        types=engine_types(pokemon),
        base_types=engine_types(pokemon),
        hp=current_hp,
        maxhp=max_hp,
        item=item,
        ability=ability,
        attack=stats["atk"],
        defense=stats["def"],
        special_attack=stats["spa"],
        special_defense=stats["spd"],
        speed=stats["spe"],
        status=STATUS_NAMES.get(pokemon.status, "none"),
        terastallized=pokemon.is_terastallized,
        tera_type=type_name(pokemon.tera_type),
        moves=moves[:4],
    )

def to_engine_side(team, active, is_mine):
    ordered_pokemon = [active]

    for pokemon in team.values():
        if pokemon is not active:
            ordered_pokemon.append(pokemon)

    boosts = active.boosts

    engine_pokemon = []

    for pokemon in ordered_pokemon:
        engine_pokemon.append(to_engine_pokemon(pokemon, is_mine))

    return Side(
        pokemon=engine_pokemon,
        attack_boost=boosts.get("atk", 0),
        defense_boost=boosts.get("def", 0),
        special_attack_boost=boosts.get("spa", 0),
        special_defense_boost=boosts.get("spd", 0),
        speed_boost=boosts.get("spe", 0),
        accuracy_boost=boosts.get("accuracy", 0),
        evasion_boost=boosts.get("evasion", 0),
    )

def battle_to_state(battle):
    # weather, terrain, trick room, hazards to be implemented later
    return State(
        side_one=to_engine_side(battle.team, battle.active_pokemon, True),
        side_two=to_engine_side(battle.opponent_team, battle.opponent_active_pokemon, False),
    )

# evaluation function for the game state (minimax) PROBABLY GONNA MOVE THIS TO A DIFFERENT FILE LATER

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

async def main():
    bot = OneTurnPlayer(battle_format="gen9randombattle", save_replays=True)
    opponent = RandomPlayer(battle_format="gen9randombattle")
    await bot.battle_against(opponent, n_battles=20)
    print(f"OneTurnPlayer won {bot.n_won_battles} of {bot.n_finished_battles}")

# async def main():
#     bot = OneTurnPlayer(
#         account_configuration=AccountConfiguration("FutureSightBot", None),
#         battle_format="gen9randombattle",
#         save_replays=True,
#     )
#     print("Waiting for a challenge... challenge FutureSightBot at http://localhost:8000")
#     await bot.accept_challenges(None, 1)   # None = accept from anyone, 1 = one battle
#     print(f"Done. Bot won {bot.n_won_battles} of {bot.n_finished_battles}")

if __name__ == "__main__":
    asyncio.run(main())