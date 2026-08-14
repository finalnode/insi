import sys

import pykim
import pytest
from pykim import (
    animate,
    get_color,
    paint,
    play_tone,
    right,
    run,
    set_color,
    set_x,
    set_y,
)
from pykim.testing import set_pixel_for_test


class FakeSound:
    def __init__(self):
        self._notes, self._tones, self._volumes, self._effects = [], [], [], []
        self.speed = 0

    notes = property(lambda self: self._notes)
    tones = property(lambda self: self._tones)
    volumes = property(lambda self: self._volumes)
    effects = property(lambda self: self._effects)


class FakePyxel:
    KEY_LEFT = 1
    KEY_RIGHT = 2
    KEY_UP = 3
    KEY_DOWN = 4
    KEY_SPACE = 5
    KEY_RETURN = 6
    KEY_ESCAPE = 7

    def __init__(self):
        self.sounds = [FakeSound()]
        self.calls = []
        self.frame_count = 0

    def init(self, width, height, *, title, display_scale=None):
        self.calls.append(("init", width, height, title, display_scale))

    def run(self, update, draw):
        for _ in range(47):
            update()
        draw()

    def btn(self, key):
        self.calls.append(("btn", key))
        return key == self.KEY_RIGHT

    def btnp(self, key):
        self.calls.append(("btnp", key))
        return key == self.KEY_SPACE

    def btnr(self, key):
        self.calls.append(("btnr", key))
        return False

    def play_pos(self, channel):
        return None

    def play(self, channel, sound):
        self.calls.append(("play", channel, sound))

    def cls(self, color):
        self.calls.append(("cls", color))

    def pset(self, x, y, color):
        self.calls.append(("pset", x, y, color))

    def circ(self, *args):
        self.calls.append(("circ", *args))

    def line(self, *args):
        self.calls.append(("line", *args))

    def rect(self, *args):
        self.calls.append(("rect", *args))

    def text(self, *args):
        self.calls.append(("text", *args))


def test_interactive_run_uses_update_draw_and_world_api(monkeypatch):
    fake = FakePyxel()
    monkeypatch.setitem(sys.modules, "pyxel", fake)
    frames = []

    def update():
        frames.append(pykim.world.frame_count)
        if pykim.world.btn("right"):
            pykim.kim.right()

    def draw():
        pykim.world.cls("navy")
        pykim.world.rect(1, 2, 3, 4, "purple")
        pykim.world.text(5, 6, "Punkte", "white")
        pykim.kim.draw()

    pykim.world.run(update, draw)

    assert len(frames) == 47
    assert pykim.kim.get_x() == 47
    assert ("btn", fake.KEY_RIGHT) in fake.calls
    assert ("cls", 1) in fake.calls
    assert ("rect", 1, 2, 3, 4, 2) in fake.calls
    assert ("text", 5, 6, "Punkte", 7) in fake.calls


def test_interactive_run_automatically_updates_pixel_subclasses(monkeypatch):
    fake = FakePyxel()
    monkeypatch.setitem(sys.modules, "pyxel", fake)

    class Walker(pykim.Pixel):
        def update(self):
            self.right()

    mia = pykim.world.spawn(Walker, "MIA", 10, 10)
    pykim.world.run(lambda: None)

    assert mia.get_x() == 57


def test_world_btn_is_false_before_run_and_validates_runtime_keys():
    assert not pykim.world.btn("right")
    with pytest.raises(TypeError, match="Tastenname"):
        pykim.world.btn(1)

def test_run_connects_world_and_audio_to_pyxel(monkeypatch):
    fake = FakePyxel()
    monkeypatch.setitem(sys.modules, "pyxel", fake)
    set_x(10)
    set_y(20)
    set_color("purple")
    paint()
    play_tone("C4", beats=2)

    run()

    assert ("init", 160, 120, "PyKIM", None) in fake.calls
    assert ("pset", 10, 20, 2) in fake.calls
    assert ("pset", 10, 20, 1) in fake.calls
    assert not any(call[0] in ("circ", "line") for call in fake.calls)
    assert ("play", 0, 0) in fake.calls
    assert fake.sounds[0].notes == [24]
    assert fake.sounds[0].speed == 60


