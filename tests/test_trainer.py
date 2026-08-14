import pytest
import pykim
import pykim.trainer.exercises as exercise_registry

from pykim import down, left, paint, paint_path, right, set_x, set_y, up
from pykim.trainer.runner import check_exercise
from pykim.trainer.optimization import evaluate_stairs
from pykim.trainer import ExerciseBuilder
from pykim.trainer.authoring import audit_exercise, generate_exercise_source
from pykim.trainer.exercises import exercise_names, get_exercise


def test_builtin_exercises_work_without_searchable_package_directory(monkeypatch):
    """Die Registry benötigt keine dynamisch importierten Python-Trainer."""

    exercises = exercise_registry._discover_exercises()

    assert "farben-melodie" in exercises
    assert set(exercises) == set(exercise_names())


def efficient_stairs():
    paint_path("purple")
    for _ in range(5):
        right(5)
        down(5)


def repeated_stairs():
    paint_path("purple")
    right(5)
    down(5)
    right(5)
    down(5)
    right(5)
    down(5)
    right(5)
    down(5)
    right(5)
    down(5)


def draw_multiple_pixels_example():
    pykim.kim.set_position(20, 20)
    pykim.kim.paint_path("purple")
    mia = pykim.world.new_pixel("MIA", x=60, y=20)
    mia.paint_path("orange")
    leo = pykim.world.new_pixel("LEO", x=40, y=60)
    leo.paint_path("cyan")

    with pykim.world.parallel():
        pykim.kim.right(15)
        mia.left(15)
        leo.up(20)

    pykim.kim.down(10)
    mia.down(20)
    leo.right(10)

    with pykim.world.parallel():
        pykim.kim.right(15)
        mia.left(15)
        leo.up(15)
    leo.hide()


def test_square_exercise_accepts_a_complete_square(capsys):
    set_x(50)
    set_y(50)
    paint_path("purple")
    right(5)
    down(5)
    left(5)
    up(5)

    report = check_exercise("quadrat-5", "")

    assert report.successful
    assert report.passed == 5
    output = capsys.readouterr().out
    assert "5 Pixel breit" in output
    assert "vollständig gelöst" in output


def test_square_exercise_accepts_another_direction(capsys):
    set_x(50)
    set_y(50)
    paint_path()
    down(5)
    right(5)
    up(5)
    left(5)

    assert check_exercise("quadrat-5", "").successful
    capsys.readouterr()


def test_square_exercise_gives_several_hints_for_an_incomplete_solution(capsys):
    set_x(50)
    set_y(50)
    paint_path()
    right(5)
    down(4)

    report = check_exercise("quadrat-5", "")

    assert not report.successful
    assert report.passed < 5
    output = capsys.readouterr().out
    assert "✗ Start oder Ende des Quadrats liegt nicht bei (50, 50)" in output
    assert "Hinweis:" in output
    assert "Prüfungen bestanden" in output


def test_square_exercise_rejects_an_extra_pixel(capsys):
    set_x(50)
    set_y(50)
    paint_path()
    right(5)
    down(5)
    left(5)
    up(5)
    right(1)
    down(1)
    paint()

    report = check_exercise("quadrat-5", "")

    assert not report.successful
    assert not report.results[-1].passed
    capsys.readouterr()


def test_stairs_accept_complete_drawing_with_a_loop(capsys):
    set_x(50)
    set_y(50)
    efficient_stairs()

    report = check_exercise("treppe-5", "for _ in range(5): pass")

    assert report.successful
    assert report.passed == 5
    output = capsys.readouterr().out
    assert "5 Stufen" in output
    assert "vermeidest Wiederholungen" in output


def test_stairs_reports_optimal_code_score(capsys):
    set_x(50)
    set_y(50)
    efficient_stairs()
    source = """
for _ in range(5):
    right(5)
    down(5)
"""

    report = check_exercise("treppe-5", source)

    assert report.optimization is not None
    assert report.optimization.score == 100
    output = capsys.readouterr().out
    assert "Optimierung: 100 %" in output
    assert "optimal aufgebaut" in output


def test_stairs_gives_optimization_tips_for_repeated_code(capsys):
    source = "\n".join(["right(5)", "down(5)"] * 5)

    optimization = evaluate_stairs(source)

    assert optimization.score == 1
    assert any("Schleife" in tip for tip in optimization.tips)
    assert any("jeweils nur einmal" in tip for tip in optimization.tips)


