import tkinter as tk
from tkinter import ttk
import mido

# === Setup MIDI ===
print("Porte MIDI disponibili:")
print(mido.get_output_names())

MIDI_PORT_NAME = "Arduino Leonardo"  # cambia con quello reale
outport = mido.open_output(MIDI_PORT_NAME)
inport = mido.open_input(MIDI_PORT_NAME)

# === Costanti ===
NOTES = {
    "Do (C)": 60, "Do# (C#)": 61, "Re (D)": 62, "Re# (D#)": 63,
    "Mi (E)": 64, "Fa (F)": 65, "Fa# (F#)": 66, "Sol (G)": 67,
    "Sol# (G#)": 68, "La (A)": 69, "La# (A#)": 70, "Si (B)": 71,
    "Do (C) 2": 72, "Do# (C#) 2": 73, "Re (D) 2": 74, "Re# (D#) 2": 75,
    "Mi (E) 2": 76, "Fa (F) 2": 77, "Fa# (F#) 2": 78, "Sol (G) 2": 79,
    "Sol# (G#) 2": 80, "La (A) 2": 81, "La# (A#) 2": 82, "Si (B) 2": 83
}

FIRST_OCTAVE = [ "Do (C)", "Do# (C#)", "Re (D)", "Re# (D#)",
    "Mi (E)", "Fa (F)", "Fa# (F#)", "Sol (G)",
    "Sol# (G#)", "La (A)", "La# (A#)", "Si (B)"]

SCALES = {
    "Maggiore (prime 5)": [0, 2, 4, 5, 7],
    "Minore (prime 5)": [0, 2, 3, 5, 7],
    "Maggiore Pentatonica": [0, 2, 4, 7, 9],
    "Minore Pentatonica": [0, 3, 5, 7, 10],
    "Blues": [0, 3, 5, 6, 7],
    "Diatonica sospesa (Sus4)": [0, 2, 5, 7, 9],
    "Orientale": [0, 1, 4, 5, 7],
    "Maggior armonica (prime 5)": [0, 2, 4, 7, 11],
    "Minore armonica (prime 5)": [0, 2, 3, 7, 10],
}

DEFAULT_COMBO_NOTES = ["Do (C)", "Re (D)", "Mi (E)", "Fa (F)", "Sol (G)"]

# === Funzioni utilitarie ===
def mostra_avviso(msg, widget=None, durata=1500):
    popup = tk.Toplevel()
    popup.overrideredirect(True)
    label = tk.Label(popup, text=msg, padx=10, pady=5, anchor="center")
    label.pack()
    popup.update_idletasks()
    w, h = popup.winfo_width(), popup.winfo_height()
    
    if widget:
        x = widget.winfo_rootx() + widget.winfo_width()//2 - w//2
        y = widget.winfo_rooty() + widget.winfo_height() + 5
    else:
        x = popup.winfo_screenwidth()//2 - w//2
        y = popup.winfo_screenheight()//2 - h//2
    popup.geometry(f"{w}x{h}+{x}+{y}")
    popup.after(durata, popup.destroy)

# === GUI setup ===
root = tk.Tk()
root.title("Configurazione Arpa Laser MIDI")
combos = []

def invia_config(mostra_popup=True):
    for i, combo in enumerate(combos):
        nota_val = NOTES[combo.get()]
        outport.send(mido.Message("control_change", control=20+i, value=nota_val))
        print(f"Inviato LDR {i+1}: {combo.get()} ({nota_val})")
    if mostra_popup:
        mostra_avviso("Note applicate", widget=btn_invia)

def imposta_scala():
    tonica, scala_nome = root_note_combo.get(), scale_combo.get()
    if tonica not in NOTES or scala_nome not in SCALES:
        return
    
    tonica_val = NOTES[tonica]
    intervalli = SCALES[scala_nome]
    scale_notes = []
    
    for semitoni in intervalli:
        midi_val = tonica_val + semitoni
        nome = next((k for k, v in NOTES.items() if v == midi_val), list(NOTES.keys())[0])
        scale_notes.append(nome)
    
    for i in range(5):
        combos[i].set(scale_notes[i])
    
    invia_config(mostra_popup=False)
    mostra_avviso("Scala applicata", widget=btn_scala)

# === Layout ===
# Colonna sinistra: configurazione manuale
label_left = ttk.Label(root, text="Configurazione manuale", font=("Roboto", 15))
frame_left = ttk.LabelFrame(root, labelwidget=label_left, padding=10)
frame_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