def test_world_zoom_magnifies_pixels_without_resizing_window(monkeypatch):
    fake = FakePyxel()
    monkeypatch.setitem(sys.modules, "pyxel", fake)

    pykim.world.zoom(7)
    set_x(80)
    set_y(60)
    run()

    assert ("init", 160, 120, "PyKIM", None) in fake.calls
    assert any(call[0] == "rect" and call[3:5] == (7, 7) for call in fake.calls)


def test_world_zoom_camera_centers_on_kim_and_clamps_at_edges():
    pykim.world.zoom(4)

    set_x(80)
    set_y(60)
    assert pykim._screen_position(80, 60) == (80, 60)

    set_x(0)
    set_y(0)
    assert pykim._screen_position(0, 0) == (0, 0)

    set_x(159)
    set_y(119)
    assert pykim._screen_position(159, 119) == (156, 116)


def test_kim_rotates_through_all_visible_colors():
    fake = FakePyxel()
    set_x(10)
    set_y(20)

    pykim._draw_kim(fake)
    assert fake.calls == [("pset", 10, 20, 1)]


def test_kim_skips_the_background_color():
    fake = FakePyxel()
    set_x(10)
    set_y(20)
    set_pixel_for_test(10, 20, "navy")

    pykim._draw_kim(fake)

    assert fake.calls == [("pset", 10, 20, 2)]


def test_draw_world_uses_configured_background_and_keeps_other_colors():
    fake = FakePyxel()
    pykim.world.set_background("light_blue")
    pykim.world.pset(2, 3, "black")

    pykim._draw_world(fake)

    assert fake.calls[0] == ("cls", 6)
    assert ("pset", 2, 3, 0) in fake.calls
    assert not any(call == ("pset", 0, 0, 6) for call in fake.calls)


def test_draws_multiple_pixels_in_the_same_world():
    fake = FakePyxel()
    set_x(10)
    set_y(20)
    mia = pykim.world.new_pixel("MIA", 30, 40)

    pykim._draw_pixels(fake)

    assert ("pset", 10, 20, 1) in fake.calls
    assert ("pset", 30, 40, 4) in fake.calls
    assert pykim.world.pixels == (pykim.kim, mia)


def test_animates_an_additional_pixel_step_by_step():
    fake = FakePyxel()
    pykim.speed(99)
    mia = pykim.world.new_pixel("MIA", 30, 40)
    mia.paint_path("orange")
    mia.right(2)

    pykim._draw_pixels(fake)
    assert ("pset", 30, 40, 4) in fake.calls
    assert ("pset", 32, 40, 4) not in fake.calls

    for _ in range(3):
        pykim._advance_animation()
    fake.calls.clear()
    pykim._draw_world(fake)
    pykim._draw_pixels(fake)

    assert ("pset", 32, 40, 9) in fake.calls
    assert ("pset", 32, 40, 4) in fake.calls


def test_hidden_pixels_are_not_drawn_and_can_be_shown_again():
    fake = FakePyxel()
    mia = pykim.world.new_pixel("MIA", 30, 40)
    mia.hide()
    pykim.hide()

    pykim._draw_pixels(fake)
    assert fake.calls == []

    mia.show()
    pykim.show()
    pykim._draw_pixels(fake)
    assert ("pset", 0, 0, 1) in fake.calls
    assert ("pset", 30, 40, 4) in fake.calls


def test_hide_takes_effect_at_its_place_in_the_animation():
    fake = FakePyxel()
    pykim.speed(99)
    leo = pykim.world.new_pixel("LEO", 30, 40)
    leo.paint_path("cyan")
    leo.up(2)
    leo.hide()

    for _ in range(3):
        pykim._advance_animation()
    pykim._draw_pixels(fake)
    assert ("pset", 30, 38, 4) in fake.calls

    pykim._advance_animation()
    fake.calls.clear()
    pykim._draw_pixels(fake)
    assert not any(call[1:3] == (30, 38) for call in fake.calls)


def test_parallel_moves_two_pixels_in_the_same_animation_frames():
    fake = FakePyxel()
    set_x(10)
    set_y(10)
    mia = pykim.world.new_pixel("MIA", 20, 20)
    pykim.speed(99)
    pykim.kim.paint_path("purple")
    mia.paint_path("orange")

    with pykim.world.parallel():
        pykim.kim.right(2)
        mia.down(2)

    # Zwei paint_start-Ereignisse liegen vor dem Parallelblock. Nach einem
    # weiteren Frame haben sich beide Figuren genau einen Schritt bewegt.
    for _ in range(3):
        pykim._advance_animation()
    pykim._draw_pixels(fake)

    assert ("pset", 11, 10, 1) in fake.calls
    assert ("pset", 20, 21, 4) in fake.calls


