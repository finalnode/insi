import pytest
import pykim

from pykim import (
    animate,
    collect,
    count_color,
    down,
    get_color,
    get_obstacles,
    get_position,
    get_x,
    get_y,
    items_left,
    left,
    paint,
    paint_path,
    paint_start,
    paint_stop,
    play_pause,
    play_tone,
    right,
    set_color,
    set_position,
    set_x,
    set_y,
    speed,
    up,
)
from pykim.testing import (
    get_pending_audio_events,
    get_pending_tones,
    get_world_state,
    set_pixel_for_test,
)


def test_position_and_movement():
    set_x(10)
    set_y(20)
    right()
    down(3)
    left(2)
    up()
    assert (get_x(), get_y()) == (9, 22)
    assert get_position() == (9, 22)


def test_default_runtime_owns_mutable_imperative_state():
    set_position(12, 34)
    set_color("orange")
    paint()
    play_tone("C4")

    assert (pykim.runtime.x, pykim.runtime.y) == (12, 34)
    assert pykim.runtime.selected_color == 9
    assert pykim.runtime.cells[34][12] == 9
    assert list(pykim.runtime.notes) == [(60, 1)]
    assert pykim.runtime.world is pykim.world
    assert pykim.runtime.kim is pykim.kim


def test_world_cells_can_belong_to_an_independent_runtime():
    other_runtime = pykim.Runtime(pykim.WIDTH, pykim.HEIGHT, pykim.DEFAULT_COLOR)
    other_world = pykim.World(other_runtime)

    other_world.pset(12, 34, "orange")

    assert other_runtime.cells[34][12] == 9
    assert pykim.runtime.cells[34][12] == 0


def test_pixel_position_properties_replace_getters_in_oop_code():
    mia = pykim.world.new_pixel("MIA", 10, 20)
    assert mia.get_position() == (10, 20)

    assert mia.x == 10
    assert mia.y == 20
    assert mia.position == (10, 20)
    mia.x = 30
    mia.y = 40
    assert mia.position == (30, 40)
    mia.position = (50, 60)
    assert (mia.x, mia.y) == (50, 60)


def test_pixel_position_property_rejects_invalid_shape():
    mia = pykim.world.new_pixel("MIA")

    with pytest.raises(TypeError, match="Tupel"):
        mia.position = [10, 20]


def test_set_position_changes_both_coordinates():
    set_position(12, 34)
    assert (get_x(), get_y()) == (12, 34)


def test_kim_object_and_procedural_api_share_the_same_state():
    pykim.kim.set_position(10, 20)
    right(3)
    pykim.kim.down(2)

    assert (get_x(), get_y()) == (13, 22)
    assert (pykim.kim.get_x(), pykim.kim.get_y()) == (13, 22)


def test_two_pixels_move_and_paint_independently():
    pykim.kim.set_position(10, 10)
    pykim.kim.paint_path("purple")
    pykim.kim.right(2)
    mia = pykim.world.new_pixel("MIA", 10, 20)
    mia.paint_path("orange")
    mia.down(2)

    state = get_world_state()
    assert state[10][10:13] == (2, 2, 2)
    assert [state[y][10] for y in range(20, 23)] == [9, 9, 9]
    assert (pykim.kim.get_x(), pykim.kim.get_y()) == (12, 10)
    assert (mia.get_x(), mia.get_y()) == (10, 22)
    assert pykim.world.pixels == (pykim.kim, mia)


def test_pixel_names_are_unique():
    pykim.world.new_pixel("MIA")
    with pytest.raises(ValueError, match="bereits verwendet"):
        pykim.world.new_pixel("MIA")


def test_spawn_creates_a_custom_pixel_subclass_with_attributes():
    class MusikPixel(pykim.Pixel):
        def __init__(self, pixel_world, name, x=0, y=0, *, note="C4"):
            super().__init__(pixel_world, name, x, y)
            self.note = note

        def finish(self):
            self.play_tone(self.note)

    mia = pykim.world.spawn(MusikPixel, "MIA", 10, 20, note="E4")
    mia.finish()

    assert isinstance(mia, MusikPixel)
    assert mia.note == "E4"
    assert get_pending_tones() == (64,)


def test_spawn_rejects_a_class_that_is_not_a_pixel():
    with pytest.raises(TypeError, match="Unterklasse von Pixel"):
        pykim.world.spawn(object, "DING")


def test_world_drawing_helpers_work_without_a_running_window():
    pykim.world.pset(2, 3, "purple")
    pykim.world.rect(4, 5, 2, 3, "orange")

    state = get_world_state()
    assert state[3][2] == 2
    assert [state[y][4:6] for y in range(5, 8)] == [(9, 9)] * 3

    pykim.world.cls("black")
    assert not any(any(row) for row in get_world_state())


def test_world_background_color_fills_the_world_and_is_readable():
    pykim.world.pset(2, 3, "red")

    pykim.world.set_background("light_blue")

    assert pykim.world.background_color == "light_blue"
    assert get_color(2, 3) == "light_blue"
    assert all(
        color == 6 for row in get_world_state() for color in row
    )