for i in range(5):
    ttk.Label(frame_left, text=f"Laser {i+1}").grid(row=i, column=0, padx=5, pady=5, sticky="w")
    combo = ttk.Combobox(frame_left, values=FIRST_OCTAVE, state="readonly")
    combo.set(DEFAULT_COMBO_NOTES[i])
    combo.grid(row=i, column=1, padx=5, pady=5)
    combos.append(combo)

btn_invia = ttk.Button(frame_left, text="Applica note", command=invia_config)
btn_invia.grid(row=6, column=0, columnspan=2, pady=10)

# Colonna destra: preset di scala
label_right = ttk.Label(root, text="Preset", font=("Roboto", 15))
frame_right = ttk.LabelFrame(root, labelwidget=label_right, padding=10)
frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

ttk.Label(frame_right, text="Tonica:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
root_note_combo = ttk.Combobox(frame_right, values=FIRST_OCTAVE, state="readonly")
root_note_combo.set("Do (C)")
root_note_combo.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(frame_right, text="Scala:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
scale_combo = ttk.Combobox(frame_right, values=list(SCALES.keys()), state="readonly")
scale_combo.set("Maggiore (prime 5)")
scale_combo.grid(row=1, column=1, padx=5, pady=5)

btn_scala = ttk.Button(frame_right, text="Applica Scala", command=imposta_scala)
btn_scala.grid(row=2, column=0, columnspan=2, pady=10)

# === Frame stato ===
status_label = ttk.Label(root, text="Stato arpa", font=("Roboto", 15))
status_frame = ttk.LabelFrame(root, labelwidget=status_label, padding=10)
status_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

# --- LED ---
canvas_width, canvas_height = 300, 80
led_frame = ttk.Frame(status_frame)
led_frame.grid(row=0, column=0, padx=5, pady=5)
ttk.Label(led_frame, text="LED").pack(pady=(0,5))
led_canvas = tk.Canvas(led_frame, width=canvas_width, height=canvas_height)
led_canvas.pack()

led_radius = min(canvas_height // 3, 20)
spacing = canvas_width // 6
led_widgets = [led_canvas.create_oval(spacing*(i+1)-led_radius, canvas_height//2-led_radius,
                                     spacing*(i+1)+led_radius, canvas_height//2+led_radius,
                                     fill="gray", outline="") for i in range(5)]

def aggiorna_led(index, acceso=True):
    if 0 <= index < len(led_widgets):
        led_canvas.itemconfig(led_widgets[index], fill="green" if acceso else "gray")

# --- Ottava ---
ottava_frame = ttk.Frame(status_frame)
ottava_frame.grid(row=0, column=1, padx=5, pady=5)
ttk.Label(ottava_frame, text="Ottava").pack(pady=(0,5))
ottava_label = tk.Label(ottava_frame, text="0", font=("Arial", 18, "bold"))
ottava_label.pack()
def aggiorna_ottava(val): ottava_label.config(text=f"{val}")

# --- Ultrasuoni ---
ultra_frame = ttk.Frame(status_frame)
ultra_frame.grid(row=0, column=2, padx=5, pady=5)
ttk.Label(ultra_frame, text="Sensore").pack(pady=(0,5))
ultra_canvas = tk.Canvas(ultra_frame, width=60, height=canvas_height)
ultra_canvas.pack()
ultra_bar = ultra_canvas.create_rectangle(10, canvas_height, 50, canvas_height, fill="blue")
def aggiorna_ultrasuoni(distanza, max_dist=100):
    altezza = max(10, min(canvas_height-10, canvas_height-10-(distanza/max_dist)*(canvas_height-20)))
    ultra_canvas.coords(ultra_bar, 10, altezza, 50, canvas_height-10)

# Centra frame interni
for i in range(3): status_frame.grid_columnconfigure(i, weight=1)
led_frame.grid(sticky="n"); ottava_frame.grid(sticky="n"); ultra_frame.grid(sticky="n")

# === Lettura MIDI ===
def leggi_midi():
    for msg in inport.iter_pending():
        if msg.type == 'note_on':
            print(f"Nota ON ricevuta: {msg.note}")
        elif msg.type == 'note_off':
            print(f"Nota OFF ricevuta: {msg.note}")
        elif msg.type == 'control_change':
            if 30 <= msg.control <= 34:
                aggiorna_led(msg.control-30, msg.value>0)
            elif msg.control == 40:
                aggiorna_ottava(msg.value-64)
            elif msg.control == 91:
                aggiorna_ultrasuoni(int((127-msg.value)*100/127))
            else:
                print(f"CC sconosciuto: {msg.control} value={msg.value}")
    root.after(50, leggi_midi)

leggi_midi()
root.mainloop()