def test_parallel_keeps_shorter_pixel_at_its_destination():
    set_x(10)
    set_y(10)
    mia = pykim.world.new_pixel("MIA", 20, 20)
    pykim.speed(99)

    with pykim.world.parallel():
        pykim.kim.right(3)
        mia.down(1)

    for _ in range(3):
        pykim._advance_animation()

    assert pykim._animation_position(pykim.kim) == (13, 10)
    assert pykim._animation_position(mia) == (20, 21)


def test_parallel_blocks_cannot_be_nested():
    with pytest.raises(RuntimeError, match="nicht verschachtelt"):
        with pykim.world.parallel():
            with pykim.world.parallel():
                pass


def test_color_sensor_lights_up_during_animation():
    fake = FakePyxel()
    set_x(10)
    set_y(20)
    set_pixel_for_test(11, 20, "green")
    animate(0.01)

    assert get_color("right") == "green"
    pykim._advance_animation()
    pykim._draw_sensor(fake)

    assert fake.calls == [("pset", 11, 20, 12)]
    assert get_color(11, 20) == "green"

    fake.calls.clear()
    fake.frame_count = 5
    pykim._draw_kim(fake)
    assert fake.calls == [("pset", 10, 20, 2)]

    fake.calls.clear()
    fake.frame_count = 70
    pykim._draw_kim(fake)
    assert fake.calls == [("pset", 10, 20, 15)]

    fake.calls.clear()
    fake.frame_count = 75
    pykim._draw_kim(fake)
    assert fake.calls == [("pset", 10, 20, 1)]


def test_animation_draws_the_path_step_by_step():
    fake = FakePyxel()
    set_x(10)
    set_y(20)
    animate(0.01)
    set_color("purple")
    pykim.paint_start()
    right(2)

    pykim._draw_world(fake)
    assert ("pset", 10, 20, 2) not in fake.calls
    assert ("pset", 11, 20, 2) not in fake.calls

    pykim._advance_animation()
    fake.calls.clear()
    pykim._draw_world(fake)
    assert ("pset", 10, 20, 2) in fake.calls
    assert ("pset", 11, 20, 2) not in fake.calls

    pykim._advance_animation()
    fake.calls.clear()
    pykim._draw_world(fake)
    assert ("pset", 11, 20, 2) in fake.calls
    assert ("pset", 12, 20, 2) not in fake.calls


def test_maximum_axes_shrink_to_a_pixel():
    fake = FakePyxel()

    pykim._draw_axes(fake, 20, 30, 1, 10)
    assert fake.calls == [
        ("line", 0, 30, 159, 30, 10),
        ("line", 20, 0, 20, 119, 10),
    ]

    fake.calls.clear()
    pykim._draw_axes(fake, 20, 30, 0, 10)
    assert fake.calls == [("pset", 20, 30, 10)]


def test_start_sequence_draws_axes_for_every_visible_pixel():
    fake = FakePyxel()
    set_x(10)
    set_y(20)
    pykim.world.new_pixel("MIA", 30, 40)

    pykim._draw_start_sequences(fake, frame=0)

    assert fake.calls == [
        ("cls", 0),
        ("line", 0, 20, 159, 20, 1),
        ("line", 10, 0, 10, 119, 1),
        ("line", 0, 40, 159, 40, 4),
        ("line", 30, 0, 30, 119, 4),
    ]


def test_start_sequence_omits_a_pixel_hidden_before_animation():
    fake = FakePyxel()
    mia = pykim.world.new_pixel("MIA", 30, 40)
    mia.hide()

    pykim._draw_start_sequences(fake, frame=0)

    assert not any(call[0] == "line" and 40 in call for call in fake.calls)


def test_pause_finishes_without_using_a_pyxel_rest():
    fake = FakePyxel()
    pykim.play_pause()
    play_tone("C4")

    for _ in range(10):
        pykim._play_next_note(fake)

    assert ("play", 0, 0) in fake.calls
    assert fake.sounds[0].notes == [24]
