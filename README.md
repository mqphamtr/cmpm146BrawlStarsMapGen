# cmpm146BrawlStarsMapGen

Authors: Kianna Penner, Matthew Peters, Michael Pham-Tran, Ann Sasi

For this project, our team is building a Brawl Stars map generator using parallel genetic algorithms. As of August 11, 2025, Brawl Stars does not use procedural content generation for their arenas. This means they cycle through hand-crafted and player-created maps for variety. The goal of our project is to automatically generate playable, diverse, and balanced Brawl Stars maps quickly and efficiently. To do so, we are implementing an island model genetic algorithm proposed by a research paper and aim to show that the algorithm would work for automatically generating Brawl Stars map. For this prototype, the generated maps would be generated offline, meaning maps would be fully evolved and evaluated and then uploaded to the map pool. Also, each map would be independent from one another, meaning previous gameplay would not influence future maps. The islands interact only through migration of top-performing individuals, sharing beneficial traits while maintaining diversity. The proposed algorithm would be faster and better compared to the single-population genetic algorithm used in project 5 Mario level generation. 

Brawl Stars does not currently use a procedural content generation tool to build their labels, so our novelty will be in using an island model genetic algorithm to build Brawl Stars maps, a fitness function tailored to building quality maps, and the generation of different islands to build different map variants and styles.

The value of this project is that it could help assist the Brawl Stars developer in drafting a new map quickly while maintaining the quality. It could also help bring more variety to the map pool for the playerbase, encouraging more engageability. Even though this project is designed with Brawl Stars specifically in mind, the approach could be used in other multiplayer games to automate map generation.

