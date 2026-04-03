"""
Point d'entrée CLI — CR Reunion.

Utilisation :
    python src/main.py process --input fichier.mp3 --language fr
    python src/main.py record --language fr --duration 60
"""

import typer
from rich.console import Console
from rich.panel import Panel
from pathlib import Path

app = typer.Typer(
    name="cr-reunion",
    help="Application de transcription & diarisation de réunions, 100% offline.",
    add_completion=False,
)
console = Console()


@app.command()
def process(
    input: Path = typer.Option(
        ...,
        "--input", "-i",
        help="Chemin vers le fichier audio à traiter (MP3, WAV, M4A, etc.)",
        exists=True,
        resolve_path=True,
    ),
    language: str = typer.Option(
        "auto",
        "--language", "-l",
        help="Langue de la réunion : 'auto', 'fr' ou 'en'.",
    ),
    output: str = typer.Option(
        None,
        "--output", "-o",
        help="Nom du fichier JSON de sortie (sans extension). Par défaut : nom du fichier audio.",
    ),
    min_speakers: int = typer.Option(
        None,
        "--min-speakers",
        help="Nombre minimum de locuteurs attendus (défaut: auto).",
    ),
    max_speakers: int = typer.Option(
        None,
        "--max-speakers",
        help="Nombre maximum de locuteurs attendus (défaut: auto).",
    ),
):
    """Traite un fichier audio : diarisation + transcription → JSON."""
    if language not in ("fr", "en"):
        console.print("[red]✗ Langue non supportée. Utilisez 'fr' ou 'en'.[/red]")
        raise typer.Exit(code=1)

    console.print(Panel.fit(
        f"[bold]CR Reunion[/bold]\n"
        f"Fichier : {input.name}\n"
        f"Langue  : {language}",
        border_style="blue",
    ))

    from src.pipeline import run_pipeline

    output_path = run_pipeline(
        input_path=input,
        language=None if language == "auto" else language,
        output_name=output,
        min_speakers=min_speakers,
        max_speakers=max_speakers,
    )

    console.print(f"\n[green bold]✓ Terminé ![/green bold] Résultat : {output_path}")


@app.command()
def record(
    language: str = typer.Option(
        "fr",
        "--language", "-l",
        help="Langue de la réunion : 'fr' ou 'en'.",
    ),
    filename: str = typer.Option(
        "recording.wav",
        "--filename", "-f",
        help="Nom du fichier d'enregistrement.",
    ),
):
    """Enregistre une réunion via le microphone puis la traite."""
    from src.audio_manager import AudioRecorder

    recorder = AudioRecorder(filename=filename)

    console.print(Panel.fit(
        "[bold]CR Reunion — Mode Enregistrement[/bold]\n\n"
        "Commandes :\n"
        "  [green]Entrée[/green]  → Démarrer / Reprendre\n"
        "  [yellow]p[/yellow]       → Pause\n"
        "  [red]q[/red]       → Arrêter et traiter",
        border_style="blue",
    ))

    try:
        input("  Appuyez sur Entrée pour démarrer l'enregistrement...")
        filepath = recorder.start()
        console.print(f"  [green]● Enregistrement en cours → {filepath.name}[/green]")

        while True:
            cmd = input("  > ").strip().lower()
            if cmd == "p":
                if recorder.is_paused:
                    recorder.resume()
                    console.print("  [green]● Reprise[/green]")
                else:
                    recorder.pause()
                    console.print("  [yellow]⏸ Pause[/yellow]")
            elif cmd == "q":
                break
            elif cmd == "":
                if recorder.is_paused:
                    recorder.resume()
                    console.print("  [green]● Reprise[/green]")
    except KeyboardInterrupt:
        pass
    finally:
        filepath = recorder.stop()
        console.print(f"\n  [blue]■ Enregistrement sauvegardé : {filepath}[/blue]")

    # Proposer le traitement
    should_process = typer.confirm("\n  Traiter cet enregistrement maintenant ?", default=True)
    if should_process:
        from src.pipeline import run_pipeline
        output_path = run_pipeline(
            input_path=filepath,
            language=language,
        )
        console.print(f"\n[green bold]✓ Terminé ![/green bold] Résultat : {output_path}")
    else:
        console.print(f"\n  Fichier audio sauvegardé : {filepath}")
        console.print("  Pour le traiter plus tard :")
        console.print(f"  python src/main.py process --input {filepath} --language {language}")


if __name__ == "__main__":
    import sys
    # En mode bundled (.app PyInstaller), toujours lancer la GUI
    # car sys.argv peut être pollué par les événements Apple (odoc/oapp)
    if getattr(sys, '_MEIPASS', None):
        from src.gui import launch_gui
        launch_gui()
    elif len(sys.argv) == 1:
        from src.gui import launch_gui
        launch_gui()
    else:
        app()
