# Chess Tournament Manager

This application helps you run a chess tournament from start to finish:
- create tournaments
- create and add players
- run rounds and matches
- track points and podium
- export reports in HTML

## Start the application

From the project folder, run:

```powershell
python main.py
```

## How to navigate the app

At the top of the window, use these menus:
- `Tournaments`
- `Round`
- `Match`
- `Settings`

Main areas in the window:
- Left panel: tournament details, dates, status, players, points, description.
- Top-right panel: list of rounds.
- Bottom-right panel: matches in the selected round.
- Right side cards: details for the selected match players.

## Typical workflow (recommended)

1. Create a tournament  
Go to `Tournaments > Create tournament`, fill in the form, then click `Save`.

2. Create players  
Go to `Tournaments > Create player` and save each player.

3. Add players to the tournament  
Go to `Tournaments > Add player to tournament` and select one or more player `.json` files.

4. Start the tournament  
Go to `Tournaments > Start tournament`.

5. Run each round  
Select a round in the rounds list, then use:
- `Round > Start round`
- `Round > Stop round` (only after all matches are finished)

6. Run each match  
Select a match, then use `Match > Start match`.  
When the match is ongoing, the same menu lets you finish it and choose:
- player 1 wins
- tie
- player 2 wins

7. Finish the tournament  
When all rounds are finished, stop the tournament from `Tournaments > Stop tournament`.

8. Save / load later  
- Save current tournament: `Tournaments > Save tournament`
- Open an existing tournament: `Tournaments > Load tournament`

9. Export reports  
Use `Tournaments > Export`, choose a report type, and save the HTML file.

## Pairings mode

When creating a tournament, choose:
- `Automatic`: rounds/pairings are generated automatically as you progress.
- `Manual`: after finishing a round, you create the next round pairings yourself.

## Important rules to know

- You cannot add or remove players while a tournament is ongoing.
- A round can start only if previous rounds are finished.
- A round can stop only when all its matches are finished.
- To start a tournament, number of players must be exactly `2^(number of rounds)`.
  - Example: 4 rounds => 16 players.
- Player NCID format must be `2 letters + 5 digits` (example: `AA12345`).

## Where your files are saved

- Players: `data/players`
- Tournaments: `data/tournaments`
- Exported reports: `exports`
