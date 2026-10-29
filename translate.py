import asyncio
import random

from poke_engine import Move as Engine_Move
from poke_engine import Pokemon as Engine_Pokemon
from poke_engine import Side, State, generate_instructions
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

PLACEHOLDER_MOVE = "tackle"  # TODO: replace with belief model guesses later


# Translating poke-env information to poke-engine for simulation

def type_name(t):
    name = t.name.lower() if t is not None else "typeless"
    return name if name in VALID_TYPES else "typeless"

def engine_types(mon):
    names = [type_name(t) for t in mon.types][:2] # we take at most 2 types because poke-engine can only handle up to 2 types per Pokemon

    while len(names) < 2:
        names.append("typeless")

    return tuple(names)

def randbats_stats(mon):
    """Opponent stats aren't sent by Showdown. Randbats sets almost all use
    85 EVs and 31 IVs in every stat with a neutral nature, so we compute them."""
    hp, atk, df, spa, spd, spe = compute_raw_stats(
        mon.species, [85] * 6, [31] * 6, mon.level, "serious", GEN_DATA # serious is a neutral nature
    )

    return {"hp": hp, "atk": atk, "def": df, "spa": spa, "spd": spd, "spe": spe}

def to_engine_pokemon(mon, is_mine):
    if is_mine:
        stats = mon.stats
        maxhp = mon.max_hp
        hp = mon.current_hp
        moves = [Engine_Move(id=m.id, pp=m.current_pp) for m in mon.moves.values()]
        item = mon.item or "none"
        ability = mon.ability or "none"

    else:
        stats = randbats_stats(mon)
        maxhp = stats["hp"]
        hp = round(mon.current_hp_fraction * maxhp) # opponent HP is only a %
        moves = [Engine_Move(id=m.id) for m in mon.moves.values()]

        if not moves:
            moves = [Engine_Move(id=PLACEHOLDER_MOVE)] # TODO: belief model

        item = "none"      # TODO: use revealed item once names are checked
        ability = "none"   # TODO: use revealed ability

    return Engine_Pokemon(
        id=mon.species,
        level=mon.level,
        types=engine_types(mon),
        base_types=engine_types(mon),
        hp=0 if mon.fainted else hp,
        maxhp=maxhp,
        item=item,
        ability=ability,
        attack=stats["atk"],
        defense=stats["def"],
        special_attack=stats["spa"],
        special_defense=stats["spd"],
        speed=stats["spe"],
        status=STATUS_NAMES.get(mon.status, "none"),
        terastallized=mon.is_terastallized,
        tera_type=type_name(mon.tera_type),
        moves=moves[:4],
    )

def to_engine_side(team, active, is_mine):
    # Active Pokemon first, so the engine's active_index (P0 by default) points at it.
    ordered = [active] + [m for m in team.values() if m is not active]
    boosts = active.boosts

    return Side(
        pokemon=[to_engine_pokemon(m, is_mine) for m in ordered],
        attack_boost=boosts.get("atk", 0),
        defense_boost=boosts.get("def", 0),
        special_attack_boost=boosts.get("spa", 0),
        special_defense_boost=boosts.get("spd", 0),
        speed_boost=boosts.get("spe", 0),
        accuracy_boost=boosts.get("accuracy", 0),
        evasion_boost=boosts.get("evasion", 0),
    )

def battle_to_state(battle):
    # TODO: weather, terrain, trick room, hazards / side conditions
    return State(
        side_one=to_engine_side(battle.team, battle.active_pokemon, True),
        side_two=to_engine_side(battle.opponent_team, battle.opponent_active_pokemon, False),
    )

# Evaluation function for the game state (minimax) PROBABLY GONNA MOVE THIS TO A DIFFERENT FILE LATER

def evaluate(state):
    """Score from side one's point of view: my total HP fraction minus theirs.
    Higher is better for me. Both algorithms will share this function."""

    mine = sum(p.hp / p.maxhp for p in state.side_one.pokemon if p.maxhp)
    theirs = sum(p.hp / p.maxhp for p in state.side_two.pokemon if p.maxhp)
    unseen = 6 - len(state.side_two.pokemon)
    theirs += unseen

    return (mine - theirs) / 6


# Legal options lists

def my_options(battle):
    """Engine move strings for my legal actions, mapped to poke-env orders."""
    options = {}
    for move in battle.available_moves:
        options[move.id] = Player.create_order(move)
        if battle.can_tera:
            options[f"{move.id}-tera"] = Player.create_order(move, terastallize=True)

    for mon in battle.available_switches:
        options[mon.species] = Player.create_order(mon)

    return options


def their_options(state):
    # TODO: add opponent switches to their revealed bench
    return [m.id for m in state.side_two.pokemon[0].moves]


# Search (depth 1)

def expected_value(state, mine, theirs):
    outcomes = generate_instructions(state, mine, theirs)

    return sum(o.percentage / 100 * evaluate(state.apply_instructions(o))
               for o in outcomes)

# Minimax player (depth 1)

class OneTurnPlayer(Player): 
    def choose_move(self, battle):
        if battle.active_pokemon is None or battle.opponent_active_pokemon is None:
            return self.choose_random_move(battle)
        
        try:
            state = battle_to_state(battle)
            options = my_options(battle)
            best_option, best_score = None, float("-inf")

            for mine in options:
                # Assume the opponent picks the reply that's worst for me
                score = min(expected_value(state, mine, theirs)
                            for theirs in their_options(state))
                if score > best_score:
                    best_option, best_score = mine, score
            return options[best_option]
        
        except Exception as error:  
            print(f"[{battle.battle_tag} turn {battle.turn}] fallback to random: {error!r}")
            return self.choose_random_move(battle)


async def main():
    bot = OneTurnPlayer(battle_format="gen9randombattle", save_replays=True)
    opponent = RandomPlayer(battle_format="gen9randombattle")
    await bot.battle_against(opponent, n_battles=20)
    print(f"OneTurnPlayer won {bot.n_won_battles} of {bot.n_finished_battles}")


if __name__ == "__main__":
    asyncio.run(main())