def test_obstacle_color_stops_kim_before_the_first_matching_pixel():
    set_position(10, 20)
    pykim.world.pset(13, 20, "red")
    pykim.world.set_obstacle("red")

    right(8)

    assert get_position() == (12, 20)
    assert pykim.world.is_obstacle(13, 20)
    assert pykim.world.obstacle_colors == ("red",)


def test_get_obstacles_names_all_adjacent_obstacle_directions():
    set_position(10, 20)
    pykim.world.pset(10, 19, "red")
    pykim.world.pset(11, 20, "brown")
    pykim.world.set_obstacle("red", "brown")

    assert get_obstacles() == ("up", "right")
    assert pykim.kim.get_obstacles() == ("up", "right")


def test_get_obstacles_returns_empty_tuple_when_all_neighbors_are_free():
    set_position(10, 20)

    assert get_obstacles() == ()


@pytest.mark.parametrize(
    ("position", "direction"),
    [((10, 0), "up"), ((10, 119), "down"), ((0, 10), "left"), ((159, 10), "right")],
)
def test_get_obstacles_treats_world_edges_as_obstacles(position, direction):
    set_position(*position)

    assert direction in get_obstacles()


def test_additional_pixel_reports_obstacles_relative_to_its_own_position():
    set_position(10, 20)
    mia = pykim.world.new_pixel("MIA", 30, 40)
    pykim.world.pset(29, 40, "red")
    pykim.world.set_obstacle("red")

    assert get_obstacles() == ()
    assert mia.get_obstacles() == ("left",)


def test_collect_returns_current_color_and_restores_background():
    pykim.world.set_background("light_blue")
    pykim.world.pset(10, 20, "red")
    set_position(10, 20)

    assert count_color("red") == 1
    assert items_left("red")
    assert collect() == "red"
    assert get_color() == "light_blue"
    assert count_color("red") == 0
    assert not items_left("red")


def test_additional_pixel_can_collect_from_its_own_position():
    pykim.world.set_background("navy")
    pykim.world.pset(30, 40, "yellow")
    mia = pykim.world.new_pixel("MIA", 30, 40)

    assert mia.collect() == "yellow"
    assert mia.get_color() == "navy"


def test_obstacle_stops_painting_before_it_is_overwritten():
    set_position(10, 20)
    pykim.world.pset(13, 20, "red")
    pykim.world.set_obstacle("red")
    paint("purple")

    right(8)

    assert get_position() == (12, 20)
    assert get_world_state()[20][10:14] == (2, 2, 2, 8)


def test_obstacles_apply_to_additional_pixels():
    mia = pykim.world.new_pixel("MIA", 10, 20)
    pykim.world.pset(10, 23, "brown")
    pykim.world.set_obstacle("brown")

    mia.down(10)

    assert mia.get_position() == (10, 22)


def test_multiple_obstacle_colors_can_be_removed_or_cleared():
    pykim.world.set_obstacle("red", "brown")
    assert pykim.world.obstacle_colors == ("brown", "red")

    pykim.world.remove_obstacle("red")
    assert pykim.world.obstacle_colors == ("brown",)

    pykim.world.clear_obstacles()
    assert pykim.world.obstacle_colors == ()


def test_obstacle_configuration_requires_at_least_one_color():
    with pytest.raises(TypeError, match="mindestens eine Farbe"):
        pykim.world.set_obstacle()
    with pytest.raises(TypeError, match="mindestens eine Farbe"):
        pykim.world.remove_obstacle()


def test_set_position_can_place_kim_on_an_obstacle_as_a_start_tool():
    pykim.world.pset(10, 20, "red")
    pykim.world.set_obstacle("red")

    set_position(10, 20)
    right()

    assert get_position() == (11, 20)


def test_animation_records_only_steps_before_an_obstacle():
    set_position(10, 20)
    pykim.world.pset(13, 20, "red")
    pykim.world.set_obstacle("red")
    animate(0.1)

    right(8)

    assert pykim.runtime.animation_positions == [(10, 20), (11, 20), (12, 20)]


def test_animate_records_every_movement_step():
    set_x(10)
    set_y(20)
    animate(0.1)
    right(3)

    assert pykim.runtime.animation_delay_frames == 3
    assert pykim.runtime.animation_positions == [
        (10, 20),
        (11, 20),
        (12, 20),
        (13, 20),
    ]


@pytest.mark.parametrize("bad", [0, -1, "slow", True])
def test_invalid_animation_delay(bad):
    with pytest.raises((TypeError, ValueError), match="delay"):
        animate(bad)


@pytest.mark.parametrize(
    ("value", "frames"), [(1, 100), (10, 10), (50, 2), (99, 1)]
)
def test_speed_sets_animation_delay(value, frames):
    speed(value)
    assert pykim.runtime.animation_delay_frames == frames
    assert pykim.runtime.animation_positions == [(0, 0)]


