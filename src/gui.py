import logging
import os
import signal
import sys
import threading
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import subprocess

logger = logging.getLogger(__name__)

from PIL import Image as PILImage, ImageTk

import customtkinter as ctk

from src.pipeline import run_pipeline
from src.audio_manager import AudioRecorder

# Configuration de base de CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Répertoire racine (compatible mode bundled PyInstaller)
from src.config import PROJECT_ROOT as _PROJECT_ROOT
_ASSETS_LOGOS = _PROJECT_ROOT / "assets" / "logos"

class CRReunionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Awesome Offline Note Taker by GiG Consulting")
        self.geometry("650x550")
        self.minsize(600, 500)

        # --- Icône de l'application (barre de titre & Dock macOS) ---
        try:
            icon_path = _ASSETS_LOGOS / "logo_gi_green_icon.png"
            icon_img = PILImage.open(icon_path)
            self._app_icon = ImageTk.PhotoImage(icon_img)
            self.iconphoto(True, self._app_icon)
        except Exception:
            pass  # Dégradation gracieuse si l'icône n'est pas trouvée

        # Pré-chargement du logo principal pour la vue d'accueil
        try:
            logo_pil = PILImage.open(_ASSETS_LOGOS / "logo_gig_consulting.png")
            # Redimensionner pour tenir dans la fenêtre (réduit de moitié)
            target_w = 175
            ratio = target_w / logo_pil.width
            target_h = int(logo_pil.height * ratio)
            self._home_logo = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(target_w, target_h))
        except Exception:
            self._home_logo = None

        # Variables d'état
        self.selected_file_path: str | None = None
        self.recorder: AudioRecorder | None = None
        self._processing: bool = False  # Flag pour thread safety pendant le traitement

        # Conteneur principal qui va héberger les différentes vues
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # Gestionnaire de fermeture propre — tue les processus fils (torch/pyannote)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Démarrage sur la vue principale
        self.show_home_view()

    def _on_closing(self):
        """Fermeture propre : arrête l'enregistrement, signale aux threads, et tue le processus."""
        logger.info("Fermeture de l'application demandée")
        self._processing = False

        # Arrêter un éventuel enregistrement en cours
        if self.recorder is not None:
            try:
                self.recorder.stop()
            except Exception:
                pass
            self.recorder = None

        # Détruire la fenêtre Tk
        try:
            self.destroy()
        except Exception:
            pass

        # Forcer la terminaison du processus entier (y compris les threads/processus fils)
        # Nécessaire car torch/pyannote peuvent laisser des threads non-daemon actifs
        logger.info("Terminaison du processus (pid=%d)", os.getpid())
        os._exit(0)

    def clear_container(self):
        """Supprime tous les widgets de la vue courante."""
        self._processing = False  # Signaler aux threads en cours que la vue a changé
        for widget in self.container.winfo_children():
            widget.destroy()

    # --- VUE 1 : ACCUEIL (Ouverture) ---
    def show_home_view(self):
        self.clear_container()
        self.selected_file_path = None
        
        # Logo GiG Consulting (remplace l'ancien texte "CR Reunion")
        if self._home_logo is not None:
            lbl_logo = ctk.CTkLabel(self.container, image=self._home_logo, text="")
            lbl_logo.pack(pady=(60, 20))
        else:
            # Fallback texte si l'image n'est pas chargée
            lbl_title = ctk.CTkLabel(self.container, text="GiG Consulting", font=ctk.CTkFont(family="Helvetica", size=32, weight="bold"))
            lbl_title.pack(pady=(80, 20))

        # Zone de Drag & Drop
        self.drop_frame = ctk.CTkFrame(self.container, corner_radius=15, border_width=2, border_color="#333333", fg_color="#1E1E1E")
        self.drop_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Contenu de la zone
        icon_lbl = ctk.CTkLabel(self.drop_frame, text="🎵", font=ctk.CTkFont(size=48))
        icon_lbl.pack(pady=(40, 10))
        
        text_lbl = ctk.CTkLabel(self.drop_frame, text="Sélectionnez un fichier audio", font=ctk.CTkFont(size=18, weight="bold"))
        text_lbl.pack(pady=(0, 5))
        
        sub_lbl = ctk.CTkLabel(self.drop_frame, text="Utilisez les boutons ci-dessous", text_color="gray", font=ctk.CTkFont(size=14))
        sub_lbl.pack(pady=(0, 40))

        # Boutons d'action
        buttons_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        buttons_frame.pack(pady=(0, 50))

        btn_record = ctk.CTkButton(buttons_frame, text="🎤 Enregistrer", command=self.show_record_view,
                                   font=ctk.CTkFont(weight="bold"), fg_color="#333333", hover_color="#444444", height=45)
        btn_record.pack(side="left", padx=10)

        btn_import = ctk.CTkButton(buttons_frame, text="📁 Importer...", command=self.browse_file,
                                   font=ctk.CTkFont(weight="bold"), fg_color="#333333", hover_color="#444444", height=45)
        btn_import.pack(side="left", padx=10)

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Sélectionner un fichier audio",
            filetypes=(("Fichiers Audio", "*.mp3 *.wav *.m4a *.ogg *.flac *.wma *.aac"), ("Tous les fichiers", "*.*"))
        )
        if filename:
            self.selected_file_path = filename
            self.show_ready_view()

    # --- VUE 2 : ENREGISTREMENT ---
    def show_record_view(self):
        self.clear_container()

        lbl_title = ctk.CTkLabel(self.container, text="Enregistrement en direct", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.pack(pady=(40, 20))

        # Icône au centre (simule l'onde sonore via la couleur)
        self.record_icon_lbl = ctk.CTkLabel(self.container, text="🎙️", font=ctk.CTkFont(size=100))
        self.record_icon_lbl.pack(pady=30)
        
        # Chronomètre (Police tabulaire claire)
        self.timer_lbl = ctk.CTkLabel(self.container, text="00:00", font=ctk.CTkFont(family="Helvetica", size=56, weight="bold"))
        self.timer_lbl.pack(pady=10)

        self.lbl_rec_status = ctk.CTkLabel(self.container, text="Prêt à enregistrer...", text_color="gray", font=ctk.CTkFont(size=14))
        self.lbl_rec_status.pack(pady=(0, 20))

        # Boutons
        controls_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        controls_frame.pack(pady=20)

        self.btn_rec_action = ctk.CTkButton(controls_frame, text="Démarrer", command=self.toggle_recording,
                                            font=ctk.CTkFont(weight="bold"), fg_color="#FF3B30", hover_color="#FF453A", height=50, corner_radius=25)
        self.btn_rec_action.pack(side="left", padx=10)

        self.btn_rec_stop = ctk.CTkButton(controls_frame, text="Terminer", command=self.stop_recording,
                                          font=ctk.CTkFont(weight="bold"), fg_color="#333333", hover_color="#444444", state="disabled", height=50, corner_radius=25)
        self.btn_rec_stop.pack(side="left", padx=10)

        # Bouton Annuler/Retour
        btn_back = ctk.CTkButton(self.container, text="Retour", command=self.cancel_recording, 
                                 fg_color="transparent", text_color="gray", hover_color="#2A2A2A")
        btn_back.pack(pady=20)

        self.record_seconds = 0
        self.timer_id = None
        self.recorder = None

    def update_timer(self):
        if self.recorder and not self.recorder.is_paused:
            self.record_seconds += 1
            mins, secs = divmod(self.record_seconds, 60)
            self.timer_lbl.configure(text=f"{mins:02d}:{secs:02d}")
            
            # Simulation d'activité visuelle
            if self.record_seconds % 2 == 0:
                self.record_icon_lbl.configure(text_color="#FF3B30")
            else:
                self.record_icon_lbl.configure(text_color="white")
        
        self.timer_id = self.after(1000, self.update_timer)

    def toggle_recording(self):
        if self.recorder is None:
            self.recorder = AudioRecorder()
            filepath = self.recorder.start()
            self.record_seconds = 0
            self.btn_rec_action.configure(text="Pause", fg_color="#007AFF", hover_color="#005ecb")
            self.btn_rec_stop.configure(state="normal")
            
            self.lbl_rec_status.configure(text=f"Enregistrement vers {filepath.name}...", text_color="gray")
            self.update_timer()
        else:
            if self.recorder.is_paused:
                self.recorder.resume()
                self.btn_rec_action.configure(text="Pause", fg_color="#007AFF", hover_color="#005ecb")
                self.lbl_rec_status.configure(text="Enregistrement en cours...", text_color="gray")
            else:
                self.recorder.pause()
                self.btn_rec_action.configure(text="Reprendre", fg_color="#FF3B30", hover_color="#FF453A")
                self.lbl_rec_status.configure(text="Enregistrement en pause.", text_color="#F57C00")
                self.record_icon_lbl.configure(text_color="gray")

    def stop_recording(self):
        if self.recorder is not None:
            if self.timer_id:
                self.after_cancel(self.timer_id)
            filepath = self.recorder.stop()
            self.recorder = None
            self.selected_file_path = str(filepath)
            self.show_ready_view()

    def cancel_recording(self):
        if self.recorder is not None:
            if self.timer_id:
                self.after_cancel(self.timer_id)
            self.recorder.stop()
            self.recorder = None
        self.show_home_view()

    # --- VUE 3 : PRET POUR L'IA ---
    def show_ready_view(self):
        if not self.selected_file_path:
            return self.show_home_view()
            
        self.clear_container()
        
        lbl_title = ctk.CTkLabel(self.container, text="Fichier Prêt", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.pack(pady=(40, 20))

        # Icône check
        icon_lbl = ctk.CTkLabel(self.container, text="✓", font=ctk.CTkFont(size=64, weight="bold"), text_color="#007AFF")
        icon_lbl.pack(pady=20)

        # Fichier info (Tronqué si trop long)
        path = self.selected_file_path
        if path is None:
            return
            
        filename = str(Path(path).name)
        if len(filename) > 50:
            filename = str(filename[:20]) + "..." + str(filename[-20:])
            
        lbl_file_info = ctk.CTkLabel(self.container, text="Fichier sélectionné :", text_color="gray", font=ctk.CTkFont(size=14))
        lbl_file_info.pack(pady=(0, 5))
        
        lbl_filename = ctk.CTkLabel(self.container, text=filename, font=ctk.CTkFont(size=16, weight="bold"))
        lbl_filename.pack(pady=(0, 40))

        # Option langue
        lang_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        lang_frame.pack(pady=10)
        
        lbl_lang = ctk.CTkLabel(lang_frame, text="Langue de la réunion :")
        lbl_lang.pack(side="left", padx=10)
        
        self.lang_var = ctk.StringVar(value="Auto")
        opt_lang = ctk.CTkOptionMenu(lang_frame, values=["Auto", "fr", "en"], variable=self.lang_var)
        opt_lang.pack(side="left", padx=10)

        # Bouton Lancer l'IA
        btn_start_ia = ctk.CTkButton(self.container, text="▶ Lancer l'IA", command=self.show_processing_view,
                                     font=ctk.CTkFont(size=16, weight="bold"), fg_color="#007AFF", hover_color="#005ecb", height=50, corner_radius=25)
        btn_start_ia.pack(pady=30)

        # Bouton modifier
        btn_change = ctk.CTkButton(self.container, text="Changer de fichier", command=self.show_home_view,
                                   fg_color="transparent", text_color="gray", hover_color="#2A2A2A")
        btn_change.pack(pady=10)

    # --- VUE 4 : TRAITEMENT ---
    def show_processing_view(self):
        self.clear_container()
        self._processing = True

        lbl_title = ctk.CTkLabel(self.container, text="Traitement en cours...", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.pack(pady=(80, 40))

        # Barre de progression
        self.progress_bar = ctk.CTkProgressBar(self.container, mode="indeterminate", width=300)
        self.progress_bar.pack(pady=20)
        self.progress_bar.start()

        self.lbl_proc_status = ctk.CTkLabel(self.container, text="Initialisation de l'IA...", text_color="gray", font=ctk.CTkFont(size=16))
        self.lbl_proc_status.pack(pady=20)

        # Démarrer le process dans un thread séparé
        lang = self.lang_var.get()
        thread = threading.Thread(target=self.process_file_thread, args=(self.selected_file_path, lang), daemon=True)
        thread.start()

    def _safe_update_status(self, text: str):
        """Met à jour le label de statut de manière thread-safe."""
        if self._processing and hasattr(self, 'lbl_proc_status'):
            try:
                self.lbl_proc_status.configure(text=text)
            except Exception:
                pass  # Widget détruit entre-temps, on ignore

    def process_file_thread(self, file_path, lang):
        # Mettre à jour le texte dynamiquement avant le blocage
        self.after(500, lambda: self._safe_update_status("Analyse audio et transcription en cours...\nCela peut prendre quelques minutes."))

        try:
            output_path = run_pipeline(
                input_path=file_path,
                language=None if lang == "Auto" else lang,
                min_speakers=None,
                max_speakers=None
            )
            if self._processing:
                self.after(0, self.show_success_view, output_path)
        except Exception as e:
            if self._processing:
                self.after(0, self.show_error_view, str(e))

    # --- VUE 5 : SUCCÈS ---
    def show_success_view(self, output_path: Path):
        self.clear_container()

        icon_lbl = ctk.CTkLabel(self.container, text="✅", font=ctk.CTkFont(size=80))
        icon_lbl.pack(pady=(60, 20))

        lbl_title = ctk.CTkLabel(self.container, text="Traitement terminé avec succès !", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.pack(pady=10)

        lbl_desc = ctk.CTkLabel(self.container, text=f"Le résumé de la réunion a été généré.", text_color="gray", font=ctk.CTkFont(size=14))
        lbl_desc.pack(pady=10)

        btn_finder = ctk.CTkButton(self.container, text="Ouvrir dans le Finder", command=lambda: self.open_finder(output_path.parent),
                                   font=ctk.CTkFont(weight="bold"), fg_color="#333333", hover_color="#444444", height=45)
        btn_finder.pack(pady=30)

        btn_home = ctk.CTkButton(self.container, text="Retour à l'accueil", command=self.show_home_view,
                                 fg_color="transparent", text_color="#007AFF", hover_color="#1E1E1E")
        btn_home.pack(pady=10)
        
        # Ouvre automatiquement le Finder
        self.open_finder(output_path.parent)

    def show_error_view(self, error_msg: str):
        self.clear_container()

        icon_lbl = ctk.CTkLabel(self.container, text="❌", font=ctk.CTkFont(size=80))
        icon_lbl.pack(pady=(60, 20))

        lbl_title = ctk.CTkLabel(self.container, text="Une erreur est survenue", font=ctk.CTkFont(size=24, weight="bold"), text_color="#FF3B30")
        lbl_title.pack(pady=10)

        # Zone d'erreur défilable
        tb_error = ctk.CTkTextbox(self.container, width=500, height=150, fg_color="#2A2A2A")
        tb_error.pack(pady=20)
        tb_error.insert("1.0", error_msg)
        tb_error.configure(state="disabled")

        btn_home = ctk.CTkButton(self.container, text="Retour à l'accueil", command=self.show_home_view,
                                 font=ctk.CTkFont(weight="bold"), fg_color="#333333", hover_color="#444444", height=45)
        btn_home.pack(pady=20)

    def open_finder(self, directory: Path):
        """Ouvre le répertoire spécifié dans l'explorateur de fichiers de l'OS."""
        if sys.platform == "darwin":
            subprocess.run(["open", str(directory)])
        elif sys.platform == "win32":
            subprocess.run(["explorer", str(directory)])
        else:
            subprocess.run(["xdg-open", str(directory)])


def launch_gui():
    app = CRReunionApp()
    app.mainloop()

if __name__ == "__main__":
    launch_gui()
