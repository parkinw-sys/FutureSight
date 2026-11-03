from poke_engine import Move as EngineMove
from poke_engine import Pokemon as EnginePokemon
from poke_engine import Side, State

from poke_env.battle import Status
from poke_env.data import GenData
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