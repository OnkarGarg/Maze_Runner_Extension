import csv
import gc
from math import sqrt

from alive_progress import alive_bar

from runner import create_runner, get_x, get_y, get_orientation, turn, forward, orientation_options
import matplotlib.pyplot as plt
from matplotlib import patches
import os
import random


class Maze:
    def __init__(self, width: int = 5, height: int = 5):
        """ Constructs the initial maze with outer walls with given dimensions """
        self._width = width
        self._height = height
        self._h_walls = set()
        self._v_walls = set()
        self._flood_array = {}
        self._mind_maze = None
        self._visited_cells = set()
        self._path = []
        self.prev_runner = ()
        self.exploration_data = []
        self.final_path = []
        self.all_walls = {}
        self._render_settings = (False, False, 1, False, False, False, 0.998, 0.1, False)
        # Save images, display images, display time, floodfill data display, euclidian_only, Hope_mode, decay rate,
        # exploration factor, heatmap
        self.heuristic = {}
        self.run_id = ""

        for i in range(height):
            self._v_walls.add((0, i))
            self._v_walls.add((width, i))

        for i in range(width):
            self._h_walls.add((i, 0))
            self._h_walls.add((i, height))

        rows = range(self.width)
        columns = range(self.height)
        coordinates = [(r, c) for r in rows for c in columns]
        for i, (x, y) in enumerate(coordinates):
            self.all_walls[(x, y)] = [False, False, False, False]
            if x == 0:
                self.all_walls[(x, y)][3] = True
            if x == self.width - 1:
                self.all_walls[(x, y)][1] = True
            if y == 0:
                self.all_walls[(x, y)][2] = True
            if y == self.height - 1:
                self.all_walls[(x, y)][0] = True
            if i % 70000 == 0:
                print(i/(width*height))
                gc.collect()
        gc.collect()

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path: list):
        self._path = path

    @property
    def flood_array(self):
        return self._flood_array

    @flood_array.setter
    def flood_array(self, flood_array):
        self._flood_array = flood_array

    @property
    def render_settings(self):
        return self._render_settings

    @render_settings.setter
    def render_settings(self, settings: tuple[bool, bool, int, bool]):
        self._render_settings = settings

    def set_all_walls(self, coord, index):
        self.all_walls[coord][index] = True

    def add_horizontal_wall(self, x_coordinate: int, horizontal_line: int):
        if 0 <= x_coordinate < self._width and 1 <= horizontal_line < self._height:
            self._h_walls.add((x_coordinate, horizontal_line))

    def add_vertical_wall(self, y_coordinate: int, vertical_line: int):
        if 0 <= y_coordinate < self._height and 1 <= vertical_line < self._width:
            self._v_walls.add((vertical_line, y_coordinate))

    def get_walls(self, x_coordinate: int, y_coordinate: int) -> tuple[bool, bool, bool, bool]:
        h_walls = self._h_walls
        v_walls = self._v_walls
        north = (x_coordinate, y_coordinate + 1) in h_walls
        east = (x_coordinate + 1, y_coordinate) in v_walls
        south = (x_coordinate, y_coordinate) in h_walls
        west = (x_coordinate, y_coordinate) in v_walls

        return north, east, south, west

    def sense_walls(self, runner: dict[str, any]) -> tuple[bool, bool, bool]:
        walls = self.get_walls(get_x(runner), get_y(runner))
        sensed_walls = []
        wall_num = 0
        orientations = orientation_options(runner)
        for orientation in orientations:
            if orientation == "N":
                wall_num = 0
            elif orientation == "S":
                wall_num = 2
            elif orientation == "E":
                wall_num = 1
            elif orientation == "W":
                wall_num = 3
            sensed_walls.append(walls[wall_num])
        sensed_walls = tuple(sensed_walls)
        return sensed_walls

    def go_straight(self, runner):
        if not self.sense_walls(runner)[1]:
            runner = forward(runner)
        else:
            raise ValueError()
        return runner

    def get_open_neighbors(self, runner, goal, num):
        x = get_x(runner)
        y = get_y(runner)
        neighbors = [(x, y + 1), (x + 1, y), (x, y - 1), (x - 1, y)]
        neighbors_orientations = ["N", "E", "S", "W"]
        walls = self.sense_walls(runner)  # direction to the left, current direction, direction to the right
        self._mind_maze, self._flood_array = update_maze(runner, walls, goal, num, self.render_settings, self.run_id, maze=self._mind_maze,
                                                         width=self._width, height=self._height)
        walls_orientations = orientation_options(runner)
        indices = [neighbors_orientations.index(orientation) for orientation in walls_orientations if not walls[walls_orientations.index(orientation)]]
        return_list = [neighbors[i] for i in indices]

        return return_list

    def flood_fill(self, goal):
        queue = [goal]
        flood_array = {goal: 0}
        fill_value = 1
        heuristic = self.heuristic
        all_walls = self.all_walls

        while queue:
            next_queue = []
            for x, y in queue:
                walls = tuple(all_walls[(x, y)])
                for i, n_coord in enumerate([(x, y + 1), (x + 1, y), (x, y - 1), (x - 1, y)]):
                    if not walls[i] and n_coord not in flood_array:
                        if self.render_settings[4] or self.render_settings[5]:
                            flood_array[n_coord] = fill_value + heuristic[n_coord]
                        else:
                            flood_array[n_coord] = fill_value
                        next_queue.append(n_coord)

            queue = next_queue
            fill_value += 1
        return flood_array

    def move(self, runner, goal, num):
        x = get_x(runner)
        y = get_y(runner)
        self.prev_runner = (x, y)
        self._visited_cells.add((x, y))

        neighbors = self.get_open_neighbors(runner, goal, num)
        flood_array = self._flood_array

        tmp_dict = {cell: flood_array[cell] for cell in flood_array if cell in neighbors}

        neighbors_with_cost = [(cell, tmp_dict[cell]) for cell in neighbors if cell in tmp_dict]


        action = ""

        try:
            cheapest_node_data = min(neighbors_with_cost, key=lambda x: x[1])

            orientations_dict = {(0, 1): "N", (1, 0): "E", (0, -1): "S", (-1, 0): "W"}
            orientations = ["N", "E", "S", "W"]
            current_orientation = get_orientation(runner)
            coord_diff = (cheapest_node_data[0][0] - x, cheapest_node_data[0][1] - y)
            target_orientation = orientations_dict[coord_diff]
            diff = orientations.index(target_orientation) - orientations.index(current_orientation)
            while diff != 0:
                turn(runner, "Left")
                action += "L"
                current_orientation = get_orientation(runner)
                diff = orientations.index(target_orientation) - orientations.index(current_orientation)

        except ValueError:
            turn(runner, "Left")
            turn(runner, "Left")
            action = "LL"
        if "LLL" in action:
            action = action.replace("LLL", "R")
        action += "F"
        self.go_straight(runner)

        nx = get_x(runner)
        ny = get_y(runner)
        self._visited_cells.add((nx, ny))

        return runner, action

    def dijkstra(self, starting: tuple[int, int], goal: tuple[int, int]):
        queue = []
        dist = {}
        prev = {}

        coordinates = [(r, c) for r in range(self._width) for c in range(self._height)]

        for coord in coordinates:
            dist[coord] = float("inf")
            prev[coord] = None
            queue.append(coord)
        dist[starting] = 0

        temp_run_num = 0

        with alive_bar(None, title="Dijkstra's", calibrate=100000) as bar:
            while queue:
                u = min(queue, key=lambda node: dist[node])
                queue.remove(u)

                temp_runner = create_runner(u[0], u[1])
                temp_run_num += 1
                neighbors = self.free_nodes(temp_runner)
                turn(temp_runner, "Left")
                free_nodes = self.free_nodes(temp_runner)
                neighbors.extend([node for node in free_nodes if node not in neighbors])
                for v in neighbors:
                    alt = dist[u] + 1
                    if alt < dist[v]:  # Only update if the new path is shorter
                        dist[v] = alt
                        prev[v] = u
                bar()

        path = []
        goal_prev_pair = []
        if prev[goal] is not None or goal == starting:
            u = goal
            while prev[u] is not None:
                path.append(u)
                if [u, prev[u]] in goal_prev_pair:
                    break
                else:
                    goal_prev_pair.append([u, prev[u]])
                u = prev[u]

        path = path[::-1]
        self._path = path

    def euclidian_calc(self, goal):
        for x in range(self.width):
            for y in range(self.height):
                self.heuristic[(x, y)] = sqrt((goal[0] - x)**2 + (goal[1] - y)**2)

    def hope_mode(self, goal):
        print("modified_heuristic_with_decay running")
        decay = self.render_settings[6]
        factor = self.render_settings[7]

        for x in range(self.width):
            for y in range(self.height):
                h = sqrt((goal[0] - x)**2 + (goal[1] - y)**2)
                exploration_term = 2 * random.uniform(-factor, factor)
                self.heuristic[(x, y)] = h + exploration_term
                factor *= decay

    def explore(self, starting: tuple[int, int] = (0, 0), goal: tuple[int, int] = (0, 0)):
        print("Exploration running")
        runner = create_runner(starting[0], starting[1])
        num = 0
        data = [["Step", "x-coordinate", "y-coordinate", "Actions"]]
        rate = []
        with alive_bar(None, title="Exploration", calibrate=100000) as bar:
            while (get_x(runner), get_y(runner)) != goal:
                runner, action = self.move(runner, goal, num)
                num += 1
                data.append([num, self.prev_runner[0], self.prev_runner[1], action])
                bar()
                if self.height*self.width >= 250000:
                    gc.collect()
                rate.append(float(bar.rate.replace("?", "0").replace("/s", "")))
        # print("RATE", rate)
        # print("DATA", data)

        self.exploration_data = data

        return num

    def shortest_path(self, starting: list[int, int] = [0, 0], goal: list[int, int] = [0, 0]):
        goal = (goal[0], goal[1])
        starting = (starting[0], starting[1])
        num = self.explore(starting, goal)

        maze = self._mind_maze
        maze.render_settings = self.render_settings
        width = maze.width
        height = maze.height
        rows = range(width)
        columns = range(height)
        all_cells = [(r, c) for r in rows for c in columns]
        unvisited_cells = set()
        for cell in all_cells:
            if cell not in self._visited_cells:
                unvisited_cells.add(cell)
                maze.add_vertical_wall(cell[1], cell[0])
                maze.add_horizontal_wall(cell[0], cell[1])
                maze.add_vertical_wall(cell[1], cell[0] + 1)
                maze.add_horizontal_wall(cell[0], cell[1] + 1)
        if self.render_settings[0] or self.render_settings[1]:
            maze.render(create_runner(starting[0], starting[1]), goal, 100000, list(self._visited_cells))
        maze.dijkstra(starting, goal)
        if self.render_settings[0] or self.render_settings[1]:
            maze.render(create_runner(starting[0], starting[1]), goal, 100001, list(maze.path))
            self.render(create_runner(starting[0], starting[1]), goal, 100002, list(maze.path))
        print("Exploration steps:", num, "    Final path length:", len(maze.path) + 1,
              "    score:", num / 4 + (len(maze.path) + 1),
              "    Final data file path:", self.run_id)
        self.final_path = [starting] + maze.path
        return self.exploration_data, self.final_path, num, len(maze.path) + 1, num / 4 + (len(maze.path) + 1)

    def build_files(self, file_name):
        exploration_data = self.exploration_data
        final_path = self.final_path

        try:
            os.mkdir(self.run_id)
        except FileExistsError:
            pass

        with open(f"{self.run_id}\exploration.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(exploration_data)

        with open(f"{self.run_id}\statistics.txt", "w") as file:
            file.write(file_name + "\n")
            file.write(str((len(exploration_data) - 1) / 4 + (len(final_path))) + "\n")
            file.write(str(len(exploration_data) - 1) + "\n")
            file.write(str(final_path).replace("[", "").replace("]", "") + "\n")
            file.write(str(len(final_path)))


    def render(self, runner: dict[str, any], goal: tuple[int, int], num: int, final_path: list = []):
        """ Renders the maze using matplotlib """
        plt.figure(figsize=(10, 10))
        ax = plt.gca()
        colored_boxes = []

        for step in final_path:
            colored_boxes.append([step[0], step[1], "pink"])

        # Draw horizontal walls
        for x, y in self._h_walls:
            plt.plot([x, x + 1], [y, y], color="red", linewidth=2)

        # Draw vertical walls
        for x, y in self._v_walls:
            plt.plot([x, x], [y, y + 1], color="green", linewidth=2)

        colored_boxes.append([goal[0], goal[1], "yellow"])
        colored_boxes.append([get_x(runner), get_y(runner), "blue"])

        for x, y, color in colored_boxes:
            rect = patches.Rectangle((x, y), 1, 1, linewidth=0, facecolor=color)
            ax.add_patch(rect)

        if self.render_settings[3]:
            cell_values = self._flood_array
            if cell_values:
                for (x, y), value in cell_values.items():
                    # Center the text in the cell
                    plt.text(x + 0.5, y + 0.5, "{:.1f}".format(value), ha='center', va='center', fontsize=10, color='black')
                if self.render_settings[8]:
                        heatmap = [[cell_values.get((x, y), float('inf')) for x in range(self._width)] for y in
                                   range(self._height)]
                        plt.imshow(heatmap, cmap='coolwarm', interpolation='nearest', origin='lower',
                                   extent=[0, self._width, 0, self._height])

        direction = get_orientation(runner)
        dx, dy = 0, 0
        if direction == "N":
            dy = 0.3
        elif direction == "S":
            dy = -0.3
        elif direction == "E":
            dx = 0.3
        elif direction == "W":
            dx = -0.3
        ax.arrow(get_x(runner) + 0.5, get_y(runner) + 0.5, dx, dy, head_width=0.2, head_length=0.2, fc='yellow',
                 ec='blue')

        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

        # Add custom axes showing x and y values
        for x in range(self._width):
            plt.text(x + 0.5, -0.5, str(x), ha='center', va='center', fontsize=10, color='black')  # x-axis values
        for y in range(self._height):
            plt.text(-0.5, y + 0.5, str(y), ha='center', va='center', fontsize=10, color='black')  # y-axis values

        # Set grid and labels
        plt.xlim(0, self._width)
        plt.ylim(0, self._height)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.grid(visible=True, which='both', color='lightgray', linestyle='--', linewidth=0.5)#
        if self.render_settings[0]:
            try:
                os.mkdir(self.run_id)
            except FileExistsError:
                pass
            plt.savefig(f'./{self.run_id}/{num}.png')

        if self.render_settings[1]:
            plt.show(block=False)
            plt.pause(self.render_settings[2])
        plt.close()

    def free_nodes(self, runner: dict[str, any]) -> list[tuple[int, int]]:
        walls = [not value for value in self.sense_walls(runner)]
        free_nodes = []
        if walls[0]:
            new_runner = runner.copy()
            turn(new_runner, "Left")
            forward(new_runner)
            free_nodes.append((get_x(new_runner), get_y(new_runner)))
        if walls[1]:
            new_runner = runner.copy()
            forward(new_runner)
            free_nodes.append((get_x(new_runner), get_y(new_runner)))
        if walls[2]:
            new_runner = runner.copy()
            turn(new_runner, "Right")
            forward(new_runner)
            free_nodes.append((get_x(new_runner), get_y(new_runner)))
        return free_nodes


def update_maze(runner, walls, goal, num, render_settings, run_id, maze: Maze = None, width=None, height=None):
    if maze is None and width is None and height is None:
        maze = Maze()
    elif maze is None and height is None:
        maze = Maze(width)
    elif maze is None:
        maze = Maze(width, height)

    if maze.heuristic == {}:
        if maze.render_settings[4]:
            maze.euclidian_calc(goal)
        elif maze.render_settings[5]:
            maze.hope_mode(goal)

    x = get_x(runner)
    y = get_y(runner)
    orientation = get_orientation(runner)

    if orientation == "N":
        if walls[0]:
            maze.add_vertical_wall(y, x)
            maze.all_walls[(x, y)][3] = True
            try:
                maze.all_walls[(x - 1, y)][1] = True
            except KeyError:
                pass
        if walls[1]:
            maze.add_horizontal_wall(x, y + 1)
            maze.all_walls[(x, y)][0] = True
            try:
                maze.all_walls[(x, y + 1)][2] = True
            except KeyError:
                pass
        if walls[2]:
            maze.add_vertical_wall(y, x + 1)
            maze.all_walls[(x, y)][1] = True
            try:
                maze.all_walls[(x + 1, y)][3] = True
            except KeyError:
                pass
    if orientation == "S":
        if walls[0]:
            maze.add_vertical_wall(y, x + 1)
            maze.all_walls[(x, y)][1] = True
            try:
                maze.all_walls[(x + 1, y)][3] = True
            except KeyError:
                pass
        if walls[1]:
            maze.add_horizontal_wall(x, y)
            maze.all_walls[(x, y)][2] = True
            try:
                maze.all_walls[(x, y - 1)][0] = True
            except KeyError:
                pass
        if walls[2]:
            maze.add_vertical_wall(y, x)
            maze.all_walls[(x, y)][3] = True
            try:
                maze.all_walls[(x - 1, y)][1] = True
            except KeyError:
                pass

    if orientation == "E":
        if walls[0]:
            maze.add_horizontal_wall(x, y + 1)
            maze.all_walls[(x, y)][0] = True
            try:
                maze.all_walls[(x, y + 1)][2] = True
            except KeyError:
                pass
        if walls[1]:
            maze.add_vertical_wall(y, x + 1)
            maze.all_walls[(x, y)][1] = True
            try:
                maze.all_walls[(x + 1, y)][3] = True
            except KeyError:
                pass
        if walls[2]:
            maze.add_horizontal_wall(x, y)
            maze.all_walls[(x, y)][2] = True
            try:
                maze.all_walls[(x, y - 1)][0] = True
            except KeyError:
                pass

    if orientation == "W":
        if walls[0]:
            maze.add_horizontal_wall(x, y)
            maze.all_walls[(x, y)][2] = True
            try:
                maze.all_walls[(x, y - 1)][0] = True
            except KeyError:
                pass
        if walls[1]:
            maze.add_vertical_wall(y, x)
            maze.all_walls[(x, y)][3] = True
            try:
                maze.all_walls[(x - 1, y)][1] = True
            except KeyError:
                pass
        if walls[2]:
            maze.add_horizontal_wall(x, y + 1)
            maze.all_walls[(x, y)][0] = True
            try:
                maze.all_walls[(x, y + 1)][2] = True
            except KeyError:
                pass

    flood_array = maze.flood_fill(goal)
    maze.flood_array = flood_array
    maze.render_settings = render_settings
    maze.run_id = run_id
    if render_settings[0] or render_settings[1]:
        maze.render(runner, goal, num)

    return maze, flood_array