def test_stairs_encourage_shorter_code(capsys):
    set_x(50)
    set_y(50)
    repeated_stairs()

    report = check_exercise("treppe-5", "right(5)\ndown(5)")

    assert not report.successful
    assert all(result.passed for result in report.results[:-1])
    assert not report.results[-1].passed
    assert "Code lässt sich noch kürzen" in capsys.readouterr().out


def test_stairs_reject_a_missing_step(capsys):
    set_x(50)
    set_y(50)
    paint_path()
    for _ in range(4):
        right(5)
        down(5)

    report = check_exercise("treppe-5", "for _ in range(4): pass")

    assert not report.successful
    assert not report.results[0].passed
    assert not report.results[1].passed
    assert "unvollständig" in capsys.readouterr().out


def test_run_style_check_detects_a_loop_without_a_function(capsys):
    set_x(50)
    set_y(50)
    efficient_stairs()
    source = """
paint_path()
for _ in range(5):
    right(5)
    down(5)
"""

    report = check_exercise("treppe-5", source)

    assert report.successful
    assert "vermeidest Wiederholungen" in capsys.readouterr().out


def test_run_style_check_rejects_an_unknown_exercise():
    with pytest.raises(ValueError, match="gibt es nicht"):
        check_exercise("unbekannt", "for _ in range(5): pass")


def test_multiple_pixels_exercise_checks_world_drawing_and_parallel(capsys):
    draw_multiple_pixels_example()

    report = check_exercise(
        "mehrere-pixel", "with world.parallel():\n    kim.right(15)"
    )

    assert report.successful
    assert report.passed == 5
    output = capsys.readouterr().out
    assert "farbigen Linien stimmen exakt" in output
    assert "world.parallel()-Block" in output


def test_multiple_pixels_exercise_detects_a_wrong_world_pixel(capsys):
    draw_multiple_pixels_example()
    pykim.world.cells[20][20] = 9

    report = check_exercise(
        "mehrere-pixel", "with world.parallel():\n    kim.right(15)"
    )

    assert not report.results[2].passed
    assert "Farben weichen" in capsys.readouterr().out


def test_multiple_pixels_exercise_requires_parallel_source(capsys):
    draw_multiple_pixels_example()

    report = check_exercise("mehrere-pixel", "kim.right(15)")

    assert all(result.passed for result in report.results[:-1])
    assert not report.results[-1].passed
    assert "noch nicht parallel" in capsys.readouterr().out


def test_dotted_line_exercise_accepts_compact_loop_solution(capsys):
    pykim.set_position(20, 20)
    pykim.set_color("purple")
    for _ in range(8):
        pykim.paint()
        pykim.paint_stop()
        pykim.right(2)
    source = """
for _ in range(8):
    paint()
    paint_stop()
    right(2)
"""

    report = check_exercise("punktlinie-8", source)

    assert report.successful
    assert report.optimization is not None
    assert report.optimization.score == 100
    assert "Optimierung: 100 %" in capsys.readouterr().out


def test_four_squares_exercise_checks_function_loop_and_world(capsys):
    pykim.set_position(20, 20)
    pykim.paint_path("purple")
    for _ in range(4):
        pykim.right(5)
        pykim.down(5)
        pykim.left(5)
        pykim.up(5)
        pykim.right(5)
    source = """
def zeichne_quadrat():
    right(5)
    down(5)
    left(5)
    up(5)
    right(5)

for _ in range(4):
    zeichne_quadrat()
"""

    report = check_exercise("vier-quadrate", source)

    assert report.successful
    assert report.optimization is not None
    assert report.optimization.score == 100
    assert "vollständig und korrekt verbunden" in capsys.readouterr().out


def test_checkerboard_exercise_checks_nested_loops_condition_and_function(capsys):
    def zeichne_feld(x, y, color):
        pykim.set_position(x, y)
        pykim.set_color(color)
        pykim.paint()

    for y in range(8):
        for x in range(8):
            if (x + y) % 2 == 0:
                color = "purple"
            else:
                color = "orange"
            zeichne_feld(20 + x, 20 + y, color)

    source = """
def zeichne_feld(x, y, color):
    set_position(x, y)
    set_color(color)
    paint()
for y in range(8):
    for x in range(8):
        if (x + y) % 2 == 0:
            color = "purple"
        else:
            color = "orange"
        zeichne_feld(20 + x, 20 + y, color)
"""

    report = check_exercise("schachbrett-8", source)

    assert report.successful
    assert report.optimization is not None
    assert report.optimization.score == 100
    assert "Alle 64 Schachbrettfelder" in capsys.readouterr().out


