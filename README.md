# Inteligência Artificial: Snake Agent

### Grades
- **1st Delivery:** 17.9/20  
- **2nd Delivery:** 17.7/20  

## Project Abstract
This project was developed as part of the "Inteligência Artificial" (Artificial Intelligence) course. It involved creating an autonomous agent capable of playing the game Snake effectively in both single-player and multiplayer modes. The agent leverages AI concepts such as search techniques and agent architectures to navigate and strategize within the constraints of the game environment. The primary objective was to maximize the score under varying gameplay conditions.

Key game modifications included limited snake vision, various food effects (e.g., superfoods and poisons), and dynamic map configurations (e.g., spherical and flat worlds). These additions introduced complexity and required strategic adaptability in the agent's behavior.

## Results
The agent's performance was evaluated based on its relative results in 10 games per delivery. The max score corresponded to a grade of 20 and the mean score to ~15. The game sets consisted of different proportions of single-player and multiplayer modes:

- **1st Delivery:** 70% single-player, 30% multiplayer  
  - **Score:** 109 (Min: 0, Max: 162.5)
- **2nd Delivery:** 30% single-player, 70% multiplayer  
  - **Score:** 113.3 (Min: 0, Mean: 72, Max: 172)  

## How to Run

### Installation
Ensure you are using Python 3.11.

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Tip: Use a virtual environment for better dependency management.*

### Running the Game
Start the game using three terminals:
1. Server:
   ```bash
   python3 server.py
   ```
2. Viewer:
   ```bash
   python3 viewer.py
   ```
3. Client:
   ```bash
   python3 client.py
   ```

To use the sample client, ensure the Pygame window has focus during play.

### Controls
- **Movement:** Arrow keys

### Debugging
Verify that Pygame is installed correctly:
```bash
python -m pygame.examples.aliens
```

## Bookmarks
- [Private Repository of the Project (Source Code)](https://github.com/detiuaveiro/ia2024-tpg-112981_113384_114514)

## Our Team
| <div align="center"><a href="https://github.com/tomasf18"><img src="https://avatars.githubusercontent.com/u/122024767?v=4" width="150px;" alt="Tomás Santos"/></a><br/><strong>Tomás Santos</strong></div> | <div align="center"><a href="https://github.com/DaniloMicael"><img src="https://avatars.githubusercontent.com/u/115811245?v=4" width="150px;" alt="Danilo Silva"/></a><br/><strong>Danilo Silva</strong></div> | <div align="center"><a href="https://github.com/Affapple"><img src="https://avatars.githubusercontent.com/u/65315165?v=4" width="150px;" alt="João Gaspar"/></a><br/><strong>João Gaspar</strong></div> |
| --- | --- | --- |
