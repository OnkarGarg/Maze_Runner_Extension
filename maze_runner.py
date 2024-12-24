import uuid
from pstats import Stats

from maze import Maze
import argparse
import cProfile as cp


def maze_reader(maze_file: str):
    input_lines = list()
    try:
        with open(maze_file, 'r') as file:
            for line in file:
                line = line.strip()
                input_lines.append(line)
    except FileNotFoundError:  # add any other relevant errors that need to be handled
        raise IOError

    line_lengths = {len(line) for line in input_lines}
    if len(line_lengths) != 1:
        raise ValueError("The maze file may be missing a line.")

    if not all(c == "#" for c in input_lines[0]) or not all(c == "#" for c in input_lines[-1]):
        raise ValueError

    height = len(input_lines) // 2
    width = len(input_lines[0]) // 2

    for i, line in enumerate(input_lines):
        if i % 2 == 0:  # Horizontal wall line
            if len(line) != 2 * width + 1 or not line.startswith('#') or not line.endswith('#'):
                raise ValueError(f"Line {i+1} is not a valid horizontal wall line as it's missing the outer wall.")
        else:  # Vertical wall line
            if len(line) != 2 * width + 1 or line[0] != '#' or line[-1] != '#':
                raise ValueError(f"Line {i+1} is not a valid vertical wall line as it's missing the outer wall.")
        for j, c in enumerate(line):
            if c not in "#.":
                raise ValueError(f"Invalid character at position {j + 1} in line {i + 1}.")

    maze = Maze(width=width, height=height)

    try:
        for y in range(height + 1):  # Horizontal wall lines are at even indices
            horizontal_line = input_lines[2 * y]
            for x in range(width):
                if horizontal_line[2 * x] != '#':
                    raise ValueError(f"The wall intersections in the file are incorrect. "
                                     f"The character at {y * 2 + 1}:{x * 2 + 1} seems wrong. It should be a '#'.")
                if horizontal_line[2 * x + 1] == '#':
                    maze.add_horizontal_wall(x, height - y)

        # Process vertical walls
        for y in range(height):  # Vertical wall lines are at odd indices
            vertical_line = input_lines[2 * y + 1]
            for x in range(width + 1):
                if vertical_line[2 * x] == '#':
                    maze.add_vertical_wall(height - y - 1, x)
    except IndexError:
        raise ValueError("There is something wrong with the maze file.")

    return maze


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="ECS Maze Runner")

    parser.add_argument("--starting", help='The starting position, e.g., "2, 1"', default=None)
    parser.add_argument("--goal", help='The goal position, e.g., "4, 5"', default=None)
    parser.add_argument("--save_images", help='Saves an image of the mind maze at each step'
                                              ' (negatively influences speed).', action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--display_images", help='Displays an image of the mind maze at each step'
                                                 ' (negatively influences speed).', action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--display_time", help='The amount of time the image is displayed.', default=1.)
    parser.add_argument("--floodfill_data_display", help='Whether the floodfill data will be added during'
                                                         ' rendering (negatively influences speed).', action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--euclidian_only", help="Instead of using the basic fill values in flooddill, the euclidian "
                                                 "distances are added onto the fill values. (Does not influence "
                                                 "speed)", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--hope_mode", help="When all hope is lost and the scores are bad for loopy mazes, try me...", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--hope_runs", help='The amount of hope you have. (Negatively impacts speed)', default=1)
    parser.add_argument("--decay", help='The amount of decay for each floodfill layer,', default=0.998)
    parser.add_argument("--factor", help='The amount of (positive and negative) randomness in the heuristics', default=0.1)
    parser.add_argument("--heat_map", help="If '--floodfill_data_display' is being used, this accompanies the data with a heatmap. (negatively influences speed)", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("maze", help='The name of the maze file, e.g., maze1.mz')

    args = parser.parse_args()

    run_id = (args.maze + "_" + str(uuid.uuid4())).replace(".mz", "_")

    if args.hope_mode and not args.euclidian_only:

        maze = maze_reader(args.maze)

        try:
            if args.starting is not None:
                starting = [int(x) for x in args.starting.split(", ")]
            else:
                starting = [0, 0]
        except ValueError as ve:
            print(
                "One or more of the elements provided in the starting coordinates can not be converted into integers. "
                "Using default starting coordinates of '0, 0'.")
            starting = [0, 0]
        except TypeError as te:
            print(
                "The starting coordinates provided are not in the correct format, i.e., '2, 1'. Using default starting "
                "coordinates of '0, 0'.")
            starting = [0, 0]

        try:
            if args.goal is not None:
                goal = [int(x) for x in args.goal.split(", ")]
            else:
                goal = [maze.width - 1, maze.height - 1]
        except ValueError as ve:
            print(
                "One or more of the elements provided in the goal coordinates can not be converted into integers. Using "
                "default goal coordinates of 'width - 1, height - 1'.")
            goal = [maze.width - 1, maze.height - 1]
        except TypeError as te:
            print("The goal coordinates provided are not in the correct format, i.e., '2, 1'. Using default goal "
                  "coordinates of 'width - 1, height - 1'.")
            goal = [maze.width - 1, maze.height - 1]

        print(args.save_images)

        maze.render_settings = (args.save_images, args.display_images, float(
            args.display_time), args.floodfill_data_display, args.euclidian_only,
                                args.hope_mode, float(args.decay), float(args.factor), args.heat_map)

        maze.run_id = run_id

        scores = [maze.shortest_path(starting=starting, goal=goal)]

        for i in range(int(args.hope_runs) - 1):
            maze = maze_reader(args.maze)
            maze.render_settings = (args.save_images, args.display_images, float(
                args.display_time), args.floodfill_data_display, args.euclidian_only,
                                    args.hope_mode, float(args.decay), float(args.factor), args.heat_map)
            maze.run_id = run_id
            scores.append(maze.shortest_path(starting=starting, goal=goal))
        print(min(scores, key=lambda x: x[-1]))

    else:

        maze = maze_reader(args.maze)
        maze.run_id = run_id

        try:
            if args.starting is not None:
                starting = [int(x) for x in args.starting.split(", ")]
            else:
                starting = [0, 0]
        except ValueError as ve:
            print(
                "One or more of the elements provided in the starting coordinates can not be converted into integers. "
                "Using default starting coordinates of '0, 0'.")
            starting = [0, 0]
        except TypeError as te:
            print(
                "The starting coordinates provided are not in the correct format, i.e., '2, 1'. Using default starting "
                "coordinates of '0, 0'.")
            starting = [0, 0]

        try:
            if args.goal is not None:
                goal = [int(x) for x in args.goal.split(", ")]
            else:
                goal = [maze.width - 1, maze.height - 1]
        except ValueError as ve:
            print(
                "One or more of the elements provided in the goal coordinates can not be converted into integers. Using "
                "default goal coordinates of 'width - 1, height - 1'.")
            goal = [maze.width - 1, maze.height - 1]
        except TypeError as te:
            print("The goal coordinates provided are not in the correct format, i.e., '2, 1'. Using default goal "
                  "coordinates of 'width - 1, height - 1'.")
            goal = [maze.width - 1, maze.height - 1]

        print(args.save_images)

        maze.render_settings = (args.save_images, args.display_images, float(
            args.display_time), args.floodfill_data_display, args.euclidian_only,
                                args.hope_mode, float(args.decay), float(args.factor), args.heat_map)

        print(maze.render_settings)

        pr = cp.Profile()
        pr.enable()

        maze.shortest_path(starting=starting, goal=goal)
        maze.build_files(args.maze)

        pr.disable()
        stats = Stats(pr)
        stats.sort_stats('tottime').print_stats(10)

    print("DONE RUNNING", "starting", starting, "goal", goal)