def test_scale_exercise_checks_notes_and_loop(capsys):
    for note in ("C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"):
        pykim.play_tone(note)

    report = check_exercise(
        "tonleiter-c-dur", "for note in noten:\n    play_tone(note)"
    )

    assert report.successful
    assert report.passed == 2
    assert "alle acht Töne" in capsys.readouterr().out


def test_rhythm_exercise_checks_beats_pause_function_and_loop(capsys):
    for _ in range(2):
        pykim.play_tone("C4")
        pykim.play_tone("E4")
        pykim.play_tone("G4", beats=2)
        pykim.play_pause()
    source = """
def spiele_motiv():
    play_tone('C4')
for _ in range(2):
    spiele_motiv()
"""

    report = check_exercise("rhythmus-motiv", source)

    assert report.successful
    assert report.passed == 3
    assert "richtigen Ton- und Pausenlängen" in capsys.readouterr().out


def test_color_melody_checks_world_audio_loop_and_condition(capsys):
    colors = ("red", "green", "cyan", "yellow")
    notes = (("C4", 1), ("E4", 1), ("G4", 1), ("C5", 2))
    for offset, (color, (note, beats)) in enumerate(zip(colors, notes)):
        pykim.set_position(20 + offset, 20)
        pykim.set_color(color)
        pykim.paint()
        pykim.play_tone(note, beats)
    source = """
for _ in range(4):
    color = get_color()
    if color == 'red':
        play_tone('C4')
"""

    report = check_exercise("farben-melodie", source)

    assert report.successful
    assert report.passed == 4
    assert "vorgesehenen Ton" in capsys.readouterr().out


def test_audio_exercise_rejects_wrong_note_length(capsys):
    for note in ("C4", "D4", "E4", "F4", "G4", "A4", "B4"):
        pykim.play_tone(note)
    pykim.play_tone("C5", beats=2)

    report = check_exercise("tonleiter-c-dur", "for note in noten: play_tone(note)")

    assert not report.results[0].passed
    assert "Tonlängen stimmen noch nicht" in capsys.readouterr().out


def test_interactive_exercise_accepts_update_draw_and_input(capsys):
    source = """
def update():
    if world.btn('right'):
        kim.right()
def draw():
    world.cls()
    kim.draw()
world.run(update, draw)
"""

    report = check_exercise("interaktive-steuerung", source)

    assert report.successful
    assert report.passed == 4
    assert "Spielschleife gestartet" in capsys.readouterr().out


def test_custom_pixel_exercise_accepts_inheritance_and_spawn(capsys):
    source = """
class MusikPixel(Pixel):
    def __init__(self, pixel_world, name, x, y):
        super().__init__(pixel_world, name, x, y)
    def update(self):
        self.play_tone('C4')
    def draw(self):
        self.world.pset(self.get_x(), self.get_y(), 'purple')
mia = world.spawn(MusikPixel, 'MIA', 20, 20)
"""

    report = check_exercise("musik-pixel-klasse", source)

    assert report.successful
    assert report.passed == 4
    assert "erbt von" in capsys.readouterr().out


def test_builder_accepts_color_names_without_exposing_palette_indices():
    pykim.set_position(3, 4)
    pykim.set_color("cyan")
    pykim.paint()
    exercise = (
        ExerciseBuilder("test-farbe", "Testfarbe")
        .expect_pixels({(3, 4): "cyan"})
        .build()
    )

    assert exercise.checker("").successful


def test_builder_translates_notes_and_none_pause():
    pykim.play_tone("C4")
    pykim.play_pause(beats=2)
    exercise = (
        ExerciseBuilder("test-audio", "Testaudio")
        .expect_audio((("C4", 1), (None, 2)))
        .build()
    )

    assert exercise.checker("").successful


def test_builder_source_rules_share_the_same_ast_analysis():
    source = """
class Figur(Pixel):
    def __init__(self, world, name):
        super().__init__(world, name)
    def update(self):
        if world.btn('space'):
            pass
world.spawn(Figur, 'MIA')
"""
    exercise = (
        ExerciseBuilder("test-code", "Testcode")
        .require_class("Figur", base="Pixel")
        .require_super_init("Figur")
        .require_methods("Figur", "update")
        .require_condition(calls=("btn",))
        .require_calls("spawn")
        .build()
    )

    assert exercise.checker(source).successful


