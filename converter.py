from poke_engine import Pokemon as EngineMon
from poke_engine import Move as EngineMove
from poke_engine import State as EngineState
from poke_engine import Side as EngineSide
from poke_engine import PokemonIndex
from poke_env.battle.pokemon import Pokemon
from poke_env.battle import Battle as init_battle
from poke_env import to_id_str

# Convert poke-env pokemon into poke-engine pokemon for MCTS node states

# poke-env has function for normalizing pokemon species strings
def normalize(name: str) -> str:
    return to_id_str(name)

# an EngineMon requires attributes (species, level, types, etc.) to be transferred from poke-env pokemon
# convert_pokemon: take these attributes from poke-env pokemon and map them into poke-engine pokemon
def convert_pokemon(pokemon: Pokemon) -> EngineMon:
    species = normalize(pokemon.species)
    stats = pokemon.stats
    types = [t.name.lower() for t in pokemon.types if t is not None]
    # since poke-engine expects 2 type strings, a one-typed pokemon must have a second type of "typeless"
    if len(types) == 1:
        types.append("typeless")

    moves = [
        EngineMove(
            id=normalize(move.id),
            pp=move.current_pp,
            disabled=False
        ) for move in pokemon.moves.values()
    ]

    return EngineMon(
        id=species,
        level=pokemon.level,
        types=tuple(types),
        hp=pokemon.current_hp,
        maxhp=pokemon.max_hp,
        ability=normalize(pokemon.ability),
        item=normalize(pokemon.item),
        attack=stats["atk"],
        defense=stats["def"],
        special_attack=stats["spa"],
        special_defense=stats["spd"],
        speed=stats["spe"],
        moves=moves
    )

# function to convert an entire team at once
def convert_team(team: dict[str, Pokemon]) -> list(EngineMon):
    # learning list/dictionary comprehensions yay :)
    return [convert_pokemon(mon) for mon in team.values()]
    

# turn converted teams and battle into a full state that poke-engine can configure and gen instructions for
def convert_battle(battle: init_battle) -> EngineState:
    converted_team = convert_team(battle.team)
    converted_o_team = convert_team(battle.opponent_team)

    active_index: int
    active_o_index: int
    # side_conditions = battle.side_conditions

    for i in enumerate(converted_team):
        if converted_team[i].id == normalize(battle.active_pokemon.species):
            active_index = i
            break
    for i in enumerate(converted_o_team):
        if converted_o_team[i].id == normalize(battle.opponent_active_pokemon.species):
            active_o_index = i
            break

    sideOne = EngineSide(
        active_index=active_index,
        pokemon=converted_team#,
        # side_conditions=
    )
    sideTwo = EngineSide(
        active_index=active_o_index,
        pokemon=converted_o_team#,
        # side_conditions=
    ) 

    return EngineState(
        side_one=sideOne,
        side_two=sideTwo,
    )
    