def test_speed_100_disables_animation():
    animate()
    right(2)

    speed(100)

    assert pykim.runtime.animation_delay_frames is None
    assert pykim.runtime.animation_positions == []


@pytest.mark.parametrize("bad", [0, 101, -1, 1.5, "50", True])
def test_invalid_speed(bad):
    with pytest.raises((TypeError, ValueError), match="speed"):
        speed(bad)


def test_world_zoom_sets_display_scale():
    pykim.world.zoom(6)

    assert pykim.world._zoom == 6


@pytest.mark.parametrize("bad", [0, 11, -1, 1.5, "4", True])
def test_invalid_world_zoom(bad):
    with pytest.raises((TypeError, ValueError), match="zoom"):
        pykim.world.zoom(bad)


@pytest.mark.parametrize("bad", [-1, 160, 1.5, "1", True])
def test_invalid_x(bad):
    with pytest.raises((TypeError, ValueError), match="x|Position"):
        set_x(bad)


def test_movement_cannot_leave_world():
    with pytest.raises(ValueError, match="außerhalb der PyKIM-Welt"):
        left()


def test_paint_path_uses_default_color_and_paints_every_step():
    set_x(10)
    set_y(20)
    paint_path()
    right(3)
    assert get_world_state()[20][10:14] == (7, 7, 7, 7)


def test_paint_path_accepts_a_color():
    set_x(10)
    set_y(20)
    paint_path("orange")
    down(2)
    state = get_world_state()
    assert [state[y][10] for y in range(20, 23)] == [9, 9, 9]


def test_paint_start_and_stop():
    set_x(10)
    set_y(20)
    set_color("orange")
    paint_start()
    right(2)
    paint_stop()
    right(2)

    assert get_world_state()[20][10:15] == (9, 9, 9, 0, 0)


def test_paint_colors_current_pixel_and_following_path():
    set_x(10)
    set_y(20)
    paint()
    down(2)

    state = get_world_state()
    assert [state[y][10] for y in range(20, 23)] == [7, 7, 7]


def test_paint_accepts_a_color_and_starts_a_path():
    set_x(10)
    set_y(20)
    paint("orange")
    right()

    state = get_world_state()
    assert state[20][10] == 9
    assert state[20][11] == 9


def test_paint_followed_by_stop_colors_only_current_pixel():
    set_position(10, 20)
    paint("orange")
    paint_stop()
    right()

    state = get_world_state()
    assert state[20][10] == 9
    assert state[20][11] == 0


def test_world_and_pixels_can_both_trigger_shared_audio():
    mia = pykim.world.new_pixel("MIA")

    pykim.world.play_tone("C4")
    mia.play_tone("E4", beats=2)
    pykim.world.play_pause()

    assert get_pending_audio_events() == ((60, 1), (64, 2), (-1, 1))


@pytest.mark.parametrize("bad", [-1, 1.5, True])
def test_invalid_steps(bad):
    with pytest.raises((TypeError, ValueError), match="steps"):
        right(bad)


@pytest.mark.parametrize("color", ["purple", 2])
def test_paint_and_read_canonical_color(color):
    set_x(10)
    set_y(20)
    set_color(color)
    paint()
    assert get_color() == "purple"
    assert get_world_state()[20][10] == 2


def test_read_neighbor_and_arbitrary_pixel():
    set_x(10)
    set_y(10)
    set_pixel_for_test(11, 10, "green")
    set_pixel_for_test(2, 3, "red")
    assert get_color("right") == "green"
    assert get_color(2, 3) == "red"


@pytest.mark.parametrize("color", ["violet", -1, 16, 2.5, True])
def test_invalid_color(color):
    with pytest.raises((TypeError, ValueError), match="Farbe|Farbwert"):
        set_color(color)


def test_invalid_direction_and_signature():
    with pytest.raises(ValueError, match="Richtung.*unbekannt"):
        get_color("ahead")
    with pytest.raises(TypeError, match="erlaubt"):
        get_color(1, 2, 3)


@pytest.mark.parametrize(
    ("note", "number"), [(60, 60), ("C4", 60), ("F#4", 66), ("Db4", 61)]
)
def test_tones(note, number):
    play_tone(note)
    assert get_pending_tones() == (number,)
    assert list(pykim.runtime.notes) == [(number, 1)]


def test_tone_length_and_pause():
    play_tone("C4", beats=2)
    play_pause(beats=3)
    assert get_pending_tones() == (60, -1)


@pytest.mark.parametrize("beats", [0, -1, 1.5, True])
def test_invalid_beats(beats):
    with pytest.raises((TypeError, ValueError), match="beats"):
        play_tone("C4", beats=beats)
    with pytest.raises((TypeError, ValueError), match="beats"):
        play_pause(beats)


@pytest.mark.parametrize("note", ["H4", "C#", 35, 96, 3.5, True])
def test_invalid_tones(note):
    with pytest.raises((TypeError, ValueError), match="Note"):
        play_tone(note)