def test_builder_scores_code_line_threshold_as_percentage(capsys):
    exercise = (
        ExerciseBuilder("test-zeilen", "Codezeilen")
        .add_check(
            lambda _source: True,
            success="Fachlich richtig.",
            failure="Fachlich falsch.",
        )
        .optimize_lines(optimal=5)
        .build()
    )
    source = "\n".join(f"wert_{index} = {index}" for index in range(10))

    report = exercise.checker(source)

    assert report.optimization is not None
    assert report.optimization.score == 50
    assert report.optimization.maximum == 100


def test_line_score_ignores_blank_and_comment_only_lines(capsys):
    source = """
# Erklärung
a = 1

b = 2
c = 3
"""
    exercise = ExerciseBuilder("test-zeilen", "Codezeilen").optimize_lines(3).build()
    report = exercise.checker(source)

    assert report.optimization is not None
    assert report.optimization.score == 100

    from pykim.trainer.feedback import print_report
    print_report(report)
    assert "Optimierung: 100 %" in capsys.readouterr().out


@pytest.mark.parametrize("value", [0, -1, 1.5, True])
def test_line_score_rejects_invalid_threshold(value):
    with pytest.raises((TypeError, ValueError), match="optimal"):
        ExerciseBuilder("test-zeilen", "Codezeilen").optimize_lines(value)
def test_builder_exposes_rule_preview_and_stable_definition_hash():
    first = (
        ExerciseBuilder("autorentest", "Autorentest")
        .expect_position((20, 20))
        .require_loop()
        .build()
    )
    second = (
        ExerciseBuilder("autorentest", "Autorentest")
        .expect_position((20, 20))
        .require_loop()
        .build()
    )

    assert [rule.kind for rule in first.rules] == ["position", "loop"]
    assert first.rules[0].failure
    assert first.rules[0].hint
    assert first.definition_hash == second.definition_hash
    assert len(first.definition_hash) == 64
    assert audit_exercise(first).valid


def test_all_published_exercises_have_complete_author_metadata():
    for name in exercise_names():
        exercise = get_exercise(name)
        audit = audit_exercise(exercise)
        assert audit.valid, name
        assert not audit.issues, (name, audit.issues)
        assert all(rule.kind not in {"custom", "dynamic"} for rule in exercise.rules)


def test_definition_hash_changes_with_visible_feedback():
    first = ExerciseBuilder("hash-test", "Hash-Test").require_loop().build()
    second = (
        ExerciseBuilder("hash-test", "Hash-Test")
        .require_loop(success="Eine Schleife ist vorhanden.")
        .build()
    )

    assert first.definition_hash != second.definition_hash


def test_authoring_generator_creates_complete_yaml_definition():
    source = generate_exercise_source(
        "neue-aufgabe",
        "Neue Aufgabe",
        ("pixels", "loop"),
        optimal_lines=8,
    )

    import yaml
    from pykim.trainer.definitions import exercise_from_data

    payload = yaml.safe_load(source)
    exercise = exercise_from_data(payload["exercises"][0])
    assert exercise.name == "neue-aufgabe"
    assert [rule.kind for rule in exercise.rules] == ["pixels", "loop"]
    assert payload["exercises"][0]["optimization"]["optimal_lines"] == 8


def test_yaml_trainer_rejects_unknown_executable_rule():
    from pykim.trainer.definitions import exercise_from_data

    with pytest.raises(ValueError, match="Unbekannter sicherer Prüftyp"):
        exercise_from_data({
            "id": "unsicher",
            "title": "Unsicher",
            "tests": [{"type": "python", "code": "__import__('os').system('echo no')"}],
        })


def test_yaml_trainer_rejects_unknown_top_level_fields():
    from pykim.trainer.definitions import exercise_from_data

    with pytest.raises(ValueError, match="Unbekannte Aufgabenfelder"):
        exercise_from_data({
            "id": "unsicher",
            "title": "Unsicher",
            "tests": [{"type": "loop"}],
            "python": "print('wird niemals ausgeführt')",
        })


def test_yaml_trainer_parses_a_safe_world_setup():
    from pykim.trainer.definitions import exercise_from_data

    exercise = exercise_from_data({
        "id": "sammeln",
        "title": "Rote Pixel sammeln",
        "world": {
            "background": "light_blue",
            "start": [10, 20],
            "cells": [[12, 20, "red"], [14, 20, "red"]],
            "obstacles": ["brown"],
        },
        "tests": [{"type": "color-count", "color": "red", "count": 0}],
    })

    assert exercise.world_setup is not None
    assert exercise.world_setup.background == "light_blue"
    assert exercise.world_setup.start == (10, 20)
    assert exercise.world_setup.cells == (
        (12, 20, "red"),
        (14, 20, "red"),
    )
    assert exercise.world_setup.obstacles == ("brown",)


