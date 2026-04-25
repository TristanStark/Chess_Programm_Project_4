import customtkinter as ctk
from src.views.tournament_main_view import TournamentView


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tournament View")
        self.geometry("1050x760")
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        view = TournamentView(self)
        view.grid(row=0, column=0, sticky="nsew")


if __name__ == "__main__":
    app = App()
    app.mainloop()
