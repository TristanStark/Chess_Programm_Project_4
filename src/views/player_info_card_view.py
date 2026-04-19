from src.views.label_frame import CtkLabelFrame
import customtkinter as ctk


class PlayerInfoCard(CtkLabelFrame):
    def __init__(
        self,
        parent,
        first_name="",
        last_name="",
        date_of_birth="",
        ncid="",
        **kwargs,
    ):
        super().__init__(parent, text="Player Info:", **kwargs)

        self.content.grid_columnconfigure(0, weight=0)
        self.content.grid_columnconfigure(1, weight=0)
        self.content.grid_columnconfigure(2, weight=1)

        self._build_ui()

        self.set_player_info(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            ncid=ncid,
        )

    def _build_ui(self):
        row = 0

        self.first_name_title = ctk.CTkLabel(self.content, text="First Name", anchor="w")
        self.first_name_title.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)

        self.first_name_sep = ctk.CTkLabel(self.content, text=":", width=10, anchor="center")
        self.first_name_sep.grid(row=row, column=1, sticky="w", padx=(0, 8), pady=2)

        self.first_name_value = ctk.CTkLabel(self.content, text="", anchor="w")
        self.first_name_value.grid(row=row, column=2, sticky="ew", pady=2)

        row += 1

        self.last_name_title = ctk.CTkLabel(self.content, text="Last Name", anchor="w")
        self.last_name_title.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)

        self.last_name_sep = ctk.CTkLabel(self.content, text=":", width=10, anchor="center")
        self.last_name_sep.grid(row=row, column=1, sticky="w", padx=(0, 8), pady=2)

        self.last_name_value = ctk.CTkLabel(self.content, text="", anchor="w")
        self.last_name_value.grid(row=row, column=2, sticky="ew", pady=2)

        row += 1

        self.dob_title = ctk.CTkLabel(self.content, text="Date of Birth", anchor="w")
        self.dob_title.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)

        self.dob_sep = ctk.CTkLabel(self.content, text=":", width=10, anchor="center")
        self.dob_sep.grid(row=row, column=1, sticky="w", padx=(0, 8), pady=2)

        self.dob_value = ctk.CTkLabel(self.content, text="", anchor="w")
        self.dob_value.grid(row=row, column=2, sticky="ew", pady=2)

        row += 1

        self.ncid_title = ctk.CTkLabel(self.content, text="NCID", anchor="w")
        self.ncid_title.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)

        self.ncid_sep = ctk.CTkLabel(self.content, text=":", width=10, anchor="center")
        self.ncid_sep.grid(row=row, column=1, sticky="w", padx=(0, 8), pady=2)

        self.ncid_value = ctk.CTkLabel(self.content, text="", anchor="w")
        self.ncid_value.grid(row=row, column=2, sticky="ew", pady=2)

    def set_player_info(self, first_name="", last_name="", date_of_birth="", ncid=""):
        self.first_name_value.configure(text=first_name)
        self.last_name_value.configure(text=last_name)
        self.dob_value.configure(text=date_of_birth)
        self.ncid_value.configure(text=ncid)

    def clear(self):
        self.set_player_info("", "", "", "")


class PlayerInfoCardInput(CtkLabelFrame):
    def __init__(
        self,
        parent,
        first_name="",
        last_name="",
        date_of_birth="",
        ncid="",
        **kwargs,
    ):
        super().__init__(parent, text="Player Info:", **kwargs)

        self.content.grid_columnconfigure(0, weight=0)
        self.content.grid_columnconfigure(1, weight=0)
        self.content.grid_columnconfigure(2, weight=1)

        self._build_ui()
        self.set_player_info(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            ncid=ncid,
        )

    def _build_ui(self):
        row = 0

        ctk.CTkLabel(self.content, text="First Name", anchor="w").grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ctk.CTkLabel(self.content, text=":", width=10, anchor="center").grid(
            row=row, column=1, sticky="w", padx=(0, 8), pady=4
        )
        self.first_name_entry = ctk.CTkEntry(self.content)
        self.first_name_entry.grid(row=row, column=2, sticky="ew", pady=4)

        row += 1
        ctk.CTkLabel(self.content, text="Last Name", anchor="w").grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ctk.CTkLabel(self.content, text=":", width=10, anchor="center").grid(
            row=row, column=1, sticky="w", padx=(0, 8), pady=4
        )
        self.last_name_entry = ctk.CTkEntry(self.content)
        self.last_name_entry.grid(row=row, column=2, sticky="ew", pady=4)

        row += 1
        ctk.CTkLabel(self.content, text="Date of Birth", anchor="w").grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ctk.CTkLabel(self.content, text=":", width=10, anchor="center").grid(
            row=row, column=1, sticky="w", padx=(0, 8), pady=4
        )
        self.dob_entry = ctk.CTkEntry(self.content, placeholder_text="YYYY-MM-DD")
        self.dob_entry.grid(row=row, column=2, sticky="ew", pady=4)

        row += 1
        ctk.CTkLabel(self.content, text="NCID", anchor="w").grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ctk.CTkLabel(self.content, text=":", width=10, anchor="center").grid(
            row=row, column=1, sticky="w", padx=(0, 8), pady=4
        )
        self.ncid_entry = ctk.CTkEntry(self.content, placeholder_text="AA12345")
        self.ncid_entry.grid(row=row, column=2, sticky="ew", pady=4)

    def set_player_info(self, first_name="", last_name="", date_of_birth="", ncid=""):
        self.clear()
        self.first_name_entry.insert(0, first_name)
        self.last_name_entry.insert(0, last_name)
        self.dob_entry.insert(0, date_of_birth)
        self.ncid_entry.insert(0, ncid)

    def get_player_info(self):
        return {
            "first_name": self.first_name_entry.get().strip(),
            "last_name": self.last_name_entry.get().strip(),
            "date_of_birth": self.dob_entry.get().strip(),
            "ncid": self.ncid_entry.get().strip(),
        }

    def clear(self):
        self.first_name_entry.delete(0, "end")
        self.last_name_entry.delete(0, "end")
        self.dob_entry.delete(0, "end")
        self.ncid_entry.delete(0, "end")


class CreatePlayerPopup(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback):
        super().__init__(parent)
        self.on_save_callback = on_save_callback

        self.title("Add Player")
        self.geometry("500x320")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.form_card = PlayerInfoCardInput(
            self,
            corner_radius=0,
            fg_color="#F7F7F7",
            border_width=2,
            border_color="black",
        )
        self.form_card.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 8))

        self.error_label = ctk.CTkLabel(self, text="", text_color="#B00020", anchor="w")
        self.error_label.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 4))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(actions, text="Save", command=self._on_save).grid(
            row=0, column=0, padx=(0, 6), sticky="ew"
        )
        ctk.CTkButton(actions, text="Cancel", command=self.destroy).grid(
            row=0, column=1, padx=(6, 0), sticky="ew"
        )

        self.bind("<Escape>", lambda _event: self.destroy())

    def _on_save(self):
        player_data = self.form_card.get_player_info()
        success, message = self.on_save_callback(player_data)
        if success:
            self.destroy()
        else:
            self.error_label.configure(text=message)
