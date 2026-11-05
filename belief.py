import json
import random
from pathlib import Path
from poke_env.data.normalize import to_id_str
from poke_env.teambuilder.teambuilder_pokemon import TeambuilderPokemon
from poke_env.teambuilder.smogon_stats_teambuilder import complete_team
from poke_env.teambuilder import Teambuilder
from poke_env.battle import Pokemon

file_path = Path(__file__).parent / "data" / "gen9randombattle.json" # these pre-determined pokemon movesets are provided by pokemon showdown

def convert_names(moveset):
    return {to_id_str(name): move for name, move in moveset.items()}

def load_randbats_movesets():
    with open(file_path, "r") as f:
        raw_randbats_movesets = json.load(f)

        randbats_movesets = {}

        for species, info in raw_randbats_movesets.items():
            roles = {}

            for role_name, role_info in info.get("roles", {}).items():
                roles[role_name] = {
                    "weight": role_info.get("weight", 1.0),
                    "moves": convert_names(role_info.get("moves", {})),
                    "abilities": convert_names(role_info.get("abilities", {})),
                    "items": convert_names(role_info.get("items", {})),
                    "tera_types": convert_names(role_info.get("teraTypes", {})),
                }

            randbats_movesets[to_id_str(species)] = {"roles": roles}
    
    return randbats_movesets

class GuessedSet:
    def __init__(self, moves, ability, item, tera_type, role):
        self.moves = moves
        self.ability = ability
        self.item = item
        self.tera_type = tera_type
        self.role = role

def pick_option(weights, rng=None):
    if not weights:
        return None

    if rng is None:
        best_option = None
        best_weight = float("-inf")

        for option, weight in weights.items():
            if weight > best_weight:
                best_option = option
                best_weight = weight

        return best_option

    options = list(weights.keys())
    options_weights = list(weights.values())
    best_option = rng.choices(options, weights=options_weights, k=1)[0]

    return best_option


def role_matches_revealed(role, revealed_moves, revealed_item, revealed_ability, revealed_tera):
    for move_id in revealed_moves:
        if move_id not in role["moves"]:
            return False
 
    if revealed_item is not None and role["items"]:
        if revealed_item not in role["items"]:
            return False
 
    if revealed_ability is not None and role["abilities"]:
        if revealed_ability not in role["abilities"]:
            return False
 
    if revealed_tera is not None and role["tera_types"]:
        if revealed_tera not in role["tera_types"]:
            return False
 
    return True

def to_teambuilder(pokemon: Pokemon) -> TeambuilderPokemon:
    norm_moves: list[str]
    for mv in pokemon.moves.values():
        norm_moves.append(mv.id)
    
    return TeambuilderPokemon(
        species=pokemon.species,
        item=pokemon.item if pokemon.item else None,
        ability=pokemon.ability if pokemon.ability else None,
        moves=norm_moves,
        level=pokemon.level if pokemon.level else None,
        gender=pokemon.gender if pokemon.gender else None,
        tera_type=pokemon.tera_type if pokemon.tera_type else None
    )

def to_poke(pokemon: TeambuilderPokemon) -> Pokemon:
    species = to_id_str(pokemon.species)
    final_poke = Pokemon(gen=9, species=species)
    for move_id in pokemon.moves:
        cleaned_id = to_id_str(move_id)
        final_poke._add_move(cleaned_id)
    
    if pokemon.item:
        final_poke.item = pokemon.item
    if pokemon.ability:
        final_poke.ability = pokemon.ability
    if pokemon.level:
        final_poke.level = pokemon.level
    if pokemon.gender:
        final_poke.gender = pokemon.gender
    if pokemon.tera_type:
        final_poke.tera_type = pokemon.tera_type
    
    return final_poke

def guess_team(pokemon: Pokemon):
    seed_pokemon = to_teambuilder(pokemon)
    team = complete_team(
        partial_team=[seed_pokemon],
        battle_format="gen9ou",
        team_strategy="greedy",
        pokemon_strategy="greedy"
    )

def guess_set(pokemon, randbats_movesets, rng=None):
    species_info = randbats_movesets.get(to_id_str(pokemon.species))

    if species_info is None or not species_info["roles"]:
        return None

    revealed_moves = list(pokemon.moves.keys())
    
    revealed_item = None
    if pokemon.item is not (None, "", "unknown_item"):
        revealed_item = pokemon.item

    revealed_ability = None
    if pokemon.ability is not None:
        revealed_ability = pokemon.ability
    
    revealed_tera_type = None
    if pokemon.is_terastallized and pokemon.tera_type is not None:
        revealed_tera_type = pokemon.tera_type.name.lower()

    possible_roles = {}

    for role_name, role_info in species_info["roles"].items(): # narrows down possible roles based on revealed information
        if role_matches_revealed(role_info, revealed_moves, revealed_item, revealed_ability, revealed_tera_type):
            possible_roles[role_name] = role_info

    if not possible_roles: # nothing fits the revealed information
        possible_roles = species_info["roles"]

    # based on weights, pick role, moves, item, ability, and tera type

    role_weights = {}
    for role_name, role_info in possible_roles.items():
        role_weights[role_name] = role_info["weight"]
 
    chosen_role_name = pick_option(role_weights, rng)
    chosen_role = possible_roles[chosen_role_name]

    guessed_moves = revealed_moves[:4] # if all moves are revealed, then no need to guess any more moves
 
    remaining_moves = {}
    for move_id, weight in chosen_role["moves"].items():
        if move_id not in guessed_moves:
            remaining_moves[move_id] = weight
 
    while len(guessed_moves) < 4 and remaining_moves:
        next_move = pick_option(remaining_moves, rng)
        guessed_moves.append(next_move)
        remaining_moves.pop(next_move)

    item = revealed_item
    if item is None:
        item = pick_option(chosen_role["items"], rng)
    if item is None:
        item = "none"

    ability = revealed_ability
    if ability is None:
        ability = pick_option(chosen_role["abilities"], rng)
    if ability is None:
        ability = "none"

    tera_type = revealed_tera_type
    if tera_type is None:
        tera_type = pick_option(chosen_role["tera_types"], rng)
    if tera_type is None:
        tera_type = "typeless"

    return GuessedSet(
        moves=guessed_moves,
        item=item,
        ability=ability,
        tera_type=tera_type,
        role=chosen_role_name,
    )