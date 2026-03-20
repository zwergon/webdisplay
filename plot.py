import webdisplay
import matplotlib.pyplot as plt

webdisplay.connect("ws://localhost:8765/send")  # adresse de la machine locale

fig, ax = plt.subplots()
ax.plot([1, 4, 2, 8, 5])
webdisplay.show_figure(fig)
