import asyncio

from poke_env.player import RandomPlayer
from minimax import Minimax
from mc import MCTS


async def main():
    player_1 = Minimax(max_concurrent_battles=1)
    player_2 = MCTS(max_concurrent_battles=1)

    await player_1.battle_against(player_2, n_battles=20)

    print(f"Finished battles: {player_1.n_finished_battles}")
    print(f"Minimax wins: {player_1.n_won_battles} battles")
    print(f"MCTS wins: {player_2.n_won_battles} battles")


if __name__ == "__main__":
    asyncio.run(main())