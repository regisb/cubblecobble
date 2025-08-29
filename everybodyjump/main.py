#! /usr/bin/env python
# /// script
# dependencies = [
#   "pyxel",
# ]
# ///
# title: Everybody Loves To Jump
# author: Régis Behmo
# desc: My Briançon Game Jam 2025 "multiplayer" entry
# site: https://github.com/regisb/everybodylovestojump
# license: AGPL v3.0
# version: 1.0
import sys

import game
import server


def main() -> None:
    if len(sys.argv) == 1 or sys.argv[1] == "play":
        game.run()
    elif sys.argv[1] == "serve":
        server.run()


if __name__ == "__main__":
    main()
