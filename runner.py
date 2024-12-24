
def create_runner(x: int = 0, y: int = 0, orientation: str = "N") -> dict[str, any]:
    return {"x": x, "y": y, "orientation": orientation}


def get_x(runner: dict[str, any]) -> int:
    return runner["x"]


def get_y(runner: dict[str, any]) -> int:
    return runner["y"]


def get_orientation(runner: dict[str, any]) -> str:
    return runner["orientation"]


def turn(runner: dict[str, any], direction: str) -> dict[str, any]:
    new_orientations = orientation_options(runner)
    if direction == "Left":
        runner["orientation"] = new_orientations[0]
    if direction == "Right":
        runner["orientation"] = new_orientations[2]
    return runner


def orientation_options(runner):
    orientations = ["N", "E", "S", "W"]
    current_orientation = get_orientation(runner)
    current_orientation_index = orientations.index(current_orientation)
    new_orientations = [orientations[current_orientation_index - 1], current_orientation,
                        orientations[(current_orientation_index + 1) % len(orientations)]]
    return new_orientations


def forward(runner):
    orientation = get_orientation(runner)
    if orientation == "N":
        runner["y"] += 1
    elif orientation == "S":
        runner["y"] -= 1
    elif orientation == "E":
        runner["x"] += 1
    elif orientation == "W":
        runner["x"] -= 1
    return runner
