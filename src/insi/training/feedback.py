"""Textdarstellung deutschsprachiger Prüfergebnisse."""

from pykim.trainer.models import CheckReport


def print_report(report: CheckReport) -> None:
    print(f"Aufgabe: {report.title}\n")
    for result in report.results:
        marker = "✓" if result.passed else "✗"
        print(f"{marker} {result.message}")
        if not result.passed and result.hint:
            print(f"  Hinweis: {result.hint}")

    if report.successful:
        print("\nSehr gut! Du hast die Aufgabe vollständig gelöst.")
    else:
        print(f"\n{report.passed} von {len(report.results)} Prüfungen bestanden.")

    if report.optimization is not None:
        optimization = report.optimization
        if optimization.maximum == 100:
            print(f"\nOptimierung: {optimization.score} %")
        else:
            print(f"\nOptimierung: {optimization.score}/{optimization.maximum}")
        if optimization.score == optimization.maximum:
            print("✓ Dein Code ist für diese Aufgabe optimal aufgebaut.")
        else:
            for tip in optimization.tips:
                print(f"  Tipp: {tip}")