def test_prepare_loads_the_declarative_world(monkeypatch):
    from pykim.trainer.definitions import exercise_from_data

    exercise = exercise_from_data({
        "id": "sammeln",
        "title": "Rote Pixel sammeln",
        "world": {
            "background": "light_blue",
            "start": [10, 20],
            "cells": [[12, 20, "red"], [14, 20, "red"]],
        },
        "tests": [{"type": "color-count", "color": "red", "count": 0}],
    })
    monkeypatch.setattr(
        "pykim.trainer.exercises.get_exercise", lambda name: exercise
    )

    pykim.prepare("sammeln")

    assert pykim.world.background_color == "light_blue"
    assert pykim.get_position() == (10, 20)
    assert pykim.count_color("red") == 2


@pytest.mark.parametrize(
    "world",
    (
        {"start": [160, 20]},
        {"cells": [[10, 120, "red"]]},
        {"background": "unbekannt"},
        {"obstacles": ["unbekannt"]},
        {"python": "print('niemals ausführen')"},
    ),
)
def test_yaml_world_rejects_invalid_or_executable_data(world):
    from pykim.trainer.definitions import exercise_from_data

    with pytest.raises(ValueError):
        exercise_from_data({
            "id": "unsichere-welt",
            "title": "Unsichere Welt",
            "world": world,
            "tests": [{"type": "color-count", "color": "red", "count": 0}],
        })


def test_color_count_trainer_checks_remaining_items():
    from pykim.trainer.definitions import exercise_from_data

    exercise = exercise_from_data({
        "id": "sammeln",
        "title": "Rote Pixel sammeln",
        "tests": [{"type": "color-count", "color": "red", "count": 0}],
    })
    pykim.world.pset(10, 20, "red")
    assert not exercise.checker("").successful

    pykim.set_position(10, 20)
    pykim.collect()
    assert exercise.checker("").successful


def test_yaml_answer_trainer_is_valid_but_not_executable(tmp_path):
    from pykim.trainer.definitions import load_exercises

    (tmp_path / "antwort.yml").write_text(
        "format: 1\nid: begruendung\ntitle: Begründe deine Antwort\nmode: answer\n",
        encoding="utf-8",
    )

    assert load_exercises(tmp_path) == {}


def test_yaml_answer_trainer_rejects_unknown_fields(tmp_path):
    from pykim.trainer.definitions import load_exercises

    (tmp_path / "antwort.yml").write_text(
        "format: 1\nid: begruendung\ntitle: Begründe\nmode: answer\ntests: []\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unbekannte Felder für Antwortaufgabe"):
        load_exercises(tmp_path)


def test_yaml_function_cases_check_live_student_function():
    from pykim.trainer.definitions import exercise_from_data

    exercise = exercise_from_data({
        "id": "doppelt",
        "title": "Verdoppeln",
        "tests": [
            {
                "type": "function",
                "name": "doppelt",
                "parameters": ["zahl"],
                "returns": True,
            },
            {
                "type": "function-cases",
                "name": "doppelt",
                "cases": [
                    {"args": [2], "expected": 4},
                    {"args": [-3], "expected": -6},
                ],
            },
        ],
    })

    source = "def doppelt(zahl):\n    return zahl * 2\n"
    report = exercise.checker(source, {"doppelt": lambda zahl: zahl * 2})
    assert report.successful
    assert not exercise.checker(source, {"doppelt": lambda zahl: zahl + 2}).successful


def test_yaml_loop_can_require_while():
    from pykim.trainer.definitions import exercise_from_data

    exercise = exercise_from_data({
        "id": "warte",
        "title": "Warten",
        "tests": [{"type": "loop", "kind": "while"}],
    })

    assert exercise.checker("while bereit:\n    pass").successful
    assert not exercise.checker("for _ in range(3):\n    pass").successful


@pytest.mark.parametrize(
    ("name", "title", "rules"),
    (("Nicht gültig", "Titel", ("loop",)), ("gueltig", "", ("loop",)), ("gueltig", "Titel", ())),
)
def test_authoring_generator_rejects_incomplete_metadata(name, title, rules):
    with pytest.raises(ValueError):
        generate_exercise_source(name, title, rules)
