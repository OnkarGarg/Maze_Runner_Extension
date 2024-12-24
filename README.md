# Maze Runner (Extension)

This project is a maze runner and solver that reads a maze from a file, processes it, and finds a valid path from a starting point to a goal. It utilizes a modified Floodfill algorithm for the exploration and Dijkstra's algorithm for the shortest_path finding from the exploration data along with the optional Euclidian heuristic for the Floodfill algorithm. It also generates exploration data and statistics about the maze run.

## Design choices
I have opted to use the Floodfill algorithm for the exploration of the maze. This is because it seemed like a better choice over other algorithms like BFS and DFS for this task. I have also opted to use Dijkstra's algorithm for the shortest path finding as it is a very efficient algorithm for this task. I have also added the Euclidian heuristic to the Floodfill algorithm to make it more efficient as it further forces the runner to move towards the goal. I have also added a hope mode to the Floodfill algorithm to experiment with how random values can influence the algorithm.
To properly use the Floodfill algorithm without allowing the maze runner from seeing the whole maze, a secondary `Maze` object is created that only contains the information the runner has seen. The Floodfill algorithm is then run on **this** maze, hence essentially trying to do "optimistic path-finding". There are some situations where there are multiple open neighboring cells that have the same value. In such, cases, the runner opts to go to the cell that requires the least amount of turning. The reason behind this is to stay true to the physical micro mouse counterpart. Once, the runner reaches the goal, the `shortest_path` method is called in which it blocks off all the cells that were never explored by the runner as the dijkstra's is being run on the secondary "memory" maze. By doing this, it makes sure that the dijkstra's doesn't find an illegal path simply because some walls weren't explored.

## Requirements

- Python 3.x
- `matplotlib`
- `alive-progress`
- `opencv-python` (optional, for video generation)

## Usage

To run the maze runner from the terminal, use the command format:

```
python maze_runner.py [options] <maze_file>
```
Here is a list of available options:

- `-h, --help`: Show the help message and exit.
- `--starting`: The starting point of the maze. Default is (0, 0).
- `--goal`: The goal point of the maze. Default is the top right corner.
- `--save_images`: Save the maze images to the working directory. Default is False.
- `--display_images`: Display the maze images. Default is False.
- `--display_time`: The amount of time each step is displayed for. Default is 1 second.
- `--floodfill_data_display`: Display the floodfill data. Default is False.
- `--euclidian_only`: Activates the Euclidian heuristic to use for flood-filling.
- `--hope_mode`: Activates the hope mode for the maze runner. This is even it there is nothing more the euclidian version can do, run this. This mode runs the euclidian heuristic with a small random value added to it. This random value is decreased the closer the coordinates are to the goal. This mode then runs multiple iterations of maze runner with the pre-computed variable heuristics. Hence, there is no point in saving the images as only the ones from the last run will be saved. Displaying is a valid function. If the ``--euclidian_only`` function is on, then that takes priority over this. There will be no data files built in this mode but the same data will be outputted in terminal.
- `--hope_runs`: The numbers of runs the user wants in ``hope_mode``. If ``hope_mode`` is on and there is no value in ``hope_runs``, an error will be thrown.
- `--heat_map`: Activates the heat map mode for the image generation. it's an alternative for the `--floodfill_data_display` when working with bigger mazes where having text might overcrowd the render.

Here is a sample command to run the maze runner from terminal:

```sh
python maze_runner.py --starting "0, 0" --goal "9, 9" --save_images --display_images --display_time 2 --floodfill_data_display --euclidian_only --heat_map large_maze2.mz
```
The above command will run the maze runner on the `medium_maze2.mz` file with the starting point at (0, 0) and the goal at (9, 4). It will save the maze images (as a .svg file for better readability) to the working directory, display the maze images, and display each step for 1 second. The exploration data about the maze run will be saved in a CSV file named `exploration.csv` while the final path and the score are stored in a Text fle called `statstics.txt`.

### Information about the generated data
On each run, a unique folder is created in the working directory. The folder is named `<maze_file_name>_<unique_id>`. You can then run `video_maker.py` to generate a video from the saved images.